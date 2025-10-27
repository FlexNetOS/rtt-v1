import json
from .solver_constraints import LANE_BASE_LAT_MS, supports_lane

def numa_penalty_ms(topology, a, b):
    na = topology.get('place', {}).get(a, '0')
    nb = topology.get('place', {}).get(b, '0')
    return 0.4 if na != nb else 0.0

def nodes(topology):
    return list(topology.get('nodes', {}).keys()) or ['0']

def demand(sym):
    q = sym.get('qos', {})
    thr = q.get('throughput_qps', 1)
    cpuw = sym.get('tags', {}).get('cpu_weight', 1.0)
    mem = sym.get('tags', {}).get('mem_mb', 16)
    return {'cpu': max(0.1, cpuw * (thr/10.0)), 'mem': mem}

def capacity(topology, node):
    n = topology.get('nodes', {}).get(node, {})
    cap = n.get('capacity', {})
    return {'cpu': cap.get('cpu', 64.0), 'mem': cap.get('mem_mb', 65536)}

def initial_place(symbols, topology, prev_place):
    place = {}
    # seed from prev, then topology.place, then round-robin
    rr = 0
    node_list = nodes(topology)
    for s in symbols:
        if prev_place and s in prev_place:
            place[s] = prev_place[s]
        elif s in topology.get('place', {}):
            place[s] = topology['place'][s]
        else:
            place[s] = node_list[rr % len(node_list)]; rr += 1
    return place

def placement_cost(routes, place, lane_map, topology, churn_weight, prev_place):
    cost = 0.0
    moves = 0
    for r in routes:
        a = r['from']; b = r['to']; lane = lane_map.get((a,b), r.get('lane','uds'))
        base = LANE_BASE_LAT_MS.get(lane, 2.0)
        cross = numa_penalty_ms(topology, a, b) if place.get(a)!=place.get(b) else 0.0
        cost += base + cross
    if prev_place:
        for s, n in place.items():
            if prev_place.get(s) and prev_place[s] != n:
                moves += 1
        cost += churn_weight * moves
    return cost, moves

def pack_feasible(place, symbols, topology, manifests):
    # ensure capacity not exceeded; very simple rebalance if needed
    usage = {node:{'cpu':0.0,'mem':0.0} for node in nodes(topology)}
    for s in symbols:
        n = place[s]
        d = demand(manifests[s])
        u = usage[n]; u['cpu'] += d['cpu']; u['mem'] += d['mem']
    caps = {n:capacity(topology, n) for n in usage}
    # naive fix: if node exceeds, move heaviest to least loaded
    changed=True; guard=0
    while changed and guard<100:
        changed=False; guard+=1
        for n,u in usage.items():
            if u['cpu'] > caps[n]['cpu'] or u['mem'] > caps[n]['mem']:
                # find symbol on n with largest cpu demand
                heavy = None; heavy_d = 0.0
                for s in symbols:
                    if place[s]==n:
                        d = demand(manifests[s])
                        if d['cpu']>heavy_d: heavy, heavy_d = s, d['cpu']
                # move to best other node
                best_node = n
                best_load = u['cpu']
                for m in usage:
                    if m==n: continue
                    if usage[m]['cpu'] < best_load:
                        best_node = m; best_load = usage[m]['cpu']
                if best_node != n and heavy:
                    place[heavy] = best_node
                    usage[n]['cpu'] -= heavy_d
                    usage[best_node]['cpu'] += heavy_d
                    changed=True
    return place

def choose_lane(sym_from, sym_to, prefer, same_node):
    for lane in prefer:
        if lane=='shm' and not same_node: continue
        if supports_lane(sym_from, lane) and supports_lane(sym_to, lane):
            return lane
    return 'uds'

def optimize(manifests, routes, topology, prev_place, prev_lanes, prefer, churn_weight=0.5, change_threshold_ms=0.2):
    # Symbols to place
    syms = sorted({r['from'] for r in routes} | {r['to'] for r in routes})
    place = initial_place(syms, topology, prev_place)
    place = pack_feasible(place, syms, topology, manifests)
    # initial lanes based on placement
    lane_map = {}
    for r in routes:
        a=r['from']; b=r['to']
        same = place.get(a)==place.get(b)
        lane_map[(a,b)] = choose_lane(manifests[a], manifests[b], prefer, same)
    # keep previous lanes if feasible and improvement < threshold
    for r in routes:
        key=(r['from'], r['to'])
        if key in prev_lanes:
            prev_lane = prev_lanes[key]
            same = place.get(key[0])==place.get(key[1])
            # if prev lane still feasible keep it unless better by threshold
            def lat(lane): 
                base = LANE_BASE_LAT_MS.get(lane, 2.0)
                cross = 0.0 if same else 0.4
                return base + cross
            if (prev_lane == 'shm' and not same):  # infeasible now
                continue
            # both feasible. compare
            if lat(prev_lane) - lat(lane_map[key]) <= change_threshold_ms:
                lane_map[key] = prev_lane
    # local improve placement to reduce cost + churn
    base_cost, _ = placement_cost(routes, place, lane_map, topology, churn_weight, prev_place)
    improved=True; guard=0
    nlist = nodes(topology)
    while improved and guard<50:
        improved=False; guard+=1
        for s in syms:
            cur = place[s]; best = cur; best_cost = base_cost
            for n in nlist:
                if n==cur: continue
                place[s]=n
                c,_ = placement_cost(routes, place, lane_map, topology, churn_weight, prev_place)
                if c + 1e-9 < best_cost: best_cost, best = c, n
            place[s]=best
            if best!=cur:
                base_cost = best_cost
                improved=True
    return place, lane_map, base_cost
