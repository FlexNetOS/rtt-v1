#!/usr/bin/env python3
import os, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFESTS = ROOT/".rtt"/"manifests"
DRIVERS = ROOT/".rtt"/"drivers"
outdir = DRIVERS/"generated"
outdir.mkdir(parents=True, exist_ok=True)
def stub_py(name, saddr):
    return f"""# Auto-generated connector stub (Python)\nfrom typing import Any\nclass Connector:\n    def probe(self, root: str):\n        return [{{'saddr':'{saddr}'}}]\n    def open(self, symbol: dict, params: dict):\n        return object()\n    def tx(self, handle: Any, data: bytes):\n        pass\n    def rx(self, handle: Any) -> bytes:\n        return b''\n    def close(self, handle: Any):\n        pass\n    def health(self, handle: Any):\n        return {{'ok': True}}\n"""\n
for mf in MANIFESTS.glob("*.json"):
    obj = json.loads(mf.read_text(encoding="utf-8"))
    s = obj.get("symbol",{})
    saddr = s.get("saddr","rtt://unknown")
    name = saddr.split("/")[-1].replace("@","_").replace("#","_")
    (outdir/f"{name}.py").write_text(stub_py(name, saddr), encoding="utf-8")
print("[OK] generated Python connector stubs in", outdir)
