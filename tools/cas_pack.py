#!/usr/bin/env python3
import json, sys, pathlib, struct
ROOT = pathlib.Path(__file__).resolve().parents[1]
CAS = ROOT / ".rtt" / "registry" / "cas" / "sha256"
PACK = ROOT / ".rtt" / "registry" / "pack" / "agents.pack"
LUT  = ROOT / ".rtt" / "registry" / "pack" / "index.lut"

def build_pack():
    entries = []
    offset = 0
    with open(PACK, "wb") as f:
        for p in sorted(CAS.glob("*.json")):
            data = p.read_bytes()
            entries.append((p.stem, offset, len(data)))
            f.write(struct.pack(">I", len(data)))
            f.write(data)
            offset += 4 + len(data)
    lut = {h: {"offset": off, "len": ln} for h, off, ln in entries}
    LUT.write_text(json.dumps(lut, indent=2))
    print(f"[OK] wrote {PACK} and {LUT}")

if __name__ == "__main__":
    build_pack()
