import json, glob, os
def load_json(p):
    with open(p, 'r', encoding='utf-8') as f: return json.load(f)
def load_manifests(mdir):
    out={}
    for p in glob.glob(os.path.join(mdir, "*.json")):
        try:
            m=load_json(p); sym=m['symbol']; out[sym['saddr']]=sym
        except Exception:
            pass
    return out
