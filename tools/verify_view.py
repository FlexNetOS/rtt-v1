#!/usr/bin/env python3
import json, sys, base64
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
from ed25519_helper import verify as verify_sig

def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def main():
    if len(sys.argv) < 2:
        print("usage: verify_view.py <views/*.view.json>")
        sys.exit(2)
    vf = Path(sys.argv[1])
    view = json.loads(vf.read_text())
    sign = view.get("sign")
    if not sign or sign.get("alg") != "ed25519":
        print("[FAIL] missing or invalid sign field"); sys.exit(1)
    key_id = sign["key_id"]
    sig = sign["sig"]
    pubfile = ROOT / ".rtt" / "registry" / "trust" / "keys" / f"{key_id}.pub"
    if not pubfile.exists():
        print(f"[FAIL] missing pub key for {key_id}"); sys.exit(1)
    pub_b64 = pubfile.read_text().strip().split(":",1)[1]
    payload = dict(view); payload.pop("sign", None)
    ok = verify_sig(pub_b64, canon(payload), sig)
    if not ok:
        print("[FAIL] signature mismatch"); sys.exit(1)
    print("[OK] view signature valid")
if __name__ == "__main__":
    main()
