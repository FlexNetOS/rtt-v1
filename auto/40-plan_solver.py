#!/usr/bin/env python3
import os, json, pathlib, hashlib, time
ROOT = pathlib.Path(__file__).resolve().parents[1]
routes = json.loads((ROOT/".rtt"/"routes.json").read_text(encoding="utf-8"))
symbols = {}
for mf in (ROOT/".rtt"/"manifests").glob("*.json"):
    obj = json.loads(mf.read_text(encoding="utf-8"))
    s = obj.get("symbol",{})
    symbols[s.get("saddr")] = s
plan = {"plan_id":"", "created_at":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "routes_add":[], "routes_del":[], "order":[]}
for r in routes.get("routes", []):
    frm = r["from"]; to = r["to"]
    lane = "shm" if any(k for k in symbols if k.startswith(to.split("@")[0])) else "uds"
    plan["routes_add"].append({"from":frm,"to":to,"lane":lane})
    plan["order"].append(f"{frm}->{to}")
h = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
plan["plan_id"] = f"sha256-{h}"
out = ROOT/"plans"/f"{h[:16]}.plan.json"
out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
(ROOT/"plans"/"latest.plan.json").write_text(out.name, encoding="utf-8")
print("[OK] wrote", out)
