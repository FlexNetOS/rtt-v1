#!/usr/bin/env python3
import json, sys, base64, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
from ed25519_helper import sign as sign_msg

def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def main():
    if len(sys.argv) < 3:
        print("usage: sign_view.py <views/*.view.json> <key_id>")
        sys.exit(2)
    vf = Path(sys.argv[1])
    key_id = sys.argv[2]
    priv = (ROOT / ".rtt" / "registry" / "keys" / "private" / f"{key_id}.priv").read_text().strip()
    view = json.loads(vf.read_text())
    # strip existing sign
    view.pop("sign", None)
    payload = canon(view)
    sig_b64 = sign_msg(priv, payload)
    view["sign"] = {"alg":"ed25519", "key_id": key_id, "sig": sig_b64}
    vf.write_text(json.dumps(view, indent=2))
    print(f"[OK] signed {vf} with {key_id}")
if __name__ == "__main__":
    main()
