#!/usr/bin/env python3
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    req = json.loads(line)
    res = {"id": req["id"], "result": {"ok": True}, "error": None}
    print(json.dumps(res), flush=True)
