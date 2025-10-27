#!/usr/bin/env python3
import time, json, random, sys
dur = float(sys.argv[1]) if len(sys.argv)>1 else 5.0
t0 = time.time()
while time.time()-t0 < dur:
    rec = {"ts": time.time(), "route_id": "demo", "p50": 0.2, "p95": 0.8, "p99": 1.3, "qdepth": random.randint(0,10), "drops": 0, "breaker":"closed"}
    print(json.dumps(rec)); time.sleep(0.1)
