#!/usr/bin/env python3
import json, sys, base64, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
from ed25519_helper import sign as sign_msg

def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def stable_plan(routes_file: Path, manifests_dir: Path):
    routes = json.loads(routes_file.read_text())
    add = [{"from": r["from"], "to": r["to"]} for r in routes["routes"]]
    # stable order for deterministic plan
    add = sorted(add, key=lambda x: (x["from"], x["to"]))
    plan = {
        "plan_id": "sha256-PLACEHOLDER",
        "routes_add": add,
        "routes_del": [],
        "order": [f"A{i}" for i in range(1, len(add)+1)],
    }
    payload = canon(plan)
    pid = "sha256-" + hashlib.sha256(payload).hexdigest()
    plan["plan_id"] = pid
    return plan, payload, pid

def main():
    if len(sys.argv) < 4:
        print("usage: plan_build.py <.rtt/routes.json> <.rtt/manifests> <key_id>")
        sys.exit(2)
    routes = Path(sys.argv[1]); mani = Path(sys.argv[2]); key_id = sys.argv[3]
    plan, payload, pid = stable_plan(routes, mani)
    priv = (ROOT / ".rtt" / "registry" / "keys" / "private" / f"{key_id}.priv").read_text().strip()
    sig_b64 = sign_msg(priv, payload)
    plan["sign"] = {"alg":"ed25519", "key_id": key_id, "sig": sig_b64}
    out = ROOT / "plans" / (pid + ".json")
    out.write_text(json.dumps(plan, indent=2))
    # also write latest.json
    (ROOT / "plans" / "latest.json").write_text(json.dumps(plan, indent=2))
    print(f"[OK] wrote {out}")
if __name__ == "__main__":
    main()
