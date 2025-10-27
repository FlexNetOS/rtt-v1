# Exact solver + admission control

ILP-based placement, lane choice, and admission selection. Requires PuLP.

## Install
```bash
pip install pulp pynacl
# or install a system CBC solver for better performance
```

## Inputs
- `.rtt/routes.json` desired routes.
- `.rtt/manifests/` symbols with qos, version sets, tags.
- `.rtt/policy.json` wildcard allow rules.
- `.rtt/topology.json` nodes, capacities, optional hints.
- `plans/last_applied.json` optional prior plan for churn.

## Run
```bash
python tools/ilp/plan_build_ilp.py       .rtt/routes.json       .rtt/manifests       dev-ed25519       .rtt/policy.json       .rtt/topology.json       shm,uds,tcp       1000       plans/last_applied.json
```

- The model maximizes admissions, then minimizes latency + churn via weighted objective.
- QoS budgets prune infeasible lanes using big-M constraints.
- SHM lanes enforced only if endpoints co-locate on the same node.
- Capacity constraints for CPU and MEM enforce admission control.

## Outputs
- `plans/<plan_id>.json` signed plan with `routes_add` (lanes) and `placement`.
- `plans/latest.json` copy of the last build.
- `plans/analysis.json` summary with admitted count and rejects list.

## Notes
- Increase `admit_priority` to force more admissions.
- Add `tags.supports_shm: true`, `tags.cpu_weight`, and `tags.mem_mb` in manifests for better results.
- For large graphs consider OR-Tools CP-SAT or Z3.
