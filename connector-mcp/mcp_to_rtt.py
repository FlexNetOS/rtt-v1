#!/usr/bin/env python3
import os, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".rtt" / "manifests"

def mcp_tool_to_rtt(provider: str, tool: dict) -> dict:
    name = tool.get("name","tool")
    ver = tool.get("version","1.0.0")
    saddr = f"rtt://mcp/{provider}/tool/{name}@{ver}"
    caps = ["request","response"]
    qos = {"latency_budget_ms": 2000, "throughput_qps": 5}
    return {
        "$schema":"https://rtt/spec/v1",
        "symbol":{
            "saddr": saddr,
            "type":"api",
            "direction":"provider",
            "capabilities": caps,
            "inputs":[{"name":"request","schema":"json://mcp.request"}],
            "outputs":[{"name":"response","schema":"json://mcp.response"}],
            "qos": qos,
            "version_set": f">={ver} <{int(ver.split('.')[0])+1}.0",
            "auth":{"mode":"caps","scopes":["mcp.invoke"]},
            "tags":{"provider":provider, "mcp":"true"}
        }
    }

def main():
    if len(sys.argv) < 3:
        print("usage: mcp_to_rtt.py <provider> <tools.json>", file=sys.stderr)
        sys.exit(2)
    provider = sys.argv[1]
    tools_path = Path(sys.argv[2])
    tools = json.loads(tools_path.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for t in tools.get("tools", []):
        doc = mcp_tool_to_rtt(provider, t)
        name = t.get("name","tool")
        (OUT / f"mcp.{provider}.tool.{name}.json").write_text(json.dumps(doc, indent=2))
        print(f"[OK] wrote {OUT / f'mcp.{provider}.tool.{name}.json'}")

if __name__ == "__main__":
    main()
