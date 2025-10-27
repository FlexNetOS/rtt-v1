#!/usr/bin/env python3
import json, sys, hashlib, glob, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
from ed25519_helper import sign as sign_msg

def canon(obj): 
    import json
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def saddr_from_agent(ag):
    ver = ag.get("version","1.0.0")
    return ag.get("rtt_saddr", f"rtt://agent/api/{ag['id']}@{ver}")

def load_manifests(mdir):
    out={}
    for p in glob.glob(os.path.join(mdir, "*.json")):
        try:
            m=json.load(open(p,'r',encoding='utf-8'))
            out[m["symbol"]["saddr"]]=m["symbol"]
        except Exception: pass
    return out

def autowire(routes, mcp_provider, skills_dir, agents_dir, manifests_dir):
    # Simple strategy: connect agent.id to MCP tool with same name.
    idx_agents = {}
    for p in glob.glob(os.path.join(agents_dir, "*.agent.json")):
        a = json.load(open(p,'r',encoding='utf-8'))
        idx_agents[a["id"]] = a
    tools=[]
    mcp_tools_json = list(glob.glob(f"mcp/{mcp_provider}/tools.json"))
    if mcp_tools_json:
        tools = json.load(open(mcp_tools_json[0],'r',encoding='utf-8')).get("tools",[])
    routes_auto=[]
    for t in tools:
        name = t.get("name")
        if name in idx_agents:
            frm = saddr_from_agent(idx_agents[name])
            to = f"rtt://mcp/{mcp_provider}/tool/{name}@{t.get('version','1.0.0')}"
            routes_auto.append({"from": frm, "to": to})
    # Skills-based autowire
    skill_caps=set()
    for p in glob.glob(os.path.join(skills_dir, "*.skill.json")):
        s=json.load(open(p,'r',encoding='utf-8'))
        for c in s.get("provides", []): skill_caps.add(c)
    for t in tools:
        caps = set(t.get("capabilities", []))
        if skill_caps & caps and t.get("name") not in idx_agents:
            # find any agent that claims matching cap in tags
            for a in idx_agents.values():
                acaps=set(a.get("caps",[]))
                if skill_caps & acaps:
                    frm = saddr_from_agent(a)
                    to = f"rtt://mcp/{mcp_provider}/tool/{t.get('name')}@{t.get('version','1.0.0')}"
                    routes_auto.append({"from": frm, "to": to})
                    break
    # merge unique
    existing=set((r["from"],r["to"]) for r in routes.get("routes",[]))
    for r in routes_auto:
        if (r["from"], r["to"]) not in existing:
            routes["routes"].append(r)
            existing.add((r["from"], r["to"]))
    return routes

def invariant_gate(routes, manifests_dir):
    # Weak gate: endpoints exist, no dupes, no self loops.
    errs=[]
    manis=load_manifests(manifests_dir)
    for r in routes.get("routes", []):
        if r["from"] not in manis: errs.append({"missing_from": r["from"]})
        if r["to"] not in manis: errs.append({"missing_to": r["to"]})
        if r["from"] == r["to"]: errs.append({"self_loop": r})
    seen=set()
    for r in routes.get("routes", []):
        k=(r["from"], r["to"])
        if k in seen: errs.append({"duplicate": r})
        seen.add(k)
    return errs

def main():
    if len(sys.argv) < 6:
        print("usage: plan_build.py <.rtt/routes.json> <.rtt/manifests> <key_id> <agents_dir> <mcp_provider> [skills_dir] [--autowire]")
        sys.exit(2)
    routes_f, mani_dir, key_id, agents_dir, mcp_provider = sys.argv[1:6]
    skills_dir = sys.argv[6] if len(sys.argv) > 6 and not sys.argv[6].startswith("--") else "skills"
    autowire_flag = "--autowire" in sys.argv
    routes = json.load(open(routes_f,'r',encoding='utf-8'))
    if autowire_flag:
        routes = autowire(routes, mcp_provider, skills_dir, agents_dir, mani_dir)
    errs = invariant_gate(routes, mani_dir)
    if errs:
        print(json.dumps({"ok": False, "errors": errs}, indent=2))
        sys.exit(1)
    # Deterministic plan
    add = sorted([{"from": r["from"], "to": r["to"]} for r in routes["routes"]], key=lambda x: (x["from"], x["to"]))
    plan = { "plan_id":"sha256-PLACEHOLDER", "routes_add": add, "routes_del": [], "order":[f"A{i}" for i in range(1, len(add)+1)] }
    payload = canon(plan)
    pid = "sha256-" + hashlib.sha256(payload).hexdigest()
    plan["plan_id"] = pid
    # Sign
    priv = (ROOT / ".rtt" / "registry" / "keys" / "private" / f"{key_id}.priv").read_text().strip()
    from ed25519_helper import sign as sign_msg
    sig = sign_msg(priv, payload)
    plan["sign"] = {"alg":"ed25519","key_id": key_id, "sig": sig}
    out = ROOT / "plans" / (pid + ".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2))
    (ROOT / "plans" / "latest.json").write_text(json.dumps(plan, indent=2))
    print(f"[OK] wrote {out}")
if __name__ == "__main__": main()
