Added placement and churn optimizer. Download and drop in.

* [rtt_placement_churn.zip](sandbox:/mnt/data/rtt_placement_churn.zip)

## What changed

* Placement solver. Assigns each symbol to a NUMA node with simple capacity packing and local search.
* Lane choice tied to placement. Uses SHM only on same node, else UDS/TCP by preference.
* Churn minimization. Penalizes moves and lane flips. Preserves prior state unless improvement beats a threshold.
* Plan now includes `placement{ saddr → node }`.
* Emits `plans/analysis.json` with total cost, moved count, and route changes.

## How to run

```bash
python tools/plan_build.py \
  .rtt/routes.json \
  .rtt/manifests \
  dev-ed25519 \
  .rtt/policy.json \
  .rtt/topology.json \
  shm,uds,tcp \
  --churn-weight=0.8 \
  --change-threshold-ms=0.15
```

## Inputs to tune

* `.rtt/topology.json`: set `nodes[*].capacity.cpu` and `mem_mb`. Add `place` hints.
* Manifests: set `tags.supports_shm`, `tags.cpu_weight`, `tags.mem_mb`.
* `plans/last_applied.json`: persisted after apply. The optimizer reads it to minimize churn.

## Optimizer mechanics

* Seed placement from `last_applied` or `.rtt/topology.place`, else round-robin.
* Repack if a node exceeds capacity. Move the heaviest symbol to the lightest node.
* Choose lanes: prefer `shm` when co-located and supported. Else `uds`, then `tcp`.
* Keep previous lanes if still feasible and benefit < `--change-threshold-ms`.
* Local search: try moving one symbol at a time. Accept only cost-reducing moves.
* Cost = predicted latency (lane base + cross-node penalty) + `churn_weight × moves`.

If you want ILP/SMT exact placement, admission control for throughput, or breaker-aware reroutes next, say “add exact solver and admission control.”
