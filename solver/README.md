# Solver constraints add-on

Adds to the planner:
- Semver version meet between endpoints.
- QoS latency budget check using lane base costs.
- Policy ACL allow-list matching.
- NUMA-aware placement penalty from `.rtt/topology.json`.
- Lane selection by preference and endpoint support.
- Objective: minimize predicted latency, then stable keys.

## Inputs
- `.rtt/routes.json` — desired from/to pairs.
- `.rtt/manifests/` — symbols with `saddr`, `version_set`, `qos`, and optional `tags.supports_shm`.
- `.rtt/policy.json` — allow rules with wildcards.
- `.rtt/topology.json` — optional node map and `place` dict of saddr → node.

## Run
```bash
python tools/plan_build.py .rtt/routes.json .rtt/manifests dev-ed25519 .rtt/policy.json .rtt/topology.json shm,uds,tcp
```

If any route violates constraints the builder exits with a JSON report and no plan.

## Notes
- Set `tags.supports_shm: true` in both endpoints to prefer SHM lanes.
- Latency model is a simple base per lane plus +0.4 ms for cross-node. Replace with measured values in Autotune.
- Extend semver expressions like `>=1.2 <2.0` in manifests.
