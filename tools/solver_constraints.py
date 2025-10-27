import json, os, glob
from .semver import check_set
from .policy_match import allowed

LANE_BASE_LAT_MS = {'shm':0.2, 'uds':0.6, 'tcp':1.5}

def load_manifests(mdir):
    out={}
    for p in glob.glob(os.path.join(mdir, "*.json")):
        try:
            m=json.load(open(p,'r',encoding='utf-8'))
            sym=m['symbol']; out[sym['saddr']] = sym
        except Exception:
            pass
    return out

def load_topology(path):
    try:
        return json.load(open(path,'r',encoding='utf-8'))
    except Exception:
        return {"nodes":{"0":{"name":"n0"}}, "place":{}}

def numa_penalty_ms(topology, a, b):
    na = topology.get('place', {}).get(a, '0')
    nb = topology.get('place', {}).get(b, '0')
    return 0.4 if na != nb else 0.0

def supports_lane(sym, lane):
    # heuristic via tags or type
    tags = sym.get('tags', {})
    if lane == 'shm':
        return tags.get('supports_shm', False)
    if lane == 'uds':
        return True
    if lane == 'tcp':
        return True
    return False

def version_of_saddr(saddr:str)->str:
    if '@' in saddr:
        return saddr.split('@',1)[1].split('#',1)[0]
    return '1.0.0'

def version_set(sym)->str:
    return sym.get('version_set', '>=0.0.0')

def qos(sym):
    return sym.get('qos', {"latency_budget_ms": 2000, "throughput_qps": 1})

def feasible_lane(sym_from, sym_to, prefer):
    for lane in prefer:
        if supports_lane(sym_from, lane) and supports_lane(sym_to, lane):
            return lane
    # default
    return 'uds'

def route_ok(sym_from, sym_to, lane, topology):
    # semver meet
    vf = version_of_saddr(sym_from['saddr'])
    vt = version_of_saddr(sym_to['saddr'])
    if not check_set(vf, version_set(sym_to)): return False, "from_version_not_accepted_by_to"
    if not check_set(vt, version_set(sym_from)): return False, "to_version_not_accepted_by_from"
    # qos latency
    budget = min(qos(sym_from).get('latency_budget_ms', 999999), qos(sym_to).get('latency_budget_ms', 999999))
    lat = LANE_BASE_LAT_MS.get(lane, 2.0) + numa_penalty_ms(topology, sym_from['saddr'], sym_to['saddr'])
    if lat*1.0 >= budget/1000.0:  # ms to sec? budgets in ms so compare ms
        # keep units consistent: lat is in ms
        lat_ms = LANE_BASE_LAT_MS.get(lane, 2.0)*1000.0 + numa_penalty_ms(topology, sym_from['saddr'], sym_to['saddr'])*1000.0
        if lat_ms >= budget:
            return False, "latency_budget_violation"
    return True, ""

def solve(routes, manifests_dir, policy, topology, prefer):
    manis = load_manifests(manifests_dir)
    result = []
    rejects = []
    seen = set()
    for r in routes.get('routes', []):
        sfrom = r['from']; sto = r['to']
        if (sfrom, sto) in seen: continue
        seen.add((sfrom, sto))
        if sfrom not in manis or sto not in manis:
            rejects.append({"route":r, "reason":"missing_manifest"}); continue
        if not allowed(policy, sfrom, sto):
            rejects.append({"route":r, "reason":"policy_denied"}); continue
        lane = feasible_lane(manis[sfrom], manis[sto], prefer)
        ok, why = route_ok(manis[sfrom], manis[sto], lane, topology)
        if not ok:
            rejects.append({"route": {"from":sfrom,"to":sto,"lane":lane}, "reason":why}); continue
        result.append({"from": sfrom, "to": sto, "lane": lane})
    # objective: sort by predicted latency then stable keys
    def cost(x):
        base = LANE_BASE_LAT_MS.get(x['lane'], 2.0) + numa_penalty_ms(topology, x['from'], x['to'])
        return (base, x['from'], x['to'])
    result.sort(key=cost)
    return result, rejects
