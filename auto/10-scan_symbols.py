#!/usr/bin/env python3
import os, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = ROOT/"rtt_elite_addon"/"index"/"symbols.index.json"
MANIFESTS = ROOT/".rtt"/"manifests"
symbols = []
for mf in MANIFESTS.glob("*.json"):
    try:
        obj = json.loads(mf.read_text(encoding="utf-8"))
        saddr = obj.get("symbol",{}).get("saddr")
        stype = obj.get("symbol",{}).get("type")
        if saddr and stype:
            symbols.append({"source":"manifest","saddr":saddr,"type":stype,"path":str(mf)})
    except Exception as e:
        pass
INDEX.parent.mkdir(parents=True, exist_ok=True)
INDEX.write_text(json.dumps({"symbols":symbols}, indent=2), encoding="utf-8")
print("[OK] wrote", INDEX)
