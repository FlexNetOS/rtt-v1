#!/usr/bin/env python3
import json, sys, base64, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
from ed25519_helper import verify as verify_sig

def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def main():
    if len(sys.argv) < 2:
        print("usage: plan_verify.py plans/<hash>.json")
        sys.exit(2)
    f = Path(sys.argv[1])
    plan = json.loads(f.read_text())
    sign = plan.get("sign", {})
    pid = plan.get("plan_id", "")
    payload = dict(plan); payload.pop("sign", None)
    payload_bytes = canon(payload)
    pid_chk = "sha256-" + hashlib.sha256(payload_bytes).hexdigest()
    if pid_chk != pid:
        print("[FAIL] plan_id mismatch"); sys.exit(1)
    pubfile = ROOT / ".rtt" / "registry" / "trust" / "keys" / f"{sign['key_id']}.pub"
    pub_b64 = pubfile.read_text().strip().split(":",1)[1]
    if not verify_sig(pub_b64, payload_bytes, sign["sig"]):
        print("[FAIL] signature invalid"); sys.exit(1)
    print("[OK] plan verified")
if __name__ == "__main__":
    main()
