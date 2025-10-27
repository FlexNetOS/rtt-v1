#!/usr/bin/env python3
import json, sys, hashlib, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CAS = ROOT / ".rtt" / "registry" / "cas" / "sha256"
INDEX = ROOT / ".rtt" / "registry" / "index.json"
def canon(obj): 
    import json
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
def sha256(b): import hashlib; return hashlib.sha256(b).hexdigest()
def main():
    paths = sys.argv[1:] or ["agents/common/*.agent.json"]
    idx = json.loads(INDEX.read_text()) if INDEX.exists() else {"agents":{}, "mcp_tools":{}, "skills":{}, "signers":[]}
    idx.setdefault("agents", {})
    CAS.mkdir(parents=True, exist_ok=True)
    for pattern in paths:
        for p in glob.glob(pattern):
            obj = json.loads(open(p,'r',encoding='utf-8').read())
            key = f"{obj['id']}@{obj.get('version','1.0.0')}"
            h = sha256(canon({"type":"agent","agent":obj}))
            (CAS / f"{h}.json").write_bytes(canon({"type":"agent","agent":obj}))
            idx["agents"][key] = f"sha256:{h}"
            print(f"[OK] agent {key} -> sha256:{h}")
    INDEX.write_text(json.dumps(idx, indent=2))
if __name__ == "__main__": main()
