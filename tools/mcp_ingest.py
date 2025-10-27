#!/usr/bin/env python3
import json, sys, hashlib, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAS = ROOT / ".rtt" / "registry" / "cas" / "sha256"
INDEX = ROOT / ".rtt" / "registry" / "index.json"
MANI = ROOT / ".rtt" / "manifests"

def canon(obj): 
    import json
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
def sha256(b): import hashlib; return hashlib.sha256(b).hexdigest()

def to_rtt(provider, t):
    name = t.get("name","tool")
    ver = t.get("version","1.0.0")
    return {
      "$schema":"https://rtt/spec/v1",
      "symbol":{
        "saddr": f"rtt://mcp/{provider}/tool/{name}@{ver}",
        "type":"api",
        "direction":"provider",
        "capabilities":["request","response"],
        "inputs":[{"name":"request","schema":"json://mcp.request"}],
        "outputs":[{"name":"response","schema":"json://mcp.response"}],
        "qos": {"latency_budget_ms": 2000, "throughput_qps": 5},
        "version_set": f">={ver} <{int(ver.split('.')[0])+1}.0",
        "auth":{"mode":"caps","scopes":["mcp.invoke"]},
        "tags":{"provider":provider}
      }
    }

def main():
    if len(sys.argv) < 3:
        print("usage: mcp_ingest.py <provider> <mcp/tools.json>"); sys.exit(2)
    prov = sys.argv[1]; jf = Path(sys.argv[2])
    tools = json.loads(jf.read_text()).get("tools", [])
    idx = json.loads(INDEX.read_text()) if INDEX.exists() else {"agents":{}, "mcp_tools":{}, "skills":{}, "signers":[]}
    idx.setdefault("mcp_tools", {})
    CAS.mkdir(parents=True, exist_ok=True); MANI.mkdir(parents=True, exist_ok=True)
    for t in tools:
        record = {"type":"mcp_tool","provider":prov,"tool":t}
        h = sha256(canon(record))
        (CAS / f"{h}.json").write_bytes(canon(record))
        key = f"{prov}/{t.get('name','tool')}@{t.get('version','1.0.0')}"
        idx["mcp_tools"][key] = f"sha256:{h}"
        # emit RTT manifest
        mani = to_rtt(prov, t)
        (MANI / f"mcp.{prov}.tool.{t.get('name','tool')}.json").write_text(json.dumps(mani, indent=2))
        print(f"[OK] MCP {key} -> CAS sha256:{h}")
    INDEX.write_text(json.dumps(idx, indent=2))
    print(f"[OK] updated index.json")
if __name__ == "__main__": main()
