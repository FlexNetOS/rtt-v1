#!/usr/bin/env python3
import json, sys, os, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = ROOT / ".rtt" / "registry" / "index.json"
CAS = ROOT / ".rtt" / "registry" / "cas" / "sha256"
OVERLAYS = ROOT / "overlays"
OUTROOT = ROOT / "providers"

def safe_mkdir(p: pathlib.Path):
    p.mkdir(parents=True, exist_ok=True)

def try_symlink(src: pathlib.Path, dst: pathlib.Path):
    try:
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        os.symlink(src, dst)
        return True
    except Exception:
        return False

def write_proxy(src: pathlib.Path, dst: pathlib.Path):
    obj = {"$schema":"https://rtt/agent-proxy/v1","ref":os.path.relpath(src, dst.parent)}
    dst.write_text(json.dumps(obj, indent=2))

def resolve_hash(agent_key: str)->pathlib.Path:
    # agent_key format id@ver
    idver = agent_key
    idx = json.loads(INDEX.read_text())
    h = idx["agents"].get(idver)
    if not h or not h.startswith("sha256:"):
        raise SystemExit(f"[ERR] not in index: {idver}")
    return CAS / f"{h.split(':',1)[1]}.json"

def overlay_files(provider: str, env: str, idver: str):
    id_, ver = idver.split("@",1)
    files = []
    # provider-specific patch for the exact id or a generic
    p1 = OVERLAYS / "provider" / provider / f"{id_}.patch.json"
    if p1.exists(): files.append(p1)
    # env global, then id-specific
    p2 = OVERLAYS / "env" / env / "_global.patch.json"
    if p2.exists(): files.append(p2)
    p3 = OVERLAYS / "env" / env / f"{id_}.patch.json"
    if p3.exists(): files.append(p3)
    return files

def deep_merge(base, patch):
    if isinstance(base, dict) and isinstance(patch, dict):
        out = dict(base)
        for k,v in patch.items():
            out[k] = deep_merge(out.get(k), v) if k in out else v
        return out
    return patch

def apply_overlays(base_obj, files):
    out = base_obj
    for p in files:
        with open(p, "r", encoding="utf-8") as f:
            out = deep_merge(out, json.load(f))
    return out

def materialize(view_file: pathlib.Path):
    view = json.loads(view_file.read_text())
    provider = view["provider"]
    env = "prod"
    mount = ROOT / view["mount"]
    safe_mkdir(mount)
    for e in view["entries"]:
        idv = e["id"]
        src = resolve_hash(idv)
        # apply overlays and write a realized file beside the link for clarity
        realized = json.loads(src.read_text())
        realized = apply_overlays(realized, overlay_files(provider, env, idv))
        realized_name = f"{idv.replace('@','_')}.agent.json"
        realized_path = mount / realized_name
        realized_path.write_text(json.dumps(realized, indent=2))
        # create a link file pointing to CAS for provenance
        link_name = realized_name + ".link"
        link_path = mount / link_name
        if not try_symlink(src, link_path):
            write_proxy(src, link_path)
        print(f"[OK] {provider} materialized {realized_name}")
    # write linkmap
    linkmap = { e["id"]: f"{view['mount']}/{e['id'].replace('@','_')}.agent.json" for e in view["entries"] }
    (ROOT / ".rtt" / "linkmap.json").write_text(json.dumps({provider: linkmap}, indent=2))
    print(f"[OK] wrote linkmap")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: view_materialize.py views/<provider>.view.json")
        sys.exit(2)
    materialize(ROOT / sys.argv[1])
