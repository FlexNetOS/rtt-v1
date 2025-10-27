#!/usr/bin/env python3
import json, sys, copy, os
def deep_merge(base, patch):
    if isinstance(base, dict) and isinstance(patch, dict):
        out = dict(base)
        for k,v in patch.items():
            if k in out:
                out[k] = deep_merge(out[k], v)
            else:
                out[k] = v
        return out
    return patch
def main():
    base = json.loads(open(sys.argv[1]).read())
    for p in sys.argv[2:]:
        if os.path.isfile(p):
            patch = json.loads(open(p).read())
            base = deep_merge(base, patch)
    print(json.dumps(base, indent=2))
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: apply_overlay.py <base.json> [patch1.json ...]")
        sys.exit(2)
    main()
