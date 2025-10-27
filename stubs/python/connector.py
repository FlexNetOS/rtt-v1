#!/usr/bin/env python3
import sys, json
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    req=json.loads(line)
    print(json.dumps({"id": req.get("id","0"), "result": {"ok": True}, "error": None}), flush=True)
