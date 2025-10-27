#!/usr/bin/env python3
import json, sys, os, glob

def require(obj, keys, where):
    for k in keys:
        if k not in obj:
            raise SystemExit(f"[FAIL] Missing key '{k}' in {where}")

def validate_schema(obj, schema, where):
    # Very small subset validator
    if schema.get("type") == "object":
        if not isinstance(obj, dict):
            raise SystemExit(f"[FAIL] {where} is not an object")
        if "required" in schema:
            require(obj, schema["required"], where)
        props = schema.get("properties", {})
        for k, s in props.items():
            if k in obj:
                validate_schema(obj[k], s, f"{where}.{k}")
    elif schema.get("type") == "array":
        if not isinstance(obj, list):
            raise SystemExit(f"[FAIL] {where} is not an array")
        item_schema = schema.get("items")
        if item_schema:
            for i, itm in enumerate(obj):
                validate_schema(itm, item_schema, f"{where}[{i}]")
    elif schema.get("type") == "string":
        if not isinstance(obj, str):
            raise SystemExit(f"[FAIL] {where} is not a string")
    # enums check
    if "enum" in schema and obj not in schema["enum"]:
        raise SystemExit(f"[FAIL] {where} value '{obj}' not in enum {schema['enum']}")

def load(p): 
    with open(p,"r",encoding="utf-8") as f: 
        txt=f.read()
        try:
            return json.loads(txt)
        except Exception as e:
            raise SystemExit(f"[FAIL] {p} invalid JSON: {e}")

def main(root):
    sch_sym = load(os.path.join(root, "schemas", "rtt.symbol.schema.json"))
    sch_pol = load(os.path.join(root, "schemas", "rtt.policy.schema.json"))
    sch_rts = load(os.path.join(root, "schemas", "rtt.routes.schema.json"))
    ok = True
    for p in glob.glob(os.path.join(root, ".rtt", "manifests", "*.json")):
        obj = load(p)
        try:
            validate_schema(obj, sch_sym, p)
            print(f"[OK] {p}")
        except SystemExit as e:
            print(str(e)); ok=False
    p = os.path.join(root, ".rtt", "policy.json")
    try:
        validate_schema(load(p), sch_pol, p); print(f"[OK] {p}")
    except SystemExit as e:
        print(str(e)); ok=False
    p = os.path.join(root, ".rtt", "routes.json")
    try:
        validate_schema(load(p), sch_rts, p); print(f"[OK] {p}")
    except SystemExit as e:
        print(str(e)); ok=False
    if not ok: 
        sys.exit(1)

if __name__ == "__main__":
    main(os.path.dirname(os.path.abspath(__file__)))
