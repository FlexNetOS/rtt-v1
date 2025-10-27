#!/usr/bin/env python3
import json, sys, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
from ed25519_helper import verify as verify_sig
def canon(obj): 
    import json
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
def main():
    if len(sys.argv)<2: print("usage: plan_verify.py plans/<hash>.json"); sys.exit(2)
    f = Path(sys.argv[1]); plan = json.loads(f.read_text())
    payload = dict(plan); payload.pop("sign", None)
    pid = "sha256-" + hashlib.sha256(canon(payload)).hexdigest()
    if pid != plan.get("plan_id"): print("[FAIL] plan_id mismatch"); sys.exit(1)
    sign = plan.get("sign",{}); pub = (ROOT/".rtt/registry/trust/keys"/f"{sign.get('key_id')}.pub").read_text().strip().split(":",1)[1]
    if not verify_sig(pub, canon(payload), sign.get("sig","")): print("[FAIL] signature invalid"); sys.exit(1)
    print("[OK] plan verified")
if __name__ == "__main__": main()
