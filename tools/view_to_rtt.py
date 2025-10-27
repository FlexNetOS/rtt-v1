#!/usr/bin/env python3
import json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
MANI = ROOT / ".rtt" / "manifests"

def to_rtt(agent):
    id_ = agent["id"]
    ver = agent.get("version","1.0.0")
    saddr = agent.get("rtt_saddr", f"rtt://agent/api/{id_}@{ver}")
    return {
        "$schema":"https://rtt/spec/v1",
        "symbol":{
            "saddr": saddr,
            "type":"api",
            "direction":"provider",
            "capabilities":["request","response"],
            "inputs":[{"name":"input","schema":"json://generic"}],
            "outputs":[{"name":"output","schema":"json://generic"}],
            "qos": agent.get("qos", {"latency_budget_ms":1000,"throughput_qps":1}),
            "version_set": f">={ver} <{int(ver.split('.')[0])+1}.0",
            "auth":{"mode":"caps","scopes":[f"{id_}.invoke"]},
            "tags":{"provider_view":"true"}
        }
    }

def main():
    if len(sys.argv) < 2:
        print("usage: view_to_rtt.py providers/<prov>/.<prov>/agents/*.agent.json")
        sys.exit(2)
    MANI.mkdir(parents=True, exist_ok=True)
    for p in sys.argv[1:]:
        ag = json.loads(open(p, 'r', encoding='utf-8').read())
        doc = to_rtt(ag)
        name = pathlib.Path(p).stem
        out = MANI / f"agent.{name}.json"
        out.write_text(json.dumps(doc, indent=2))
        print(f"[OK] wrote {out}")
if __name__ == "__main__":
    main()
