Added solver constraints. Download and drop in.

* [rtt_solver_constraints.zip](sandbox:/mnt/data/rtt_solver_constraints.zip)

## What changed

* Semver meet. Both ends must satisfy each other’s `version_set`.
* QoS check. Predicted lane latency must fit both latency budgets.
* Policy ACL. Wildcard allow rules enforced.
* NUMA-aware placement. Cross-node adds a penalty.
* Lane selection. Honors preference `shm,uds,tcp` and endpoint support (`tags.supports_shm`).
* Objective. Sort by predicted latency, then stable keys.

## How to run

```bash
python tools/plan_build.py \
  .rtt/routes.json \
  .rtt/manifests \
  dev-ed25519 \
  .rtt/policy.json \
  .rtt/topology.json \
  shm,uds,tcp
```

If a constraint fails, the tool exits non-zero and prints a JSON list of rejected routes.

## Where to edit

* `.rtt/topology.json` for node placement.
* `.rtt/policy.json` for allow rules.
* Manifests: add `tags.supports_shm: true` to enable SHM lanes. Ensure `version_set` and `qos` are accurate.

## “Gate plan generation on a quick invariant check”

Function: refuse to produce or sign a plan when cheap safety rules fail. It protects the fabric from bad graphs.

* Existence: every `from` and `to` present in manifests.
* No duplicates. No self-loops.
* Fast prefilters run before constraint solving and signing.

Want NUMA pinning suggestions, throughput admission, or churn minimization against the last applied plan next? Say “add placement and churn optimizer.”
