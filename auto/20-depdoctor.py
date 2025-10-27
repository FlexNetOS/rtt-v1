#!/usr/bin/env python3
import os, json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[1]
plan = {"unify":{}, "notes":[]}
for pkg in ROOT.rglob("package.json"):
    try:
        obj = json.loads(pkg.read_text(encoding="utf-8"))
        for sec in ["dependencies","devDependencies","peerDependencies"]:
            deps = obj.get(sec,{})
            for k,v in deps.items():
                plan["unify"].setdefault(k, set()).add(v)
    except Exception as e:
        plan["notes"].append(f"bad package.json {pkg}: {e}")
for req in list(ROOT.rglob("requirements.txt")) + list(ROOT.rglob("requirements.in")):
    for line in req.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line or line.startswith("#"): continue
        k = re.split(r"[<>=!~ ]", line)[0]
        plan["unify"].setdefault(k, set()).add(line.replace(k,"").strip())
unify_str = {k: sorted(list(v)) for k,v in plan["unify"].items()}
out = ROOT/"plans"/"dep.unify.json"
out.write_text(json.dumps({"unify":unify_str, "notes":plan["notes"]}, indent=2), encoding="utf-8")
(ROOT/"plans"/"LATEST").write_text("dep.unify.json", encoding="utf-8")
print("[OK] wrote", out)
