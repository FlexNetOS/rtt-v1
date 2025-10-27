# Placement + Churn Optimizer

Adds:
- Per-symbol placement across NUMA nodes with capacity checks.
- Lane choice linked to placement (SHM only when same node).
- Churn penalty to preserve prior placement and lanes unless gain exceeds threshold.
- Writes `placement` into the signed plan. Emits `plans/analysis.json` with cost and change counts.

## Run
```bash
python tools/plan_build.py       .rtt/routes.json       .rtt/manifests       dev-ed25519       .rtt/policy.json       .rtt/topology.json       shm,uds,tcp       --churn-weight=0.8       --change-threshold-ms=0.15
```

Inputs:
- `.rtt/topology.json`: nodes, optional capacities, and optional `place` hints.
- `plans/last_applied.json`: previous placement and lanes for churn minimization.

Notes:
- Provide `tags.supports_shm: true` in manifests to enable SHM lanes.
- Provide resource hints: `tags.cpu_weight` and `tags.mem_mb` per symbol to improve packing.
- The optimizer is greedy with local search. Replace with ILP or SMT for larger graphs if needed.
