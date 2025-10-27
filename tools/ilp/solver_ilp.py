import json, os
from typing import Dict, List, Tuple
from ..common.io import load_manifests, load_json
from ..common.semver import check_set
from ..common.policy import allowed
from ..common.util import version_of_saddr, canon

LANE_BASE_MS = {'shm':0.2, 'uds':0.6, 'tcp':1.5}
NUMA_PENALTY_MS = 0.4

def feasible_lanes(sym_f, sym_t, same_node):
    lanes = []
    tags_f = sym_f.get('tags',{}); tags_t = sym_t.get('tags',{})
    if same_node and tags_f.get('supports_shm') and tags_t.get('supports_shm'):
        lanes.append('shm')
    lanes += ['uds','tcp']
    return lanes

def solve_ilp(routes_file, manifests_dir, key_id, policy_file, topo_file, prefer_list, admit_priority=1000.0, churn_weight=1.0, change_threshold_ms=0.15, last_plan_file=None):
    try:
        import pulp
    except Exception as e:
        raise RuntimeError("PuLP not installed. Install with: pip install pulp") from e

    routes = load_json(routes_file)
    manis = load_manifests(manifests_dir)
    policy = load_json(policy_file) if os.path.isfile(policy_file) else {"allow":[{"from":"*","to":"*"}]}
    topo = load_json(topo_file) if os.path.isfile(topo_file) else {"nodes":{"0":{"name":"n0"}}, "place":{}}
    last = load_json(last_plan_file) if last_plan_file and os.path.isfile(last_plan_file) else {}
    prev_place = last.get("placement", {})
    prev_lanes = {(r.get("from"), r.get("to")): r.get("lane") for r in last.get("routes_add", []) if r.get("from") and r.get("to") and r.get("lane")}

    # candidates
    R = []
    for r in routes.get('routes', []):
        sf, st = r['from'], r['to']
        if sf not in manis or st not in manis: continue
        if not allowed(policy, sf, st): continue
        # semver meet
        vf = version_of_saddr(sf); vt = version_of_saddr(st)
        if not check_set(vf, manis[st].get('version_set','>=0.0.0')): continue
        if not check_set(vt, manis[sf].get('version_set','>=0.0.0')): continue
        R.append((sf,st))
    S = sorted({s for r in R for s in r})
    N = list(topo.get('nodes', {}).keys()) or ['0']

    # QoS and demand
    def qos(sym): return sym.get('qos', {"latency_budget_ms": 2000, "throughput_qps": 1})
    def demand(sym):
        q = qos(sym)
        thr = q.get('throughput_qps', 1)
        cpuw = sym.get('tags', {}).get('cpu_weight', 1.0)
        mem = sym.get('tags', {}).get('mem_mb', 16)
        return {'cpu': max(0.1, cpuw * (thr/10.0)), 'mem': mem}
    def capacity(node):
        n = topo.get('nodes', {}).get(node, {})
        cap = n.get('capacity', {})
        return {'cpu': cap.get('cpu', 64.0), 'mem': cap.get('mem_mb', 65536)}
    place_hint = topo.get('place', {})

    # Model
    m = pulp.LpProblem("rtt_exact_admission", pulp.LpMinimize)

    # Variables
    x = pulp.LpVariable.dicts('x', ((s,n) for s in S for n in N), lowBound=0, upBound=1, cat='Binary')  # place
    a = pulp.LpVariable.dicts('a', (r for r in R), lowBound=0, upBound=1, cat='Binary')  # admit route
    y = pulp.LpVariable.dicts('y', ((sf,st,l) for sf,st in R for l in ['shm','uds','tcp']), lowBound=0, upBound=1, cat='Binary')  # lane
    d = pulp.LpVariable.dicts('d', (r for r in R), lowBound=0, upBound=1, cat='Binary')  # cross-node delta
    mv = pulp.LpVariable.dicts('mv', (s for s in S), lowBound=0, upBound=1, cat='Binary')  # move indicator
    lc = pulp.LpVariable.dicts('lc', (r for r in R), lowBound=0, upBound=1, cat='Binary')  # lane change

    # Link a and y
    for sf,st in R:
        m += pulp.lpSum([y[(sf,st,l)] for l in ['shm','uds','tcp']]) == a[(sf,st)]

    # Lane feasibility: shm implies co-placement
    for sf,st in R:
        # y_shm ≤ x_sf,n and y_shm ≤ x_st,n for the same n aggregated via classic trick:
        # enforce equality of placement when y_shm=1: for all n: x_sf,n - x_st,n ≤ 1 - y_shm and x_st,n - x_sf,n ≤ 1 - y_shm
        yshm = y[(sf,st,'shm')]
        for n in N:
            m += x[(sf,n)] - x[(st,n)] <= 1 - yshm
            m += x[(st,n)] - x[(sf,n)] <= 1 - yshm

    # One node per active symbol; activate symbol if any incident route admitted
    for s in S:
        incident = [a[r] for r in R if s in r]
        if incident:
            m += pulp.lpSum([x[(s,n)] for n in N]) >= pulp.lpSum(incident) * 0.0001  # if any admitted, sum x ≥ tiny
            m += pulp.lpSum([x[(s,n)] for n in N]) <= 1

    # Cross-node delta d[r] ≥ |x_f - x_t| in 0/1 form
    for sf,st in R:
        for n in N:
            m += d[(sf,st)] >= x[(sf,n)] - x[(st,n)]
            m += d[(sf,st)] >= x[(st,n)] - x[(sf,n)]

    # QoS latency budget: forbid lane choices that exceed budget
    for sf,st in R:
        qf = qos(manis[sf]); qt = qos(manis[st])
        budget = min(qf.get('latency_budget_ms', 1e9), qt.get('latency_budget_ms', 1e9))
        for l, base in LANE_BASE_MS.items():
            # worst-case cross penalty = NUMA_PENALTY_MS * d
            # require: base + NUMA_PENALTY_MS * d ≤ budget when y_l = 1. Use big-M: base + NUMA*d ≤ budget + M*(1 - y_l)
            M = 1e6
            m += base + NUMA_PENALTY_MS * d[(sf,st)] <= budget + M*(1 - y[(sf,st,l)])

    # Capacity per node
    for n in N:
        cpu = pulp.lpSum([ (demand(manis[s])['cpu']) * x[(s,n)] for s in S ])
        mem = pulp.lpSum([ (demand(manis[s])['mem']) * x[(s,n)] ])
        cap = capacity(n)
        m += cpu <= cap['cpu']
        m += mem <= cap['mem']

    # Movement indicator against previous placement
    for s in S:
        prev = prev_place.get(s)
        if prev and prev in N:
            # mv ≥ 1 - x[s,prev]
            m += mv[s] >= 1 - x[(s,prev)]
        else:
            # no penalty baseline
            m += mv[s] >= 0

    # Lane change indicator
    for sf,st in R:
        prev = prev_lanes.get((sf,st))
        if prev:
            # if admitted and choose lane ≠ prev, penalize
            m += lc[(sf,st)] >= a[(sf,st)] - y[(sf,st,prev)]
        else:
            m += lc[(sf,st)] >= 0

    # Prefer list biases via objective weights
    lane_bias = {l: (0.0 if l in prefer_list else 0.05) for l in ['shm','uds','tcp']}

    # Objective
    lat_cost = pulp.lpSum([ y[(sf,st,l)] * (LANE_BASE_MS[l] + lane_bias[l]) for (sf,st) in R for l in ['shm','uds','tcp'] ])                  + pulp.lpSum([ d[(sf,st)] * NUMA_PENALTY_MS * a[(sf,st)] for (sf,st) in R ])
    churn_cost = pulp.lpSum([ mv[s] for s in S ]) + pulp.lpSum([ lc[(sf,st)] for (sf,st) in R ])
    # Maximize admissions by large negative coefficient
    admit_reward = -admit_priority * pulp.lpSum([ a[(sf,st)] for (sf,st) in R ])
    m += lat_cost + churn_weight*churn_cost + admit_reward

    # Hints: place to hinted node when inactive or no conflict
    for s in S:
        pref = place_hint.get(s)
        if pref and pref in N:
            # soft hint via tiny objective term
            m += 0  # no hard constraint

    # Solve
    m.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[m.status]
    if status not in ("Optimal","Feasible"):
        return {"ok": False, "status": status, "reason": "solver_failed"}

    place = {}
    for s in S:
        for n in N:
            if pulp.value(x[(s,n)]) > 0.5:
                place[s] = n; break
    routes_add = []
    rejects = []
    for sf,st in R:
        if pulp.value(a[(sf,st)]) < 0.5:
            rejects.append({"from":sf,"to":st,"reason":"not_admitted"})
            continue
        chosen = None
        for l in ['shm','uds','tcp']:
            if pulp.value(y[(sf,st,l)]) > 0.5:
                chosen = l; break
        routes_add.append({"from": sf, "to": st, "lane": chosen})
    return {"ok": True, "placement": place, "routes_add": routes_add, "rejects": rejects}
