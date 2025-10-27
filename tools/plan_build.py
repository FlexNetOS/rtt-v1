#!/usr/bin/env python3
import json, sys, hashlib, os, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
from ed25519_helper import sign as sign_msg  # user provides from previous kits
from solver_constraints import load_manifests
from solver_placement import optimize

def canon(obj): 
    import json
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
def load_json(p):
    return json.loads(open(p,'r',encoding='utf-8').read())
def load_last():
    for p in ["plans/last_applied.json", "plans/latest.json"]:
        fp = ROOT / p
        if fp.exists():
            try: return json.loads(fp.read_text())
            except Exception: pass
    return None

def main():
    if len(sys.argv) < 7:
        print("usage: plan_build.py <.rtt/routes.json> <.rtt/manifests> <key_id> <policy.json> <topology.json> <prefer_list> [--churn-weight=0.5] [--change-threshold-ms=0.2]")
        sys.exit(2)
    routes_f, mani_dir, key_id, policy_f, topo_f, prefer = sys.argv[1:7]
    churn_weight = 0.5
    change_thr = 0.2
    for arg in sys.argv[7:]:
        if arg.startswith("--churn-weight="): churn_weight = float(arg.split("=",1)[1])
        if arg.startswith("--change-threshold-ms="): change_thr = float(arg.split("=",1)[1])
    routes = load_json(routes_f)
    manis = load_manifests(mani_dir)
    topology = load_json(topo_f) if os.path.isfile(topo_f) else {"nodes":{"0":{"name":"n0"}}, "place":{}}
    prefer_list = [p.strip() for p in prefer.split(',') if p.strip()]
    last = load_last() or {}
    prev_place = last.get("placement", {})
    prev_lanes = {(r.get("from"), r.get("to")): r.get("lane") for r in last.get("routes_add", []) if r.get("from") and r.get("to") and r.get("lane")}
    # Optimize placement and lanes with churn penalty
    place, lane_map, total_cost = optimize(manis, routes.get("routes", []), topology, prev_place, prev_lanes, prefer_list, churn_weight, change_thr)
    # Build routes_add with lanes
    add = []
    for r in sorted(routes.get("routes", []), key=lambda x: (x["from"], x["to"])):
        lane = lane_map.get((r["from"], r["to"]), "uds")
        add.append({"from": r["from"], "to": r["to"], "lane": lane})
    # Plan
    plan = {"plan_id":"sha256-PLACEHOLDER","routes_add": add, "routes_del": [], "order":[f"A{i}" for i in range(1, len(add)+1)], "placement": place}
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
    # analysis
    analysis = {"total_cost": total_cost, "moved": len([1 for s,n in place.items() if prev_place.get(s) and prev_place[s]!=n]), "changed_routes": len([1 for r in add if prev_lanes.get((r['from'], r['to'])) and prev_lanes[(r['from'], r['to'])]!=r['lane']])}
    (ROOT / "plans" / "analysis.json").write_text(json.dumps(analysis, indent=2))
    print(json.dumps(analysis, indent=2))
    print(f"[OK] wrote {out}")
if __name__ == "__main__":
    main()
