#!/usr/bin/env python3
import os, sys, json, pathlib, time, hashlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
WAL = ROOT/".rtt"/"wal"
def merkle(prev_hash: str, content: bytes) -> str:
    return hashlib.sha256((prev_hash+hashlib.sha256(content).hexdigest()).encode()).hexdigest()
plan_arg = sys.argv[1] if len(sys.argv)>1 else (ROOT/"plans"/"latest.plan.json").read_text().strip()
plan_path = ROOT/"plans"/plan_arg
plan = json.loads(plan_path.read_text(encoding="utf-8"))
prev = (WAL/"LATEST").read_text(encoding="utf-8").strip() if (WAL/"LATEST").exists() else "GENESIS"
frame = {"ts": time.time(), "plan_id": plan.get("plan_id"), "prev": prev, "apply": plan.get("routes_add",[])}
blob = json.dumps(frame, sort_keys=True).encode()
root = merkle(prev, blob)
fn = WAL/f"{int(frame['ts'])}-{root[:12]}.wal.json"
fn.write_text(json.dumps({"root":root, "frame":frame}, indent=2), encoding="utf-8")
(WAL/"LATEST").write_text(root, encoding="utf-8")
(ROOT/".rtt"/"cache"/"desired.graph.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
print("[OK] applied plan, wal:", fn)
