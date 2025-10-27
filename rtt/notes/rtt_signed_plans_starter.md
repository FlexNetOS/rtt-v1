Download. Drop in and run.

* [rtt_signed_plans_starter.zip](sandbox:/mnt/data/rtt_signed_plans_starter.zip)

## What you got

* Signing helpers

  * `tools/ed25519_helper.py` tries PyNaCl. Falls back to `rtt-sign` if present.
  * `tools/keys_ed25519.py` generates keys and updates trust.

* View plan signing

  * `tools/sign_view.py` signs `views/*.view.json`.
  * `tools/verify_view.py` verifies signature and key.

* Auto plan builder

  * `tools/plan_build.py` reads `.rtt/routes.json` and `.rtt/manifests`, creates a deterministic plan, assigns `plan_id = sha256(unsigned_plan)`, signs it, writes `plans/<plan_id>.json` and `plans/latest.json`.
  * `tools/plan_verify.py` validates `plan_id` and signature.

## How to use

```bash
# 1) Generate a key (uses PyNaCl if installed; else use your rtt-sign CLI)
python tools/keys_ed25519.py dev-ed25519

# 2) Sign and verify a provider view
python tools/sign_view.py views/claude.view.json dev-ed25519
python tools/verify_view.py views/claude.view.json

# 3) Build and sign a route plan from your existing drop-ins
python tools/plan_build.py .rtt/routes.json .rtt/manifests dev-ed25519
python tools/plan_verify.py plans/latest.json
```

## Wiring to your flow

* Feed `plans/latest.json` to your RTT panel’s `Apply(PlanHash)` path.
* Refuse to apply any plan missing `sign`.
* Store public keys under `.rtt/registry/trust/keys/*.pub`.
* Keep private keys only under `.rtt/registry/keys/private/*.priv`.

If you want me to extend the builder to ingest MCP tool lists, or to gate plan generation on a quick invariant check, say “gate plan with invariants” and I’ll add it.
