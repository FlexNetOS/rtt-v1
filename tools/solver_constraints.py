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

def version_of_saddr(saddr:str)->str:
    if '@' in saddr: return saddr.split('@',1)[1].split('#',1)[0]
    return '1.0.0'
def version_set(sym)->str:
    return sym.get('version_set', '>=0.0.0')
def qos(sym):
    return sym.get('qos', {"latency_budget_ms": 2000, "throughput_qps": 1})
def supports_lane(sym, lane):
    tags = sym.get('tags', {})
    if lane == 'shm': return tags.get('supports_shm', False)
    if lane in ('uds','tcp'): return True
    return False
