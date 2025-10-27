# Signed Views and Plans — Starter

Adds:
- Ed25519 key generation and helpers.
- View plan signing and verification.
- Deterministic plan builder from `.rtt/routes.json` with signing.
- Plan verification.

## Generate keys
```bash
python tools/keys_ed25519.py dev-ed25519
# writes:
#  .rtt/registry/keys/private/dev-ed25519.priv  (keep secret)
#  .rtt/registry/trust/keys/dev-ed25519.pub     (commit)
```

## Sign a view plan
```bash
python tools/sign_view.py views/claude.view.json dev-ed25519
python tools/verify_view.py views/claude.view.json
```

## Build and sign a route plan
```bash
python tools/plan_build.py .rtt/routes.json .rtt/manifests dev-ed25519
python tools/plan_verify.py plans/latest.json
```

Notes:
- Uses PyNaCl if available; otherwise looks for `rtt-sign` in PATH.
- Signatures cover the canonical JSON excluding the `sign` field.
- `plan_id` is `sha256` of the canonical unsigned plan.
