#!/usr/bin/env python3
import json, sys, os, hashlib, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
CAS = ROOT / ".rtt" / "registry" / "cas" / "sha256"
INDEX = ROOT / ".rtt" / "registry" / "index.json"

def sha256_bytes(b: bytes)->str:
    import hashlib
    return hashlib.sha256(b).hexdigest()

def normalize(obj)->bytes:
    return json.dumps(obj, separators=(',', ':'), sort_keys=True).encode('utf-8')

def main():
    if len(sys.argv) < 2:
        print("usage: cas_ingest.py <agents/common/*.agent.json ...>")
        sys.exit(2)
    idx = json.loads(INDEX.read_text())
    agents = idx.get("agents", {})
    for p in sys.argv[1:]:
        obj = json.loads(open(p, 'r', encoding='utf-8').read())
        key = f"{obj['id']}@{obj.get('version','1')}"
        b = normalize(obj)
        h = sha256_bytes(b)
        out = CAS / f"{h}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b)
        agents[key] = f"sha256:{h}"
        print(f"[OK] {key} -> {out}")
    idx["agents"] = agents
    INDEX.write_text(json.dumps(idx, indent=2))
    print(f"[OK] updated index -> {INDEX}")
if __name__ == "__main__":
    main()
