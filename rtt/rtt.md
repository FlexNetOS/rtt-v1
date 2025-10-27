# RTT Elite Upgrade — Gap Map and Plan

## Summary

Target: top 0.001% version. Add formal spec, zero-copy hot path, constraint solver planner, ruthless observability, deterministic apply, strong security, NUMA-aware placement, schedulers with budgets, typed config, autotuning, chaos, safe upgrades.

## What you already have (from `rtt_dropin.zip`)

* `.rtt/panel.yaml` — base config.
* `.rtt/policy.json` — ACL, QoS, pins, failover.
* `.rtt/routes.json` — desired routes.
* `.rtt/manifests/*.json` — sample symbols.
* `.rtt/drivers/` — placeholder with README.
* `.rtt/cache/`, `.rtt/wal/`, `.rtt/sockets/` — runtime dirs.
* `schemas/*.json` — minimal JSON sanity schemas.
* `tests/validate.py` — offline validator.
* `README.md` — quick start.

## What is missing for the “secret-elite” build

| Area                  |                 Exists | Add                                                                                                                    |
| --------------------- | ---------------------: | ---------------------------------------------------------------------------------------------------------------------- |
| Formal spec           |                     No | `spec/tla/` TLA+ for scan→plan→2PC→verify→rollback. Invariants encoded.                                                |
| Constraint planner    |                     No | `planner/` with typed constraints, solver, and signed plans in `plans/`.                                               |
| Deterministic apply   | Partial (WAL dir only) | Reconciler that computes stable Δ order, 2PC batches, merkle-chained WAL.                                              |
| Zero-copy fabric      |                     No | `fabric/shm/` SPSC ring buffers, power-of-two slots, length-prefix frames, busy-poll option.                           |
| Observability         |                     No | `telemetry/flight_recorder/` zero-alloc histograms, per-route p50/p95/p99, breaker states, single “dump window”.       |
| NUMA placement        |                     No | `placement/numa/` topology probe, thread pinning, page placement.                                                      |
| Schedulers            |                     No | Admission control per route, token buckets, EDF/CBS for periodic, WFQ for mixed.                                       |
| Security              |      Basic policy only | Capability tokens per route, strict signed manifests, plan signatures, driver sandbox (seccomp/AppContainer).          |
| Config type safety    |         JSON/YAML only | `cue/` schemas for panel, routes, policy; boot validation.                                                             |
| Autotune              |                     No | `autotune/` trace runner, sweep ring sizes, batch windows, CPU pins; write `tuned/profile.json`.                       |
| Chaos + failure tests |                     No | `chaos/` kill, slow, corrupt, clock-drift hooks wired into CI.                                                         |
| Upgrade strategy      |                     No | Staged plans (canary), SLO gates, inverse diffs for rollback.                                                          |
| Data formats          |             Basic JSON | Control plane via Cap’n Proto or FlatBuffers over UDS/Npipe; framed data header `{route_id, frame_id, len, checksum}`. |
| Supply chain          |                   None | Repro builds, SBOM embed, artifact signing, offline toolchain lock.                                                    |
| Dev workflow          |                Minimal | CI gates: spec check, property tests, chaos pack, perf guardrails, fd-leak, deadlock scan.                             |

## Add this structure

```
plans/                            # signed, content-addressed plans
spec/tla/                         # formal model + invariants
planner/                          # constraint solver + plan generator
fabric/shm/                       # zero-copy SPSC rings
fabric/uds/                       # control channel
placement/numa/
schedulers/
telemetry/flight_recorder/
security/                         # caps, signing, sandbox profiles
cue/                              # typed configs
autotune/
chaos/
ci/                               
```

## Minimal files to drop in

### 1) Plan file (signed)

`plans/0001.bootstrap.plan.json`

```json
{
  "plan_id": "sha256-<hex>",
  "created_at": "2025-10-24T00:00:00Z",
  "routes_add": [
    {"from":"rtt://ui/hook/refresh","to":"rtt://core/api/metrics","lane":"shm"}
  ],
  "routes_del": [],
  "order": ["A1"], 
  "sign": {"alg":"ed25519","key_id":"dev-key-1","sig":"<base64>"}
}
```

### 2) CUE types for config

`cue/panel.cue`

```cue
api: listen: {
  unix: =~"^\\./\\.rtt/sockets/.*\\.sock$"
  npipe?: string
}
scan: {
  roots: [...string]
  ignore: [...string]
}
routing: {
  prefer: [...string] & ["shm","uds","tcp"]
  rewire_atomic: true
}
security: {
  strict_manifests: bool
  allow_unsigned?: [...string]
}
health: {
  heartbeat_ms: >=100 & <=5000
  trip_threshold: { errors: >=1, window_ms: >=1000 }
}
```

### 3) Invariants checklist (enforced at runtime)

`spec/invariants.md`

* No duplicate active link for `(from, class!=bus)`.
* After `apply`: ObservedGraph == DesiredGraph. Else rollback.
* p99 latency per route < `latency_budget_ms` over 10s window or breaker trips.
* WAL sequence strictly increases. Merkle chain valid.
* Version meet non-empty on every bind.

### 4) SHM frame header

`fabric/shm/FRAME.md`

```
u32 magic = 0xRTT1
u16 flags
u16 reserved
u32 route_id
u32 frame_id
u32 len
u32 crc32c
payload[len]
```

### 5) Capability token shape

`security/caps.schema.json`

```json
{
  "saddr":"rtt://core/api/metrics",
  "verb":"open|tx|rx|close",
  "scopes":["metrics.read"],
  "exp":"2025-10-24T00:05:00Z",
  "nonce":"<32b>"
}
```

### 6) Deterministic apply order

`planner/order.md`

* Topo sort by dependencies.
* Secondary key: `(from,type,to,version)` stable string.
* Batch non-conflicting edges.
* 2PC per batch. Any NACK → rollback.

### 7) Flight recorder usage

`telemetry/flight_recorder/README.md`

```
rtt tap --flight 5s > flight.ndjson
# contains: ts, route_id, p50, p95, p99, qdepth, drops, breaker_state, syscalls_delta
```

### 8) Chaos hooks

`chaos/cases.yaml`

```yaml
- name: kill_driver
  action: SIGKILL
  target: connector:http
  window: {start_ms: 500, dur_ms: 1000}
- name: slow_consumer
  action: sleep
  target: route:rtt://core/bus/events->logger
  latency_ms: 50
```

## Planner: constraint set (what to solve)

* Type match: `type(from) ⟂ type(to)` valid pair.
* Version set meet: `from.version ∧ to.version ≠ ∅`.
* Capabilities meet: negotiated subset non-empty.
* QoS: predicted p99 ≤ budget, tokens sized.
* Locality: minimize cross-NUMA hops.
* Policy: ACL, pins, fan-out rules.
* Objective 1: minimize latency. Objective 2: minimize churn vs current graph.

Small graphs: SMT/ILP. Large graphs: greedy with cached fingerprints.

## Fabric: zero-copy ring rules

* Power-of-two slots. Length-prefix frames.
* SPSC only on hot path. MPSC via striping.
* Atomics: Acquire/Release only. No locks.
* Optional busy-poll. Default sleep-poll budget.
* Setup time only passes handles (`SCM_RIGHTS` or `DuplicateHandle`). Never on hot path.

## Schedulers

* Token bucket per route. Size from `throughput_qps` and `latency_budget_ms`.
* EDF/CBS for periodic streams.
* WFQ for mixed workloads.
* Backpressure policy is explicit: `taildrop|mark|nack|buffer`.

## Security defaults

* `strict_manifests: true`.
* Refuse unsigned manifests unless under `allow_unsigned`.
* Plans must be signed. Panel binds only to a signed plan file.
* Drivers out-of-process with minimal profiles. No network by default.

## Autotune

* Record trace. Sweep: ring size, batch window, pinning, busy-poll threshold.
* Hill-climb on current hardware. Persist to `.rtt/tuned/profile.json` keyed by CPU+NUMA fingerprint.

## Upgrade path

* `rtt plan` generates a signed plan.
* `rtt apply --canary <percent>` wires subset.
* Verify SLO for window. Promote or rollback automatically.

## CI guardrails

* Spec pass (TLA+ TLC check).
* Property tests: idempotent apply, no orphan lanes, no fd leaks.
* Chaos pack.
* Perf gates: p99 regressions < 2%.
* SBOM + signature verification.

## Quick adoption steps

1. Add `cue/` and validate configs at boot. Refuse to serve on mismatch.
2. Add `plans/` and make `rtt apply` require a signed plan.
3. Implement SHM SPSC ring for hot routes. Keep UDS for control.
4. Add flight recorder and `rtt tap --flight`.
5. Add minimal capability tokens and strict manifests.
6. Introduce chaos hooks in tests.
7. Add NUMA pinning and token-bucket admission control.
8. Add autotune and persist tuned knobs.

## Acceptance criteria

* Deterministic plans. Same inputs → same plan hash.
* 2PC apply with rollback on any NACK.
* p99 latency within budgets for 10s windows or breaker trips.
* No fd/thread leaks under 24h churn.
* Reboot recovery from WAL to last committed graph.
* All manifests and plans verified and signed in strict mode.

---

Use this as the single source of truth to evolve the scaffold into the elite build.
