#!/usr/bin/env python3
import os, base64, sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PUBS = ROOT / ".rtt" / "registry" / "trust" / "keys"
PRIVS = ROOT / ".rtt" / "registry" / "keys" / "private"

def main():
    key_id = sys.argv[1] if len(sys.argv) > 1 else "dev-ed25519"
    # Try nacl first
    try:
        from nacl.signing import SigningKey
        sk = SigningKey.generate()
        vk = sk.verify_key
        priv_b64 = base64.b64encode(bytes(sk)).decode()
        pub_b64 = base64.b64encode(bytes(vk)).decode()
    except Exception:
        print("PyNaCl missing. Please use the Rust or Go signer to generate keys.", file=sys.stderr)
        print("Example:\n  rtt-sign gen\n  or build tools/rtt_sign_rs then run it.", file=sys.stderr)
        sys.exit(2)
    PUBS.mkdir(parents=True, exist_ok=True)
    PRIVS.mkdir(parents=True, exist_ok=True)
    (PUBS / f"{key_id}.pub").write_text(f"ed25519:{pub_b64}\n")
    (PRIVS / f"{key_id}.priv").write_text(f"{priv_b64}\n")
    idx = ROOT / ".rtt" / "registry" / "index.json"
    if idx.exists():
        j = json.loads(idx.read_text())
    else:
        j = {}
    j.setdefault("signers", [])
    if f"ed25519:{key_id}" not in j["signers"]:
        j["signers"].append(f"ed25519:{key_id}")
    idx.write_text(json.dumps(j, indent=2))
    print(f"[OK] wrote keys {key_id} and updated index.json")
if __name__ == "__main__":
    main()
