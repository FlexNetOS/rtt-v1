#!/usr/bin/env python3
import json, sys, hashlib, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
from ed25519_helper import sign as sign_msg  # provided by previous drop-ins or user
from solver_constraints import solve

def canon(obj): 
    import json
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def load_json(p):
    return json.loads(open(p,'r',encoding='utf-8').read())

def main():
    if len(sys.argv) < 6:
        print("usage: plan_build.py <.rtt/routes.json> <.rtt/manifests> <key_id> <policy.json> <topology.json?> [prefer=shm,uds,tcp]")
        sys.exit(2)
    routes_f, mani_dir, key_id, policy_f, topo_f = sys.argv[1:6]
    prefer = sys.argv[6] if len(sys.argv)>6 else "shm,uds,tcp"
    prefer_list = [p.strip() for p in prefer.split(',') if p.strip()]
    routes = load_json(routes_f)
    policy = load_json(policy_f) if os.path.isfile(policy_f) else {"allow":[{"from":"*","to":"*"}]}
    topology = load_json(topo_f) if os.path.isfile(topo_f) else {"nodes":{"0":{"name":"n0"}}, "place":{}}
    routes_add, rejects = solve(routes, mani_dir, policy, topology, prefer_list)
    if rejects:
        print(json.dumps({"ok": False, "rejected": rejects}, indent=2))
        sys.exit(1)
    plan = {"plan_id":"sha256-PLACEHOLDER","routes_add": routes_add, "routes_del": [], "order":[f"A{i}" for i in range(1, len(routes_add)+1)]}
    payload = canon(plan)
    pid = "sha256-" + hashlib.sha256(payload).hexdigest()
    plan["plan_id"] = pid
    priv = (ROOT / ".rtt" / "registry" / "keys" / "private" / f"{key_id}.priv").read_text().strip()
    sig = sign_msg(priv, payload)
    plan["sign"] = {"alg":"ed25519","key_id": key_id, "sig": sig}
    out = ROOT / "plans" / (pid + ".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2))
    (ROOT / "plans" / "latest.json").write_text(json.dumps(plan, indent=2))
    print(f"[OK] wrote {out}")
if __name__ == "__main__":
    main()
