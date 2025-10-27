#!/usr/bin/env python3
import os, sys, json, yaml, errno
from pathlib import Path

# minimal yaml loader without external deps
def _parse_yaml(text):
    # Very naive YAML subset parser for this file shape
    import re
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    d, cur = {}, None
    for ln in lines:
        if ln.startswith('providers:'):
            d['providers'] = {}
        elif ln.startswith('  ') and ':' in ln and not ln.strip().startswith('-'):
            k, v = ln.strip().split(':', 1)
            if not v.strip():
                cur = k.strip()
                d['providers'][cur] = {}
            else:
                if cur is None:
                    # key under providers
                    pass
                else:
                    d['providers'][cur][k.strip()] = v.strip().strip('"')
        else:
            if 'agent_target:' in ln:
                pass
    return d

ROOT = Path(__file__).resolve().parents[1]
providers_file = ROOT / "providers" / "providers.yaml"
agents_index_file = ROOT / "agents" / "agents.index.json"

providers = _parse_yaml(providers_file.read_text())
index = json.loads(agents_index_file.read_text())

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def try_symlink(src: Path, dst: Path):
    try:
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        os.symlink(src, dst)
        return True
    except Exception:
        return False

def write_proxy(src: Path, dst: Path):
    # simple JSON proxy that points back to canonical file
    obj = {"$schema":"https://rtt/agent-proxy/v1","ref":os.path.relpath(src, dst.parent)}
    dst.write_text(json.dumps(obj, indent=2))

def main():
    for name, cfg in providers.get('providers', {}).items():
        target = ROOT / cfg['agent_target']
        ensure_dir(target)
        for a in index['agents']:
            src = ROOT / a['path']
            dst = target / (Path(a['path']).name)
            if not try_symlink(src, dst):
                write_proxy(src, dst)
        print(f"[OK] projected {name} -> {target}")
    # write linkmap
    linkmap = {}
    for name, cfg in providers.get('providers', {}).items():
        target = cfg['agent_target']
        linkmap[name] = { a['id']: f"{target}/{Path(a['path']).name}" for a in index['agents'] }
    (ROOT / ".rtt" / "linkmap.json").write_text(json.dumps(linkmap, indent=2))
    print(f"[OK] wrote .rtt/linkmap.json")

if __name__ == "__main__":
    main()
