# RTT System Architecture

**Purpose:** Comprehensive system architecture overview
**Last Updated:** 2025-10-27

---

## One-Line Intent

> Local, deterministic connection fabric that discovers symbols, solves routes, wires lanes, and hot-swaps endpoints across multi-agent, multi-provider stacks without duplication.

---

## Core Principles

1. **Content-Addressed Storage** - Every agent stored once by hash, referenced many times
2. **Deterministic Routing** - Same inputs → same plan hash
3. **Signed Plans Only** - No ad-hoc changes, all transitions signed and auditable
4. **Zero Duplication** - Virtual views eliminate per-provider copies
5. **Hot-Swappable** - 2PC atomic apply with rollback
6. **Offline-First** - No cloud dependency, fully local operation

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RTT Production System                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ LAYER 1: Storage & Registry                                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌───────────────────┐         ┌──────────────────┐            │
│   │   Agents CAS      │────────▶│   View Engine    │            │
│   │  (SHA256 Hash)    │         │  (Overlays +     │            │
│   │  + Packfile       │         │   VFS Mount)     │            │
│   └───────────────────┘         └──────────────────┘            │
│           │                               │                      │
│           │ SHA256                        │ Materialize          │
│           ▼                               ▼                      │
│   ┌───────────────────┐         ┌──────────────────┐            │
│   │  Trust & Keys     │         │ Provider Views   │            │
│   │  (Ed25519)        │         │ (claude, openai) │            │
│   └───────────────────┘         └──────────────────┘            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ LAYER 2: Planning & Control                                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌─────────────────────────────────────────────────┐            │
│   │        RTT Constraint Planner                   │            │
│   ├─────────────────────────────────────────────────┤            │
│   │  • Constraint Solver (QoS + NUMA)              │            │
│   │  • Placement Optimizer (Churn Minimization)    │            │
│   │  • Admission Control (ILP)                     │            │
│   │  • Signed Plan Generation                      │            │
│   └─────────────────────────────────────────────────┘            │
│                         │                                         │
│                         │ Signed Plan                             │
│                         ▼                                         │
│   ┌─────────────────────────────────────────────────┐            │
│   │          2PC Reconciler + Merkle WAL            │            │
│   ├─────────────────────────────────────────────────┤            │
│   │  • 2-Phase Commit                              │            │
│   │  • Atomic Apply                                │            │
│   │  • Rollback on NACK                            │            │
│   │  • WAL Persistence                             │            │
│   └─────────────────────────────────────────────────┘            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ LAYER 3: Data Plane (Fabric)                                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │              RTT Fabric (Lanes)                          │   │
│   ├──────────────────────────────────────────────────────────┤   │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
│   │  │ SHM SPSC   │  │ UDS/Npipe  │  │ TCP        │        │   │
│   │  │ (Hot Path) │  │ (Control)  │  │ (Fallback) │        │   │
│   │  └────────────┘  └────────────┘  └────────────┘        │   │
│   └──────────────────────────────────────────────────────────┘   │
│                         │                                         │
│                         │ Routes                                  │
│                         ▼                                         │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │              Connectors & Drivers                        │   │
│   ├──────────────────────────────────────────────────────────┤   │
│   │  • MCP Tools                                             │   │
│   │  • Services                                              │   │
│   │  • Plugins                                               │   │
│   │  • 25+ Language Stubs                                    │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ LAYER 4: Observability & Optimization                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  Telemetry (Flight Recorder + Metrics + Breakers)       │   │
│   ├──────────────────────────────────────────────────────────┤   │
│   │  • Per-route p50/p95/p99                                │   │
│   │  • Queue depth tracking                                 │   │
│   │  • Circuit breaker states                               │   │
│   │  • SLO gates                                            │   │
│   └──────────────────────────────────────────────────────────┘   │
│                         │                                         │
│                         │ Traces                                  │
│                         ▼                                         │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │      Autotune Engine (Trace Replay + Sweeps)            │   │
│   ├──────────────────────────────────────────────────────────┤   │
│   │  • Ring size optimization                               │   │
│   │  • Batch window tuning                                  │   │
│   │  • CPU pinning suggestions                              │   │
│   │  • Machine-specific profiles                            │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: End-to-End

```
1. DISCOVERY
   ┌──────────────┐
   │ Scan Folders │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │Index Symbols │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  CAS Ingest  │
   └──────────────┘

2. PLANNING
   ┌──────────────┐
   │Routes + Policy│
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │Constraint    │
   │  Solver      │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Signed Plan  │
   └──────────────┘

3. APPLY
   ┌──────────────┐
   │  Plan Hash   │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │2PC Reconciler│
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ WAL + Fabric │
   │    Update    │
   └──────────────┘

4. EXECUTION
   ┌──────────────┐
   │ Symbol Call  │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Lane Routing │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   Driver     │
   │  Execution   │
   └──────────────┘

5. OBSERVATION
   ┌──────────────┐
   │Flight Record │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   Metrics    │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  SLO Gates   │
   └──────────────┘

6. OPTIMIZATION
   ┌──────────────┐
   │    Traces    │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   Autotune   │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │Tuned Profiles│
   └──────────────┘
```

---

## Component Details

### CAS Registry (Content-Addressed Storage)

**Purpose:** Single source of truth for all agents
**Location:** `.rtt/registry/cas/`

```
.rtt/registry/
├── cas/sha256/<hash>.json    # Immutable agent definitions
├── pack/agents.pack          # Memory-mapped packfile
├── pack/index.lut            # SHA256 → {offset, len}
├── trust/keys/*.pub          # Trusted signers
└── index.json                # ID@version → SHA256
```

**Key Operations:**
- `cas_ingest.py` - Source → CAS with SHA256 hash
- `cas_pack.py` - CAS → Packfile for zero-copy reads
- Signatures verify authenticity

---

### View Engine

**Purpose:** Materialize provider views without duplication
**Location:** `tools/view_*.py`, `viewfs/`

**How it Works:**
```
Base Agent (CAS)
      │
      ├──▶ Provider Overlay (e.g., Claude-specific)
      │
      └──▶ Environment Overlay (e.g., prod settings)
            │
            ▼
     Merged View (deterministic)
            │
            ▼
     VFS Mount (FUSE/WinFsp) OR Materialized Files
```

**Example:**
```
agents/common/summarize.agent.json (base)
  + overlays/provider/claude/summarize.patch.json
  + overlays/env/prod/_global.patch.json
  = providers/claude/.claude/agents/summarize.agent.json
```

---

### Constraint Planner

**Purpose:** Generate deterministic, signed routing plans
**Location:** `planner/`, `tools/plan_build.py`

**Inputs:**
- `.rtt/routes.json` - Desired routes
- `.rtt/manifests/` - Symbol contracts
- `.rtt/policy.json` - ACL, QoS, pins
- `.rtt/topology.json` - NUMA nodes

**Constraints Checked:**
1. **Type Compatibility** - `from` and `to` types match
2. **Version Meet** - Semver ranges overlap
3. **QoS Budgets** - Latency ≤ budget
4. **Policy ACL** - Route allowed
5. **Capacity** - Node CPU/memory not exceeded
6. **Placement** - NUMA-aware, minimize cross-node

**Output:**
```json
{
  "plan_id": "sha256:<hash>",
  "routes_add": [
    {"from": "rtt://ui/hook/refresh", "to": "rtt://core/api/metrics", "lane": "shm"}
  ],
  "placement": {
    "rtt://ui/hook/refresh": "node0",
    "rtt://core/api/metrics": "node0"
  },
  "sign": {"alg": "ed25519", "key_id": "...", "sig": "..."}
}
```

---

### 2PC Reconciler

**Purpose:** Atomic apply with rollback
**Location:** `auto/50-apply_plan.py`

**Algorithm:**
```
1. PREPARE Phase
   - Read plan
   - Validate signature
   - Check pre-conditions
   - Lock resources

2. COMMIT Phase
   - Apply changes atomically
   - Write WAL entry
   - Update fabric

3. VERIFY Phase
   - Check post-conditions
   - Verify SLOs
   - If fail → ROLLBACK

4. ROLLBACK (if needed)
   - Restore from WAL
   - Revert changes
   - Log failure reason
```

---

### Fabric (Lanes)

**Purpose:** Low-latency data transport
**Location:** `fabric/shm/`, `fabric/uds/`, `fabric/tcp/`

**Lane Types:**

| Lane | Use Case | Latency Target | Mechanism |
|------|----------|----------------|-----------|
| **SHM** | Hot paths (co-located) | p99 < 1.5 ms | SPSC ring buffer, memfd |
| **UDS** | Control plane (same host) | p99 < 300 µs | Unix domain sockets |
| **TCP** | Fallback (cross-host/legacy) | p99 < 10 ms | TCP loopback |

**SHM Frame Format:**
```
┌────────┬───────┬─────────┬──────────┬──────────┬─────┬────────┐
│ magic  │ flags │reserved │ route_id │ frame_id │ len │ crc32c │
│ 0xRTT1 │  u16  │   u16   │   u32    │   u32    │ u32 │  u32   │
└────────┴───────┴─────────┴──────────┴──────────┴─────┴────────┘
                            + payload[len]
```

---

### MCP Integration

**Purpose:** Bridge MCP servers to RTT fabric
**Location:** `connector-mcp/`, `tools/mcp_ingest.py`

**Flow:**
```
MCP Server
    │
    │ tools.json
    ▼
mcp_ingest.py
    │
    ├──▶ CAS Entry (SHA256)
    │
    └──▶ RTT Manifest (.rtt/manifests/mcp.*.json)
          │
          ▼
       Planner (routes MCP tools via RTT lanes)
          │
          ▼
       RTT Fabric → MCP Tool Execution
```

---

### Telemetry & Observability

**Purpose:** Ruthless observability for SLO enforcement
**Location:** `telemetry/flight_recorder/`

**Metrics Collected:**
- **Per-route latency:** p50, p95, p99
- **Queue depth:** Current pending requests
- **Drop reason:** Why requests were rejected
- **Breaker state:** open/closed/half-open
- **Syscall counts:** Via eBPF/ETW (future)

**Flight Recorder Usage:**
```bash
rtt tap --flight 5s > flight.ndjson
# Captures 5-second window of all route metrics
```

---

### Autotune Engine

**Purpose:** Machine-specific performance optimization
**Location:** `autotune/`

**Process:**
```
1. Collect Traces
   └─ Real traffic or synthetic replay

2. Sweep Parameters
   ├─ Ring sizes (512, 1024, 2048, 4096)
   ├─ Batch windows (50µs, 100µs, 200µs)
   ├─ CPU pinning (NUMA-aware)
   └─ Busy-poll thresholds

3. Hill-Climb
   └─ Find optimal settings for this machine

4. Persist Profile
   └─ .rtt/tuned/profile.json
      (keyed by CPU model + NUMA topology)
```

---

## Security Model

### Capability Tokens

Every route operation requires a capability token:

```json
{
  "saddr": "rtt://core/api/metrics",
  "verb": "open|tx|rx|close",
  "scopes": ["metrics.read"],
  "exp": "2025-10-24T00:05:00Z",
  "nonce": "<32b>"
}
```

### Signing Chain

```
Trust Root (Keys)
    │
    ├──▶ Manifest Signature (Ed25519)
    │
    ├──▶ Plan Signature (Ed25519)
    │
    └──▶ View Signature (Ed25519)
```

**Strict Mode:** Rejects unsigned manifests and plans

### Driver Sandboxing

Drivers run out-of-process with minimal profiles:
- **Linux:** seccomp-bpf filters
- **macOS:** sandbox-exec
- **Windows:** AppContainer

**Default:** No network, read-only filesystem, specific syscalls only

---

## Non-Functional Characteristics

### Performance

| Metric | Target | Validation |
|--------|--------|------------|
| Control path p99 | ≤ 300 µs | Simulated |
| SHM data path p99 @ 64 KiB | ≤ 1.5 ms | Simulated |
| Plan generation | ≤ 1s for 100 routes | Measured |
| WAL replay | ≤ 100ms for 1000 entries | Future |

### Reliability

- **Determinism:** Same inputs → same plan hash (100%)
- **Atomicity:** 2PC ensures all-or-nothing commits
- **Durability:** WAL persists every commit
- **Crash Recovery:** WAL replay restores last committed state

### Scalability

| Dimension | Limit | Notes |
|-----------|-------|-------|
| Routes | 10,000+ | Constraint solver may need caching |
| Symbols | 100,000+ | CAS packfile supports large catalogs |
| Providers | 100+ | Virtual views prevent duplication |
| Languages | 25+ | Universal stub protocol |
| NUMA Nodes | 8+ | Placement optimizer supports multi-node |

---

## Deployment Architectures

### Single-Node Development

```
┌─────────────────────┐
│   Workstation       │
│                     │
│  RTT Panel (local)  │
│  CAS Registry       │
│  All Providers      │
│  MCP Servers        │
└─────────────────────┘
```

### Multi-Node Cluster (Future)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Node 0     │  │   Node 1     │  │   Node 2     │
│              │  │              │  │              │
│ RTT Panel    │  │ RTT Worker   │  │ RTT Worker   │
│ CAS (master) │  │ CAS (replica)│  │ CAS (replica)│
│ Providers A  │  │ Providers B  │  │ Providers C  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └────────┬────────┴─────────────────┘
                │
          RTT Fabric (SHM local, UDS/TCP remote)
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Storage** | CAS (SHA256), Packfile (mmap) | Content addressing |
| **Signing** | Ed25519 (PyNaCl, Rust, Go) | Cryptographic signatures |
| **Config** | YAML, JSON, CUE | Typed configuration |
| **Constraint Solving** | Greedy + ILP (PuLP) | Route optimization |
| **Data Plane** | SHM (POSIX/Windows), UDS, TCP | Low-latency transport |
| **VFS** | FUSE (Linux/macOS), WinFsp (Windows) | Virtual filesystem |
| **Telemetry** | Custom (zero-alloc), future eBPF/ETW | Metrics collection |
| **Automation** | Python scripts | Build pipeline |
| **Production** | Rust, Go, Node.js | High-performance components |

---

## Evolution Roadmap

### Current State (v1.0)
- ✅ CAS registry with packfile
- ✅ Signed plans
- ✅ Constraint solver
- ✅ MCP integration
- ✅ Multi-language stubs
- ✅ Automation pipeline

### Near-Term (v1.1-v1.2)
- Full VFS daemon (FUSE/WinFsp)
- Production SHM ring implementation
- TLA+ formal spec
- Real autotune with traces
- Expanded chaos testing

### Long-Term (v2.0+)
- Distributed RTT (multi-node coordination)
- Advanced schedulers (EDF, CBS, WFQ)
- ML-based placement
- Web UI for management
- Enterprise features (RBAC, audit)

---

## References

- **PRD:** [RSD-PLAN.md](./RSD-PLAN.md)
- **Implementation:** [PHASE-GUIDE.md](./PHASE-GUIDE.md)
- **Mapping:** [DROPIN-MAPPING.md](./DROPIN-MAPPING.md)
- **Agents:** [AGENT-COORDINATION.md](./AGENT-COORDINATION.md)
- **Acceptance:** [ACCEPTANCE-CRITERIA.md](./ACCEPTANCE-CRITERIA.md)

---

**End of Architecture Overview**
