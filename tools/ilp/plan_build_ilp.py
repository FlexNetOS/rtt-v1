#!/usr/bin/env python3
import json, sys, os, hashlib
from pathlib import Path
from .solver_ilp import solve_ilp
from ..common.io import load_json
from ..common.crypto_ed25519 import sign
from ..common.util import canon

ROOT = Path(__file__).resolve().parents[2]

def main():
    if len(sys.argv) < 8:
        print("usage: plan_build_ilp.py <.rtt/routes.json> <.rtt/manifests> <key_id> <.rtt/policy.json> <.rtt/topology.json> <prefer_list> <admit_priority> [plans/last_applied.json]")
        sys.exit(2)
    routes_f, mani_dir, key_id, policy_f, topo_f, prefer, admit = sys.argv[1:8]
    last = sys.argv[8] if len(sys.argv)>8 else None
    prefer_list = [p.strip() for p in prefer.split(',') if p.strip()]
    res = solve_ilp(routes_f, mani_dir, key_id, policy_f, topo_f, prefer_list, float(admit), last_plan_file=last)
    if not res.get("ok"):
        print(json.dumps(res, indent=2)); sys.exit(1)
    plan = {"plan_id":"sha256-PLACEHOLDER","routes_add": res["routes_add"], "routes_del": [], "order":[f"A{i}" for i in range(1, len(res['routes_add'])+1)], "placement": res["placement"]}
    payload = canon(plan); pid = "sha256-" + hashlib.sha256(payload).hexdigest()
    plan["plan_id"] = pid
    priv = (ROOT / ".rtt" / "registry" / "keys" / "private" / f"{key_id}.priv").read_text().strip()
    sig = sign(priv, payload)
    plan["sign"] = {"alg":"ed25519","key_id": key_id, "sig": sig}
    out = ROOT / "plans" / (pid + ".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2))
    (ROOT / "plans" / "latest.json").write_text(json.dumps(plan, indent=2))
    # summary
    summary = {"admitted": len(res['routes_add']), "rejected": res['rejects']}
    (ROOT / "plans" / "analysis.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"[OK] wrote {out}")

if __name__ == "__main__":
    main()
