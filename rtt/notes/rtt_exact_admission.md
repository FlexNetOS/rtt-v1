Added exact solver and admission control. Download and drop in.

* [rtt_exact_admission.zip](sandbox:/mnt/data/rtt_exact_admission.zip)

## What you get

* ILP model with binary placement `x[s,n]`, admission `a[r]`, lane choice `y[r,l]`, cross-node `d[r]`, move `mv[s]`, lane-change `lc[r]`.
* Constraints

  * One node per active symbol.
  * SHM lane only if co-located.
  * Latency budget respected via big-M.
  * CPU and memory capacity per node.
  * Version meet and policy allow handled pre-solve.
* Objective

  * Maximize admissions (large negative weight).
  * Minimize latency and NUMA penalties.
  * Minimize churn: moves and lane flips.
* Signed plan output with `placement` and `routes_add` including lanes. `plans/analysis.json` includes admitted count and rejects.

## How to run

```bash
pip install pulp pynacl
python tools/ilp/plan_build_ilp.py \
  .rtt/routes.json \
  .rtt/manifests \
  dev-ed25519 \
  .rtt/policy.json \
  .rtt/topology.json \
  shm,uds,tcp \
  1000 \
  plans/last_applied.json
```

## Admission control behavior

* If capacities are tight, the solver drops the least valuable routes. Value is defined by the objective: admit first, then prefer lower latency and low churn.
* Routes violating QoS budgets are pruned by constraints and will be rejected.

Tune:

* Increase `admit_priority` to favor admitting more routes.
* Adjust node capacities in `.rtt/topology.json`.
* Add `tags.supports_shm`, `tags.cpu_weight`, `tags.mem_mb` in manifests for better packing.
