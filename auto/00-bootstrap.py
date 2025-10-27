#!/usr/bin/env python3
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
for d in ["cache","wal","sockets","manifests","drivers","tuned"]:
    (ROOT/".rtt"/d).mkdir(parents=True, exist_ok=True)
print("[OK] Bootstrap complete:", ROOT)
