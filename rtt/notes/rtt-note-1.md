Here is the complete design for a cross-platform Relay Terminal Tool that auto-scans, identifies, routes, and hot-swaps “symbols” (APIs, hooks, plugins, extensions, stubs, flags, tags, etc.) like a smart distribution panel.

# Relay Terminal Tool (RTT) — Design Spec

## 1) Purpose

Single local “patch panel” that discovers endpoints in a folder, assigns addresses, validates compatibility, then wires routes with instant connect/disconnect and automatic re-connect. Latency-first. Offline-first. Deterministic.

## 2) Core Concepts

* **Symbol**: Any connectable interface surface. Types: `api`, `hook`, `plugin`, `extension`, `stub`, `flag`, `tag`, `queue`, `bus`, `file`, `proc`, `service`.
* **Endpoint**: A concrete symbol instance with capabilities and I/O contracts.
* **Connector**: A driver that knows how to speak a symbol’s protocol and materialize a link.
* **Route**: A mapping from a source endpoint to a target endpoint with a policy.
* **Panel**: The orchestration brain. Scans, indexes, validates, routes, monitors.
* **QuickConnect**: O(1) hot-swap operation with idempotent handshake and rollback.

## 3) Architecture (modules)

```mermaid
flowchart LR
  subgraph FS[Watchers]
    W1[Inotify/FSEvents/Win32\nFile watchers]
  end
  subgraph Scanner
    S1[Heuristic + Manifest scan]
    S2[Language indexers\n(tree-sitter, cargo, go, tsserver, pip/venv)]
  end
  subgraph Registry
    R1[Symbol Catalog]
    R2[Type System & Contracts]
    R3[Compat Matrix & Version Sets]
  end
  subgraph ControlPlane
    C1[Router & Reconciler]
    C2[Policy Engine\n(ACLs, QoS, pinning)]
    C3[Health & Heartbeats\n(circuit breaker)]
    C4[Txn Manager\n(2-phase rewire)]
  end
  subgraph DataPlane
    D1[Link Fabric: UDS/Npipes/SHM/Loopback]
    D2[Connector Drivers]
    D3[Buffers & Backpressure]
  end
  CLI[CLI/TUI]
  API[gRPC/UDS API]

  W1-->S1-->R1
  S2-->R1
  R2-->C1
  R3-->C1
  C1-->D2
  C2-->C1
  C1-->D1
  C3-->C1
  C4-->C1
  CLI-->API-->ControlPlane
  API-->Registry
  API-->DataPlane
```

## 4) Addressing and discovery

**Symbol Address (SADDR):**

```
rtt://<namespace>/<type>/<name>@<semver>#<variant>?caps=a,b&io=req|pubsub|stream
```

**Discovery sources (scored, merged):**

* `rtt.manifest.json` files at any depth.
* Heuristic scanners:

  * Python: `pyproject.toml`, entry points, `ast` for `@hook`, `click` CLIs.
  * Node/TS: `package.json`, `exports`, `tsserver` symbols.
  * Go: `go list -m -json`, `go:generate`, exported funcs.
  * Rust: `cargo metadata`, `#[rtt::hook]` attrs.
  * C/C++: `compile_commands.json`, `dlopen` exports map.
  * Shell/Proc: shebangs, `systemd` units, launchd plists.
  * Data/IPC: `.socket`, `.service`, `.fifo`, `.sock`, `.mq`, `.schema.json`.
* Tags: `.rtttags` sidecars and VCS metadata.

## 5) Contracts and compatibility

**Minimal contract schema (Johnson/JSON):**

```json
{
  "$schema": "https://rtt/spec/v1",
  "symbol": {
    "saddr": "rtt://core/api/metrics@1.2.0#prom",
    "type": "api",
    "direction": "provider|consumer|both",
    "capabilities": ["pull","push","stream"],
    "inputs": [{"name":"query","schema":"jsonschema://..."}],
    "outputs":[{"name":"series","schema":"jsonschema://..."}],
    "qos": {"latency_budget_ms": 2, "throughput_qps": 5000},
    "version_set": ">=1.2 <2.0",
    "auth": {"mode":"none|token|mtls|caps", "scopes":["metrics.read"]}
  }
}
```

**Compat matrix**: semantic-version rules + type coercions + negotiated capability set. Hard fail on contract mismatch unless a declared coercer exists.

## 6) Routing model

* **Decision order**: Policy pin → Hard compat → QoS fit → Locality → Historical health → Randomized tie-break.
* **Link types**:

  * **SHM lane**: POSIX `shm_open` / `memfd` or Windows File Mapping + single-producer single-consumer ring buffer for sub-millisecond paths.
  * **UDS/Npipe**: default control + data for same-host.
  * **Loopback TCP**: cross-user or legacy.
  * **In-proc FFI**: only for pure functions with reentrancy guarantees.
* **Backpressure**: token bucket per route, drop policy: `taildrop|mark|nack|buffer`.
* **Rewire**: 2PC—prepare links, flip atomically, rollback on any NACK.

## 7) QuickConnect handshake (idempotent)

1. `SYN` with `saddr`, `caps`, `contract_hash`, `nonce`.
2. `ACK` with negotiated `caps`, link type, buffer params.
3. `BIND` allocate lane, exchange fds/handles.
4. `READY` heartbeats start.
5. **Failure** → `TRIP` circuit breaker, exponential backoff with jitter, log reason, route fallback.

## 8) Connectors (drivers)

**Driver interface (FFI or gRPC over UDS):**

* `Probe(fs_path) -> [Symbol]`
* `Open(Symbol, params) -> LinkHandle`
* `Tx(LinkHandle, bytes|fd)`
* `Rx(LinkHandle) -> bytes|fd`
* `Close(LinkHandle)`
* `Health(LinkHandle) -> {ok, lag_ms, err?}`

Deliver as language-specific shims:

* Rust: `rtt-connector` crate (WASI-optional).
* Go: module with `plugin` build tag.
* Python: wheel exposing `rtt_connector` entry points.
* Node: NAPI addon.

Drivers run isolated (separate process). Optional seccomp/AppContainer/sandbox on Linux/Windows/Mac.

## 9) Policy engine

* **ACL**: who can wire what. Wildcards on `namespace`, `type`, tags.
* **QoS**: latency budgets, burst caps, priority bands.
* **Pinning**: force concrete endpoints for critical paths.
* **Failover sets**: A→B→C with health thresholds.
* **Degrade modes**: read-replicas, cached stubs, loopback emulation.

Policy format:

```json
{
  "allow": [{"from":"rtt://*/api/*","to":"rtt://*/api/*","scopes":["*"]}],
  "pin": [{"route":"rtt://core/api/auth -> rtt://idp/api/auth@2"}],
  "qos": [{"match":"rtt://*/stream/*","latency_ms":1,"prio":0}],
  "failover": [{"route":"rtt://core/bus/events -> [A,B,C]","health":"p95<5ms,err<0.1%"}]
}
```

## 10) Health, stability, and reconnection

* **Heartbeats** at route frequency with `lag_ms`, queue depth, error flags.
* **Circuit breaker**: `closed -> open -> half-open`. Trip on consecutive failures or SLO violation windows.
* **Auto-reconnect** with jitter, capped backoff, warm spare pre-bind.
* **State journal**: append-only WAL for replays on crash.
* **Stability sweeps**: periodic reconciliation of registry vs actual links.

## 11) Latency strategy

* Prefer SHM lanes for local hot paths; UDS for control.
* Pre-allocate buffers sized from QoS and token bucket rates.
* Batch coalescing with Nagle-off semantics for streams.
* Lock-free ring buffers for SPSC, MPSC via multi-lane striping.

Target budgets:

* Control path: p99 < 300 µs.
* Data path same-host SHM: p99 < 1.5 ms for 64 KiB messages.

## 12) Security model

* **Capability tokens**: least-privilege per route. Scoped to `saddr`, action, duration.
* **Manifests** signed (Ed25519). Reject unknown/unsigned if `strict=true`.
* **Process isolation** for drivers by default.
* **Audit ledger**: every bind/unbind with reason, who, when, before→after snapshot.

## 13) File layout (single folder, offline-friendly)

```
.rtt/
 ├─ panel.yaml              # node config
 ├─ policy.json             # ACL/QoS/pins
 ├─ routes.json             # desired state
 ├─ drivers/                # connector binaries/modules
 ├─ manifests/              # discovered or authored contracts
 ├─ cache/                  # symbol index, compat cache
 ├─ wal/                    # write-ahead logs
 └─ sockets/                # UDS, named pipes map
```

Example `panel.yaml`:

```yaml
api:
  listen: "unix:///abs/path/.rtt/sockets/panel.sock"
scan:
  roots: ["./", "./services", "./packages"]
  ignore: [".git", "node_modules", "target", "venv", "dist"]
routing:
  prefer: ["shm","uds","tcp"]
  rewire_atomic: true
security:
  strict_manifests: true
  allow_unsigned: ["dev/*"]
health:
  heartbeat_ms: 250
  trip_threshold: {errors: 5, window_ms: 5000}
```

## 14) CLI/TUI

```
rtt scan                # index symbols
rtt plan                # show diff of desired vs actual routes
rtt apply               # do 2PC rewire
rtt qc A -> B           # QuickConnect hot-swap
rtt ls symbols|routes   # list
rtt tap route/<id>      # live metrics
rtt trip route/<id>     # open breaker
rtt heal route/<id>     # half-open test
rtt export --sbom       # emit SBOM of connectors + contracts
```

## 15) API (gRPC over UDS)

* `ListSymbols(Filter) -> stream Symbol`
* `PlanRoutes(Desired) -> Plan`
* `ApplyPlan(Plan) -> Result`
* `QuickConnect(RouteSpec) -> Ack`
* `Health(Selector) -> stream HealthSample`
* `Audit(Query) -> stream Event`

Proto message snapshot:

```proto
message Symbol { string saddr=1; string type=2; map<string,string> tags=3; bytes contract_hash=4; }
message RouteSpec { string from=1; string to=2; map<string,string> params=3; }
message HealthSample { string route=1; double p95_ms=2; double err_rate=3; uint64 qdepth=4; }
```

## 16) Reconciler algorithm (deterministic)

1. Build observed graph Gₒ from live links.
2. Build desired graph G_d from `routes.json` + policy.
3. Compute Δ = minimal edge edit set with topological safety checks.
4. Order Δ into non-conflicting batches by dependency and QoS priority.
5. For each batch: 2PC prepare → validate health → commit or rollback.
6. Post-commit verify SLOs; trip and fallback on violation.

## 17) Test matrix

* **Unit**: parsers, compat, token buckets, ring buffers.
* **Property**: idempotent `apply`, no orphan lanes after rollback.
* **Soak**: 24h randomized churn, no fd leak, stable p95.
* **Faults**: kill -9 drivers, corrupt pipes, slow consumer, clock drifts.

## 18) Minimal working manifests

`manifests/metrics.api.json`

```json
{
  "$schema":"https://rtt/spec/v1",
  "symbol":{
    "saddr":"rtt://core/api/metrics@1.0.0",
    "type":"api",
    "direction":"provider",
    "capabilities":["pull","stream"],
    "inputs":[{"name":"query","schema":"json://metrics.query"}],
    "outputs":[{"name":"series","schema":"json://metrics.series"}],
    "qos":{"latency_budget_ms":2,"throughput_qps":5000}
  }
}
```

`routes.json`

```json
{
  "routes":[
    {"from":"rtt://ui/hook/refresh","to":"rtt://core/api/metrics"},
    {"from":"rtt://core/bus/events","to":"rtt://obs/extension/logger#ndjson"}
  ]
}
```

## 19) Performance levers

* SHM page size aligned buffers. Power-of-two ring sizes.
* Busy-poll option for ultra-low latency lanes.
* NUMA pin for paired producers/consumers.
* Adaptive coalescing window ≤ 200 µs.

## 20) Safety and rollback

* Every `apply` writes a WAL frame with pre/post graphs.
* On crash: replay last committed, discard partial.
* Manual `rtt rollback <seq>` restores prior stable topology.

---

# Implementation starter set (concise)

### Rust kernel crates

* `rtt-panel`: control plane, registry, reconciler, policy.
* `rtt-fabric`: SHM/UDS/loopback lanes, ring buffers.
* `rtt-connector-sdk`: driver trait + FFI, health, logging.
* `rtt-cli`: CLI/TUI using UDS API.

Key traits:

```rust
pub trait Connector {
  fn probe(&self, root: &Path) -> anyhow::Result<Vec<Symbol>>;
  fn open(&self, sym: &Symbol, params: &Params) -> anyhow::Result<Link>;
  fn tx(&self, link: Link, buf: &[u8]) -> anyhow::Result<()>;
  fn rx(&self, link: Link) -> anyhow::Result<Vec<u8>>;
  fn close(&self, link: Link) -> anyhow::Result<()>;
  fn health(&self, link: Link) -> Health;
}
```

### SHM SPSC ring (outline)

* Header: `write_idx`, `read_idx`, `mask`, `cycle`.
* Payload: `2^n` slots of length-prefixed frames.
* Atomics with `Acquire/Release`, no locks. Fallback to UDS.

---

# Operational runbook

1. Place `panel.yaml`, `policy.json` in `.rtt/`.
2. Drop connectors into `.rtt/drivers/` (no network required).
3. `rtt scan` → review `rtt plan`.
4. `rtt apply` → atomic wire-up.
5. Use `rtt qc A -> B` for hot swaps.
6. Monitor `rtt tap route/<id>`; set SLO trips in `policy.json`.

---

# Agent/Automation prompt (ready to run)

**Goal**: Build and run RTT locally, offline, with SHM + UDS lanes and QuickConnect.

**Do**:

* Create the repo with crates `rtt-panel`, `rtt-fabric`, `rtt-connector-sdk`, `rtt-cli`.
* Implement: registry, parser for manifests, compat resolver, reconciler with 2PC, circuit breaker, SHM SPSC ring, UDS control channel.
* Provide reference drivers: `connector-file`, `connector-process`, `connector-http` (loopback), each exposing `Probe/Open/Tx/Rx/Close/Health`.
* Expose gRPC over UDS API with methods listed above.
* Ship sample `.rtt/` scaffold and `routes.json` + `policy.json`.
* Write tests for idempotent `apply`, WAL replay, breaker trip/recover, SHM throughput.

**Constraints**:

* Offline. No Docker. Single folder. Cross-platform (Linux/macOS/Windows).
* Latency p99 budgets as above. Idempotent operations. Deterministic plans.
* Sandboxed drivers by process boundary. No globals in kernel.

**Outputs**:

* Buildable code. `rtt` binary. Sample manifests. Test suite passing.
* `README.md` with run steps: `rtt scan && rtt plan && rtt apply`.

---

If you want, I can generate the initial `.rtt/` scaffold, sample manifests, and a minimal `routes.json` so you can drop it into your repo and start coding.
