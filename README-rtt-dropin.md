# RTT Drop‑in Scaffold

Place this folder at the repo root. The `.rtt` directory gives you a working config, example policies, and sample manifests.

## Quick start
1. Review `.rtt/panel.yaml`, `.rtt/policy.json`, `.rtt/routes.json`.
2. Put connector binaries or modules in `.rtt/drivers/`.
3. Run your `rtt` binary: `rtt scan && rtt plan && rtt apply`.

## Contents
- `.rtt/panel.yaml` — control plane config.
- `.rtt/policy.json` — ACL, pinning, QoS, failover.
- `.rtt/routes.json` — desired routes.
- `.rtt/manifests/*.json` — example symbols.
- `schemas/*.json` — minimal offline schemas for sanity checks.
- `tests/validate.py` — simple validator with no external deps.

## Notes
- Paths are relative. Unix uses a UDS at `./.rtt/sockets/panel.sock`. Windows uses `\\.\pipe\rtt-panel`.
- Keep `strict_manifests: true` for production; use `allow_unsigned` for development namespaces.
