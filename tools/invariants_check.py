#!/usr/bin/env python3
import json, sys, os, glob
from pathlib import Path

def load_json(p): return json.loads(open(p,'r',encoding='utf-8').read())

def check_exists(routes, mani_dir):
    # every from and to must exist as saddr in manifests
    saddr = set()
    for p in glob.glob(os.path.join(mani_dir, "*.json")):
        try:
            m = load_json(p)
            saddr.add(m["symbol"]["saddr"])
        except Exception: pass
    missing = []
    for r in routes.get("routes", []):
        if r["from"] not in saddr: missing.append(("from", r["from"]))
        if r["to"] not in saddr: missing.append(("to", r["to"]))
    return missing

def check_dupes(routes):
    seen=set(); dupes=[]
    for r in routes.get("routes", []):
        k=(r["from"], r["to"])
        if k in seen: dupes.append({"from":r["from"],"to":r["to"]})
        seen.add(k)
    return dupes

def main():
    if len(sys.argv)<3:
        print("usage: invariants_check.py <.rtt/routes.json> <.rtt/manifests>"); sys.exit(2)
    routes = load_json(sys.argv[1])
    mani_dir = sys.argv[2]
    errs=[]
    missing = check_exists(routes, mani_dir)
    if missing: errs.append({"missing_endpoints": missing})
    dup = check_dupes(routes)
    if dup: errs.append({"duplicate_routes": dup})
    # quick self-loop check
    for r in routes.get("routes", []):
        if r["from"] == r["to"]:
            errs.append({"self_loop": r})
    if errs:
        print(json.dumps({"ok": False, "errors": errs}, indent=2)); sys.exit(1)
    print(json.dumps({"ok": True}, indent=2))

if __name__ == "__main__": main()
