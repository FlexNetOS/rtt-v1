# Relay Terminal Tool (RTT) - Requirements & Software Design Plan
## Production-Ready System with Autonomous Execution

**Project:** RTT v1 - Multi-Agent Relay Terminal Tool
**Repository:** `/home/deflex/rtt/rtt-v1`
**Date:** 2025-10-27
**Status:** Approved - Ready for Execution

---

## Executive Summary

**Objective:** Transform the 12 extracted dropin archives into a fully integrated, production-ready Relay Terminal Tool (RTT) system with MCP integration, content-addressed registry, virtual provider views, and automated build-operate loops.

**Approach:** Sequential execution with background agent verification to ensure zero duplication, complete integration, and production readiness.

**Timeline:** 12 execution phases with continuous verification

**Deliverable:** Production-ready RTT system meeting all P0, P1, and P2 milestones from the PRD

**Key Innovation:** Local, deterministic connection fabric that discovers symbols, solves routes, wires lanes, and hot-swaps endpoints across multi-agent, multi-provider stacks without duplication.

---

## 1. Requirements Analysis

### 1.1 Core Requirements (from rtt-prd.md)

**Functional Requirements:**

1. **Discovery & Registry** - CAS-based, content-addressed storage with signed entries
2. **Virtual Provider Views** - FUSE/WinFsp with deterministic overlays, no file duplication
3. **Constraint Planner** - Deterministic solver with QoS, NUMA awareness, signed plans
4. **2-Phase Commit Apply** - Atomic, reversible route changes with WAL
5. **Fabric** - SHM SPSC rings for hot paths, UDS/TCP for control/fallback
6. **Observability** - Flight recorder with p50/p95/p99 metrics, breaker states
7. **Security** - Ed25519 signatures, capability tokens, driver sandboxing
8. **Autotune** - Trace-driven optimization with machine-specific profiles
9. **MCP Bridge** - Import MCP tools as RTT symbols, route via RTT fabric
10. **Multi-Language Support** - Universal connector protocol across 25+ languages

**Non-Functional Requirements:**

- **Latency SLO:** Control path p99 ≤ 300 µs; SHM data path p99 ≤ 1.5 ms @ 64 KiB
- **Determinism:** Same inputs → same plan hash (reproducible routing)
- **Recovery:** WAL replay to last committed graph after crash
- **Compliance:** SBOM embedded, signed artifacts, reproducible builds
- **Offline-First:** No cloud dependency, no hidden network calls
- **Local-First:** Single folder deployment, portable across platforms

### 1.2 Component Inventory (from 12 dropins)

| # | Dropin Archive | Size | Purpose | Key Components |
|---|----------------|------|---------|----------------|
| 1 | rtt_dropin.zip | 10KB | Base foundation | .rtt/ structure, panel.yaml, policy.json, routes.json, schemas |
| 2 | cas_vfs_starter.zip | ~15KB | CAS registry | registry/cas/, packfile, index, trust keys, view engine |
| 3 | rtt_signed_plans_starter.zip | ~8KB | Signing infrastructure | Ed25519 helpers, plan builder, verifier |
| 4 | rtt_solver_constraints.zip | ~12KB | Constraint solver | Version meet, QoS checks, policy ACL, NUMA-aware |
| 5 | rtt_placement_churn.zip | ~10KB | Placement optimizer | NUMA placement, churn minimization, local search |
| 6 | rtt_exact_admission.zip | ~8KB | ILP solver | Binary placement, admission control, capacity constraints |
| 7 | rtt_elite_addon.zip | ~15KB | Automation | Auto-builders, agent bus, LLM integration, systemd |
| 8 | rtt_mcp_ingest_signed_plans.zip | ~12KB | MCP integration | MCP tool ingest, autowire, invariant gates |
| 9 | rtt_next_upgrades.zip | ~50KB | Production components | Rust/Go/Node stubs, VFS daemon, SHM ring, drivers |
| 10 | universal_stubs.zip | ~100KB | Multi-language support | 25+ language connector stubs |
| 11 | rtt_mcp_dropin.zip | ~8KB | MCP connector | MCP-RTT bridge |
| 12 | mcp_opt_shims_bundle.zip | ~10KB | MCP optimizations | Performance shims |

**Total Archive Size:** ~258KB of compressed implementation assets

---

## 2. System Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RTT Production System                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌─────────────┐    ┌──────────────┐   │
│  │   Agents CAS │───▶│ View Engine │───▶│   VFS Mount  │   │
│  │  + Packfile  │    │  + Overlays │    │ FUSE/WinFsp  │   │
│  └──────────────┘    └─────────────┘    └──────────────┘   │
│         │                    │                   │           │
│         │                    │                   │           │
│         ▼                    ▼                   ▼           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              RTT Constraint Planner                   │   │
│  │  (Solver + Placement + Admission + Signed Plans)     │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          2PC Reconciler + Merkle WAL                  │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │      RTT Fabric (SHM SPSC + UDS + TCP Lanes)         │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ├─────────┬──────────┬──────────┐                  │
│         ▼         ▼          ▼          ▼                  │
│    MCP Tools  Drivers   Services   Plugins                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Telemetry (Flight Recorder + Metrics + Breakers)    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │      Autotune Engine (Trace Replay + Sweeps)         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
1. Discovery:    Scan folders → Index symbols → CAS registry
2. Planning:     Routes + Policy → Constraint solver → Signed plan
3. Apply:        Plan → 2PC reconciler → WAL → Fabric update
4. Execution:    Symbol call → Lane routing → Driver execution
5. Observation:  Flight recorder → Metrics → SLO gates
6. Optimization: Traces → Autotune → Tuned profiles
```

### 2.3 Secret Formula

**Specify → Prove → Generate → Measure → Autotune**

1. **Specify:** Formal state machine for scan→plan→2PC→verify→rollback
2. **Prove:** Invariants checked with lightweight model (TLA+ or SMT)
3. **Generate:** Constraint planner emits signed immutable plans
4. **Measure:** p50/p95/p99 histograms and breaker states from flight recorder
5. **Autotune:** Trace-driven sweeps produce machine-specific tuned profiles

---

## 3. Detailed Phase Breakdown

### Phase 1: Foundation Layer
**Source:** `rtt_dropin.zip` (10KB)
**Duration:** Foundation setup
**Verification Agent:** `Explore` (verify structure)

**Objectives:**
- Establish base .rtt/ directory structure
- Deploy core configuration files
- Set up runtime directories
- Install validation schemas

**Actions:**
1. Extract to project root
2. Create `.rtt/` directory structure:
   - `panel.yaml` - Node configuration
   - `policy.json` - ACL, QoS, pins, failover rules
   - `routes.json` - Desired route state
   - `manifests/` - Symbol contract definitions
   - `drivers/` - Connector binaries placeholder
   - `cache/`, `wal/`, `sockets/` - Runtime directories
3. Extract `schemas/` with JSON validation schemas:
   - `rtt.symbol.schema.json`
   - `rtt.policy.schema.json`
   - `rtt.routes.schema.json`
4. Extract `tests/validate.py` - Offline validator

**Outputs:**
- `.rtt/panel.yaml` - Base configuration
- `.rtt/policy.json` - ACL, QoS, pins, failover
- `.rtt/routes.json` - Desired routes
- 5 sample manifests in `.rtt/manifests/`:
  - core.api.metrics.json
  - core.bus.events.json
  - idp.api.auth.json
  - obs.extension.logger.ndjson.json
  - ui.hook.refresh.json
- Validation script ready
- Directory structure established

**Verification Tasks:**
- ✓ Background agent confirms all files present
- ✓ Run `python tests/validate.py` to verify schemas
- ✓ Confirm no conflicts with existing files
- ✓ Validate YAML/JSON syntax

**Success Criteria:**
- All files extracted without conflicts
- Validation script passes
- Directory permissions correct
- No files deleted or overwritten

---

### Phase 2: CAS Registry & Views
**Source:** `cas_vfs_starter.zip` (~15KB)
**Duration:** Content-addressed storage setup
**Verification Agent:** `Explore` + `test-writer-fixer`

**Objectives:**
- Implement content-addressed storage (CAS)
- Build packfile for zero-copy reads
- Set up virtual provider views
- Enable overlay system

**Actions:**
1. Extract `.rtt/registry/` structure:
   - `cas/sha256/` - Immutable signed entries
   - `pack/agents.pack` - Memory-mapped packfile
   - `pack/index.lut` - SHA256 → {offset, len} lookup
   - `trust/keys/` - Trusted signer public keys
   - `index.json` - ID@version → SHA256 mapping
2. Extract `agents/common/` canonical agents:
   - `summarize.agent.json`
   - `search.agent.json`
   - `code_fix.agent.json`
3. Extract `overlays/` system:
   - `provider/claude/*.patch.json` - Provider-specific overlays
   - `env/prod/_global.patch.json` - Environment overlays
4. Extract `views/` with view definitions:
   - `claude.view.json` - Provider view plan
5. Extract `providers/` structure:
   - `claude/.claude/agents/` - Materialized view
6. Extract CAS tools to `tools/`:
   - `cas_ingest.py` - Source → CAS ingestion
   - `cas_pack.py` - CAS → packfile builder
   - `view_materialize.py` - CAS+overlays → provider view
   - `view_to_rtt.py` - Provider view → RTT manifests
   - `apply_overlay.py` - Overlay application logic

**Outputs:**
- CAS registry operational at `.rtt/registry/`
- 3 canonical agents stored in CAS with SHA256 hashes
- Packfile + LUT index for zero-copy reads
- View engine scripts ready
- Provider overlay system functional
- Sample view materialized for Claude provider

**Verification Tasks:**
- ✓ Background agent runs `cas_ingest.py` on sample agents
- ✓ Verify SHA256 hashes computed correctly
- ✓ Confirm packfile generation works
- ✓ Test overlay application logic
- ✓ Validate view materialization produces correct merged files

**Success Criteria:**
- CAS entries are immutable and content-addressed
- Packfile can be memory-mapped
- Overlays merge deterministically
- No duplicate agent files created
- View materialization produces valid RTT manifests

---

### Phase 3: Signing Infrastructure
**Source:** `rtt_signed_plans_starter.zip` (~8KB)
**Duration:** Security foundation
**Verification Agent:** `test-writer-fixer`

**Objectives:**
- Implement Ed25519 signing/verification
- Build plan generation pipeline
- Enable signature validation
- Establish trust chain

**Actions:**
1. Extract signing tools to `tools/`:
   - `ed25519_helper.py` - PyNaCl wrapper with fallback
   - `keys_ed25519.py` - Key generation utility
   - `sign_view.py` - View signing tool
   - `verify_view.py` - Signature verification
   - `plan_build.py` - Deterministic plan builder
   - `plan_verify.py` - Plan signature verification
2. Create `plans/` directory for signed plans
3. Create `.rtt/registry/keys/private/` for private key storage
4. Create `security/` directory:
   - `caps.schema.json` - Capability token schema
   - `sandbox/` - Sandbox profile storage

**Outputs:**
- Ed25519 signing toolchain operational
- Plan generation pipeline:
  - Reads `.rtt/routes.json` + manifests
  - Computes deterministic plan
  - Assigns `plan_id = sha256(unsigned_plan)`
  - Signs with Ed25519
  - Writes `plans/<plan_id>.json` + `plans/latest.json`
- Signature verification for plans and views
- Trust key management system
- Capability schema defined

**Verification Tasks:**
- ✓ Generate test Ed25519 keypair
- ✓ Sign sample plan
- ✓ Verify signature validates
- ✓ Confirm plan hash determinism (same inputs → same hash)
- ✓ Test signature rejection for tampered plans
- ✓ Validate key rotation workflow

**Success Criteria:**
- Plans are deterministically hashed
- Signatures verify correctly
- Tampered plans are rejected
- Key generation is reproducible
- Private keys stored securely

---

### Phase 4: Constraint Solver
**Source:** `rtt_solver_constraints.zip` (~12KB)
**Duration:** Planning intelligence
**Verification Agent:** `backend-architect` (background review)

**Objectives:**
- Implement constraint-based routing solver
- Add QoS and version compatibility checks
- Enable policy-aware planning
- Support NUMA-aware lane selection

**Actions:**
1. Extract constraint solver to `planner/`:
   - `constraints.py` - Constraint definitions:
     - Semver version meet logic
     - QoS latency budget validation
     - Policy ACL enforcement
     - Type compatibility checking
   - `solver.py` - Constraint solving engine:
     - Greedy solver for large graphs
     - Deterministic ordering
     - Stable secondary keys
2. Update `tools/plan_build.py` with constraint integration:
   - Pre-solve validation (existence, no duplicates, no self-loops)
   - Constraint checking during solve
   - Rejected routes reporting
3. Add lane selection logic:
   - SHM only if co-located + supported
   - Prefer UDS over TCP for same-host
   - Respect `supports_shm` tags in manifests

**Outputs:**
- `planner/constraints.py` - Constraint definitions and validators
- `planner/solver.py` - Constraint solving engine
- Enhanced plan builder with validation gates
- Constraint failure reporting (JSON rejected routes list)
- Lane assignment based on placement + capabilities

**Verification Tasks:**
- ✓ Run solver on sample routes with various constraints
- ✓ Verify version meet calculations (semver ranges)
- ✓ Confirm QoS budget violations are caught
- ✓ Test policy ACL allow/deny rules
- ✓ Validate NUMA cross-node penalties applied
- ✓ Ensure rejected routes report includes reason

**Success Criteria:**
- Constraints prevent invalid routes
- QoS budgets enforced
- Version incompatibilities detected
- Policy violations blocked
- Solver produces deterministic results
- Exit non-zero on constraint failures

---

### Phase 5: Placement Optimizer
**Source:** `rtt_placement_churn.zip` (~10KB)
**Duration:** NUMA optimization
**Verification Agent:** `backend-architect`

**Objectives:**
- Add NUMA-aware symbol placement
- Minimize cross-node traffic
- Reduce churn on re-planning
- Optimize lane selection based on placement

**Actions:**
1. Extract to `placement/numa/`:
   - Topology detection utilities
   - Node capacity modeling
   - Placement solver with local search
   - Churn cost calculation
2. Add `planner/placement.py` - Integration module
3. Create `.rtt/topology.json` template:
   - Node definitions with capacity
   - NUMA domain mapping
   - Placement hints
4. Update plan builder with placement:
   - Seed from `last_applied.json` or topology hints
   - Repack on capacity violations
   - Local search optimization
   - Churn weighting

**Outputs:**
- `placement/numa/` directory with:
  - Topology probing
  - Capacity-aware packing
  - Local search optimizer
  - Churn minimization
- `.rtt/topology.json` - Node capacity definitions
- Plans now include `placement{saddr→node}` section
- `plans/analysis.json` with:
  - Total cost breakdown
  - Moved symbol count
  - Route changes summary
  - Lane flip count

**Verification Tasks:**
- ✓ Test placement on multi-node topology
- ✓ Verify SHM lanes only for co-located endpoints
- ✓ Confirm churn weight respected (prefer keeping placement)
- ✓ Validate capacity constraints prevent overload
- ✓ Test local search finds improvements
- ✓ Ensure placement persists across replans

**Success Criteria:**
- Co-located symbols use SHM when supported
- Cross-node communication minimized
- Churn stays low on incremental changes
- Capacity constraints enforced
- Placement survives plan regeneration
- Analysis shows cost vs. previous plan

---

### Phase 6: ILP Admission Control
**Source:** `rtt_exact_admission.zip` (~8KB)
**Duration:** Exact solver
**Verification Agent:** `backend-architect`

**Objectives:**
- Implement exact ILP solver for small graphs
- Add admission control (reject routes when capacity tight)
- Optimize for latency + admission priority
- Provide exact solutions vs. greedy heuristics

**Actions:**
1. Extract `tools/ilp/plan_build_ilp.py` - ILP solver using PuLP
2. Define ILP model with binary variables:
   - `x[s,n]` - Symbol s placed on node n
   - `a[r]` - Route r admitted (1) or rejected (0)
   - `y[r,l]` - Route r uses lane l
   - `d[r]` - Route r crosses nodes (1) or not (0)
   - `mv[s]` - Symbol s moved from previous placement
   - `lc[r]` - Route r changed lanes
3. Add constraints:
   - One node per active symbol
   - SHM lane requires co-location
   - Latency budgets via big-M constraints
   - CPU and memory capacity per node
   - Version meet and policy (pre-filtered)
4. Define objective:
   - Maximize admissions (large negative weight)
   - Minimize latency (predicted by lane + cross-node)
   - Minimize NUMA penalties
   - Minimize churn (moves + lane changes)
5. Add admission priority tuning parameters

**Outputs:**
- `tools/ilp/plan_build_ilp.py` - ILP solver
- Exact optimal solution for small graphs (<100 routes)
- Admission control with rejection reporting
- `plans/analysis.json` includes:
  - Admitted route count
  - Rejected routes with reasons
  - Capacity utilization per node
  - Objective value breakdown

**Verification Tasks:**
- ✓ Run ILP on constrained capacity scenario
- ✓ Verify capacity limits enforced (routes rejected)
- ✓ Confirm admission priority weighting works
- ✓ Test that SHM constraints respected
- ✓ Validate QoS budget violations cause rejection
- ✓ Compare ILP vs. greedy solutions

**Success Criteria:**
- ILP finds optimal solutions for small graphs
- Capacity constraints prevent overload
- Routes rejected gracefully with reasons
- Admission priority respected
- Solutions better than greedy (lower cost)
- Solver runtime acceptable (<10s for typical graphs)

---

### Phase 7: Elite Automation
**Source:** `rtt_elite_addon.zip` (~15KB)
**Duration:** Build automation
**Verification Agent:** `devops-automator` + `workflow-optimizer`

**Objectives:**
- Add end-to-end automation pipeline
- Implement typed config validation (CUE)
- Deploy telemetry and observability
- Enable chaos testing
- Set up systemd service

**Actions:**
1. Extract automation pipeline to `auto/`:
   - `00-bootstrap.py` - Initialize directories and configs
   - `10-scan_symbols.py` - Discover and index symbols
   - `20-depdoctor.py` - Unify dependencies (npm/pip/go)
   - `30-generate_connectors.py` - Auto-generate connector stubs
   - `40-plan_solver.py` - Run constraint solver
   - `50-apply_plan.py` - Apply plan with 2PC + WAL
2. Extract typed configs to `cue/`:
   - `panel.cue` - Panel configuration schema
   - `routes.cue` - Routes schema (future)
   - `policy.cue` - Policy schema (future)
3. Extract formal spec to `spec/`:
   - `invariants.md` - Runtime invariant definitions
   - `tla/` - TLA+ model directory (placeholder)
4. Extract telemetry to `telemetry/`:
   - `flight_recorder/flight.py` - Zero-alloc metrics recorder
5. Extract chaos testing to `chaos/`:
   - `cases.yaml` - Chaos scenario definitions (kill, slow, corrupt)
6. Extract systemd service to `systemd/`:
   - `rtt-panel.service` - User-mode service definition
7. Extract agent infrastructure to `agent/`:
   - `agent_bus.py` - Local UDS pub/sub bus for agent coordination
8. Extract LLM integration to `llama/`:
   - `call_llama.py` - Optional semantic wiring via llama.cpp
   - `README.md` - Setup instructions
9. Create `autotune/` directory structure
10. Create `.rtt/tuned/profile.json` template for machine-specific tuning

**Outputs:**
- Complete automation pipeline (00-50 scripts)
- CUE typed config validation
- Flight recorder for telemetry:
  - Per-route p50/p95/p99 latency
  - Queue depth tracking
  - Drop reason logging
  - Breaker state monitoring
- Chaos test framework
- Agent coordination bus
- Systemd service for production deployment
- Optional LLM semantic wiring
- Autotune framework (ready for trace input)

**Verification Tasks:**
- ✓ Run full automation pipeline end-to-end:
  - `00-bootstrap.py` creates directories
  - `10-scan_symbols.py` indexes manifests
  - `20-depdoctor.py` finds dependency conflicts
  - `30-generate_connectors.py` creates stubs
  - `40-plan_solver.py` generates signed plan
  - `50-apply_plan.py` applies with WAL
- ✓ Validate CUE schema enforcement
- ✓ Test flight recorder metrics collection
- ✓ Execute chaos scenarios from cases.yaml
- ✓ Verify systemd service installs and runs
- ✓ Test agent bus pub/sub

**Success Criteria:**
- Automation pipeline runs without manual intervention
- CUE validation catches config errors
- Flight recorder captures metrics
- Chaos tests execute successfully
- Systemd service starts/stops cleanly
- Agent bus enables tool coordination
- Pipeline is idempotent (can re-run safely)

---

### Phase 8: MCP Integration
**Source:** `rtt_mcp_ingest_signed_plans.zip` (~12KB)
**Duration:** MCP bridge
**Verification Agent:** `backend-architect`

**Objectives:**
- Ingest MCP tools into CAS registry
- Auto-wire agents to MCP tools
- Add pre-sign invariant gates
- Enable MCP server integration

**Actions:**
1. Extract MCP ingestion tools to `tools/`:
   - `mcp_ingest.py` - MCP tools.json → CAS entries + RTT manifests
   - `agents_ingest.py` - Canonical agents → CAS
   - `skills_ingest.py` - Skills → CAS for capability matching
   - `invariants_check.py` - Pre-sign safety gates
2. Update `tools/plan_build.py` with new features:
   - `--autowire` flag for agent↔tool name/skill matching
   - Invariant gates run before plan hashing/signing:
     - Existence: all `from`/`to` in manifests
     - No duplicate `(from,to)` pairs
     - No self-loops (unless explicitly allowed)
     - Optional: version meet non-empty, policy allows, QoS defined
3. Create `connector-mcp/` directory:
   - `bridge.py` - MCP-RTT connector bridge
   - `config/` - MCP server configurations
4. Create `mcp/` directory:
   - Provider subdirectories (claude, openai, mistral)
   - `tools.json` files for each provider
   - `shared/` for common tool definitions

**Outputs:**
- MCP tool ingestion pipeline:
  - Reads `mcp/<provider>/tools.json`
  - Writes immutable CAS entries
  - Generates RTT manifests
- Autowire capability:
  - Matches agents to tools by name
  - Matches by shared skill capabilities
  - Proposes routes for approval
- Invariant gates (pre-sign):
  - Block plan emission on safety violations
  - Exit non-zero with detailed error JSON
  - No tampered or incomplete plans signed
- MCP-RTT connector bridge operational

**Verification Tasks:**
- ✓ Ingest sample MCP tools from multiple providers
- ✓ Verify CAS entries created with correct hashes
- ✓ Test autowire suggestions for agent-tool pairs
- ✓ Validate invariant gates reject bad configurations:
  - Missing endpoints
  - Duplicate routes
  - Self-loops
  - Version conflicts
- ✓ Confirm only valid plans get signed
- ✓ Test MCP tool routing through RTT fabric

**Success Criteria:**
- MCP tools appear as RTT symbols
- Autowire finds valid agent-tool pairs
- Invariant violations prevent plan generation
- No unsigned/invalid plans created
- MCP servers route through RTT lanes
- Tools callable via RTT routing

---

### Phase 9: Production Components
**Source:** `rtt_next_upgrades.zip` (~50KB)
**Duration:** Rust/Go/Node production code
**Verification Agent:** `devops-automator`

**Objectives:**
- Add production-grade VFS daemon (Rust)
- Implement signing CLI (Rust + Go)
- Build constraint planner (Rust)
- Create SHM ring library (Rust)
- Deploy multi-language drivers
- Set up build tooling (Cargo, Go, PNPM)

**Actions:**
1. Extract `viewfs/` VFS daemon:
   - `rust-fuse/` - FUSE daemon for Linux/macOS
   - `windows/README.md` - WinFsp implementation plan
2. Extract production tools:
   - `tools/rtt_sign_rs/` - Rust Ed25519 CLI (gen, sign, verify)
   - `tools/rtt_sign_go/` - Go Ed25519 CLI (gen, sign, verify)
   - `tools/rtt_planner_rs/` - Rust constraint planner with signing
3. Extract fabric components to `fabric/`:
   - `shm/` - Rust SHM SPSC ring crate:
     - Power-of-two ring buffer
     - Length-prefixed frames
     - Acquire/Release atomics only
     - No locks on hot path
   - `uds/` - Unix domain socket lane
   - `tcp/` - TCP loopback lane
4. Extract driver framework to `drivers/`:
   - `rust/` - Rust driver SDK
   - `python/` - Python driver template
   - `go/` - Go driver module
   - `node/` - Node.js NAPI driver
   - `README.md` - Shared protocol docs (JSON over stdio)
5. Extract JavaScript/TypeScript setup:
   - `package.json` - Root package
   - `pnpm-workspace.yaml` - Monorepo workspace
   - `.npmrc` - PNPM config
   - `.pnpmfile.cjs` - Hooks
   - `tsconfig.json` - TypeScript config
6. Create `Cargo.toml` - Rust workspace root
7. Create `go.mod` - Go module definition

**Outputs:**
- VFS daemon (Rust + FUSE):
  - Mounts provider views from CAS
  - Applies overlays on-the-fly
  - Zero-copy reads from packfile
- Production signing tools:
  - `rtt-sign` (Rust) - Fast, zero-dependency
  - `rtt-sign` (Go) - Alternative implementation
- Rust planner:
  - Emits deterministic plans
  - Signs with Ed25519
- SHM ring library:
  - SPSC ring buffer
  - Frame header: `{magic, flags, route_id, frame_id, len, crc32c}`
  - Benchmarks included
- Multi-language driver SDKs
- Build tooling configured:
  - Cargo workspace
  - Go module
  - PNPM monorepo

**Verification Tasks:**
- ✓ Build Rust components:
  ```bash
  cd tools/rtt_sign_rs && cargo build --release
  cd planner/rtt_planner_rs && cargo build --release
  cd fabric/shm && cargo test
  ```
- ✓ Build Go components:
  ```bash
  cd tools/rtt_sign_go && go build
  ```
- ✓ Install Node dependencies:
  ```bash
  pnpm install
  ```
- ✓ Test driver protocol with sample Rust/Python/Go/Node drivers
- ✓ Verify VFS daemon compiles (may need FUSE libs installed)
- ✓ Test SHM ring benchmarks
- ✓ Confirm signing tools generate compatible signatures

**Success Criteria:**
- All Rust code compiles
- All Go code compiles
- Node dependencies install without errors
- Driver protocol consistent across languages
- Signing tools interoperable (Rust-signed → Go-verified)
- SHM ring passes tests
- VFS daemon ready for integration (may need runtime FUSE setup)

---

### Phase 10: Universal Stubs
**Source:** `universal_stubs.zip` (~100KB)
**Duration:** Multi-language support
**Verification Agent:** `Explore`

**Objectives:**
- Deploy connector stubs for 25+ languages
- Document universal protocol
- Enable RTT symbol binding from any runtime

**Actions:**
1. Extract to `stubs/` directory
2. Organize by language (25+ supported):
   - **Runnable:** python, node, typescript, bash, powershell, ruby, php, perl, lua, go, rust, java, c, cpp, csharp, swift, kotlin, dart, julia, haskell, ocaml, clojure, groovy, r, pascal
   - **Placeholders with docs:** abap, bibtex, coffeescript, css, cuda-cpp, d, diff, dockercompose, dockerfile, erlang, fsharp, git-commit, git-rebase, handlebars, haml, html, ini, json, jsonc, latex, less, makefile, markdown, objective-c, objective-cpp, perl6, plaintext, jade, pug, razor, scss, sass, shaderlab, shellscript, slim, sql, stylus, svelte, typescriptreact, tex, vb, vue, vue-html, xml, xsl, yaml
3. Document JSON-over-stdio protocol:
   ```json
   Request:  {"id": "<uuid>", "method": "Probe|Open|Tx|Rx|Close|Health", "params": {...}}
   Response: {"id": "<uuid>", "result": {...}, "error": null}
   ```
4. Create stub registration system in automation pipeline

**Outputs:**
- `stubs/` directory with 25+ language templates
- Universal connector interface documented
- Consistent JSON protocol across all languages
- README per stub with usage instructions
- Integration guide for binding stubs to RTT

**Verification Tasks:**
- ✓ Catalog all stub languages (verify 25+ present)
- ✓ Verify protocol consistency across stubs
- ✓ Test sample stubs (Python, Node, Rust, Go)
- ✓ Validate JSON request/response format
- ✓ Confirm method signatures match (Probe/Open/Tx/Rx/Close/Health)
- ✓ Check documentation completeness

**Success Criteria:**
- All 25+ languages represented
- Protocol identical across languages
- Sample stubs execute successfully
- Documentation clear and complete
- Stubs ready for RTT integration via manifests

---

### Phase 11: MCP Optimization
**Source:** `rtt_mcp_dropin.zip` + `mcp_opt_shims_bundle.zip` (~18KB combined)
**Duration:** Performance tuning
**Verification Agent:** `devops-automator`

**Objectives:**
- Finalize MCP-RTT integration
- Add performance shims
- Configure multi-provider MCP routing
- Optimize MCP tool latency

**Actions:**
1. Extract `mcp/` provider configurations:
   - `claude/tools.json` - Claude MCP tools
   - `openai/tools.json` - OpenAI MCP tools
   - `mistral/tools.json` - Mistral MCP tools
   - `shared/` - Common tool definitions
2. Extract optimization shims from `mcp_opt_shims_bundle.zip`:
   - Batching optimizations
   - Connection pooling
   - Caching layers
   - Latency reduction techniques
3. Wire MCP servers to RTT fabric:
   - MCP tools appear as RTT symbols
   - Route via optimal lanes (UDS for local, TCP for remote)
   - Apply QoS policies to MCP calls
4. Add performance monitoring for MCP routes
5. Configure multi-provider routing policies

**Outputs:**
- MCP provider configurations for Claude, OpenAI, Mistral
- Performance optimization shims applied
- MCP-RTT routing optimized:
  - Local MCP servers use UDS
  - Remote servers use TCP with connection pooling
  - Batch requests where possible
  - Cache frequent tool lookups
- Performance metrics for MCP routes in flight recorder

**Verification Tasks:**
- ✓ Test MCP tool routing through RTT fabric
- ✓ Measure latency with and without optimization shims
- ✓ Verify connection pooling reduces overhead
- ✓ Confirm batch optimizations work
- ✓ Test multi-provider scenarios (Claude + OpenAI simultaneously)
- ✓ Validate QoS policies apply to MCP routes
- ✓ Check flight recorder captures MCP metrics

**Success Criteria:**
- MCP tools route through RTT successfully
- Optimization shims reduce latency measurably
- Connection pooling prevents connection thrashing
- Multi-provider routing works without conflicts
- Performance metrics collected for MCP routes
- No degradation in MCP tool functionality

---

### Phase 12: Verification & Testing
**Source:** All previous phases + comprehensive testing
**Duration:** Final validation
**Verification Agent:** `test-writer-fixer`

**Objectives:**
- Create comprehensive test suite
- Validate all acceptance criteria
- Run automation pipeline end-to-end
- Generate documentation
- Produce SBOM and sign artifacts

**Actions:**

**1. Test Suite Creation:**
- Unit tests for each component:
  - CAS registry operations
  - Signature generation/verification
  - Constraint solver logic
  - Placement optimizer
  - ILP admission control
  - Plan determinism
  - WAL operations
- Integration tests:
  - Full automation pipeline (00-50)
  - CAS → VFS → Planner → Apply flow
  - MCP tool routing
  - Multi-language stub protocol
  - Agent-tool autowiring
- Chaos tests from `chaos/cases.yaml`:
  - Driver kill scenarios
  - Slow consumer simulation
  - Corrupted frame handling
  - Clock drift tolerance
- Performance benchmarks:
  - Control path latency (target p99 ≤ 300 µs simulated)
  - SHM path latency (target p99 ≤ 1.5 ms @ 64 KiB simulated)
  - Plan generation time
  - WAL replay time

**2. Automation Pipeline Validation:**
```bash
# Full end-to-end test
python auto/00-bootstrap.py      # Initialize
python auto/10-scan_symbols.py   # Discover symbols
python auto/20-depdoctor.py      # Unify dependencies
python auto/30-generate_connectors.py  # Generate stubs
python auto/40-plan_solver.py    # Solve constraints
python auto/50-apply_plan.py     # Apply with 2PC + WAL
```

**3. Acceptance Criteria Validation:**

**P0 Baseline:**
- ✓ CAS registry with signed entries operational
- ✓ ViewFS mounts for 2+ providers configured
- ✓ Planner produces deterministic plans
- ✓ 2PC apply with rollback functional
- ✓ SHM + UDS lanes defined (stubs ready)
- ✓ Flight recorder captures metrics
- ✓ SLO targets documented and simulated
- ✓ Deterministic plan hash verified (same inputs → same hash)
- ✓ Rollback functionality tested
- ✓ Crash-replay validated (WAL restore)

**P1 Elite Core:**
- ✓ Constraint solver with QoS + NUMA operational
- ✓ Ed25519 signing infrastructure complete
- ✓ Token bucket admission framework ready
- ✓ Chaos suite defined and runnable
- ✓ Typed configs (CUE) enforced
- ✓ MCP integration working

**P2 Full Automation:**
- ✓ Autotune engine framework ready (trace input needed)
- ✓ CUE-typed configs validated at boot
- ✓ Signed plan-only apply enforced
- ✓ Multi-language stubs (25+) deployed
- ✓ Production components (Rust/Go/Node) built

**4. Documentation Generation:**
- `README.md` - Project overview and quickstart
- `docs/QUICKSTART.md` - Getting started guide
- `docs/ARCHITECTURE.md` - System architecture (already created)
- `docs/API.md` - API documentation
- `docs/DEPLOYMENT.md` - Production deployment guide
- `docs/TROUBLESHOOTING.md` - Common issues and solutions
- `docs/CONTRIBUTING.md` - Development guidelines

**5. SBOM and Artifact Signing:**
- Generate SBOM (Software Bill of Materials):
  - List all components and versions
  - Include dropins, tools, libraries
  - Document dependencies
- Sign release artifacts:
  - Sign final plans
  - Sign packfile
  - Sign critical binaries
- Verify supply chain:
  - All signatures validate
  - Reproducible builds documented
  - Trust chain established

**Outputs:**
- Complete test suite (unit + integration + chaos + perf)
- All tests passing with coverage report
- Automation pipeline runs successfully end-to-end
- Full documentation set
- SBOM generated
- Signed release artifacts
- Acceptance criteria validation report

**Verification Tasks:**
- ✓ Run full test suite, confirm all pass
- ✓ Execute automation pipeline, verify success
- ✓ Validate all P0 criteria met
- ✓ Validate 90%+ P1 criteria met
- ✓ Validate 50%+ P2 criteria met
- ✓ Review documentation completeness
- ✓ Verify SBOM includes all components
- ✓ Validate artifact signatures
- ✓ Confirm no files deleted during integration
- ✓ Check no duplicate files exist across providers

**Success Criteria:**
- All tests pass
- Automation pipeline runs without errors
- All P0 + 90% P1 + 50% P2 criteria met
- Documentation complete and accurate
- SBOM comprehensive
- Artifacts properly signed
- Zero file conflicts or deletions
- Production-ready system delivered

---

## 4. Agent Coordination Strategy

### 4.1 Background Verification Agents

**Purpose:** Agents run in parallel to verify work, cross-reference, and report issues WITHOUT blocking main execution.

**Agent Assignments:**

| Agent | Phases | Responsibilities | Reporting |
|-------|--------|------------------|-----------|
| **Explore** | 1, 2, 10 | Verify file structure, catalog components, check conflicts | Warnings for structure issues |
| **test-writer-fixer** | 2, 3, 7, 12 | Run tests, execute validators, verify integration | Critical on test failures |
| **backend-architect** | 4, 5, 6, 8 | Review architecture consistency, validate contracts | Warnings for design issues |
| **devops-automator** | 7, 9, 11 | Verify builds, test automation, check services | Critical on build failures |
| **workflow-optimizer** | Continuous | Track progress, identify bottlenecks, cross-reference | Suggestions for optimization |

### 4.2 Agent Communication Protocol

**Agents operate as observers:**
- Launch at phase start with specific verification tasks
- Run in background while main execution continues
- Report findings via structured output
- Do NOT block phase completion
- Provide warnings, not blockers (unless critical)

**Critical vs. Warning:**
- **Critical:** Missing dependencies, file conflicts, broken tests, build failures
- **Warning:** Style issues, optimization suggestions, documentation gaps

**Agent Launch Pattern:**
```
Phase Start
  ↓
Launch Verification Agent(s) in Background
  ↓
Continue Main Execution
  ↓
Check Agent Reports (non-blocking)
  ↓
Address Critical Issues if Found
  ↓
Phase Complete
```

### 4.3 Coordination Benefits

1. **Parallel Validation** - Testing happens while extraction continues
2. **Early Detection** - Issues found before cascading to later phases
3. **Non-Blocking** - Main execution not delayed by verification
4. **Comprehensive Coverage** - Multiple expert perspectives
5. **Cross-Referencing** - Agents catch inter-phase dependencies

---

## 5. Acceptance Criteria

### 5.1 P0 Baseline (Must Have) ✅

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| CAS registry operational | Immutable, signed entries | Test ingestion + verification |
| ViewFS mounts | 2+ providers | Materialize Claude + OpenAI views |
| Deterministic planner | Same inputs → same hash | Run planner 10x, compare hashes |
| 2PC apply + WAL | Atomic, rollback tested | Simulate failures, test rollback |
| SHM + UDS lanes | Stubs functional | Verify protocol implementation |
| Flight recorder | Metrics captured | Run sample flows, dump metrics |
| Plan determinism | Hash stability | Verify across reruns |
| Rollback works | WAL restore | Test crash recovery |

**Status:** All P0 criteria deliverable with provided dropins

### 5.2 P1 Elite Core (Should Have) ✅

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| Constraint solver | QoS + NUMA aware | Test with capacity constraints |
| Signing infrastructure | Ed25519 complete | Sign + verify test artifacts |
| Admission control | Token bucket framework | Test rate limiting |
| Chaos suite | Defined scenarios | Execute chaos/cases.yaml |
| Typed configs | CUE validation | Test invalid configs rejected |
| MCP integration | Tools routable | Route sample MCP tools |

**Status:** All P1 criteria deliverable with provided dropins

### 5.3 P2 Full Automation (Nice to Have) ✅

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| Autotune engine | Framework ready | Verify trace input hooks exist |
| CUE boot validation | Fail closed | Test boot with bad config |
| Signed-plan-only | Unsigned rejected | Test unsigned plan rejection |
| Multi-language stubs | 25+ languages | Catalog and test samples |
| Production components | Rust/Go/Node built | Compile and test |

**Status:** 50%+ P2 criteria deliverable (autotune framework, not full tuning)

### 5.4 Final Deliverables Checklist

**Integration:**
- [ ] All 12 dropins extracted and integrated
- [ ] Zero file conflicts across phases
- [ ] All cross-references validated
- [ ] Directory structure matches specification

**Functionality:**
- [ ] Automation pipeline (00-50) runs successfully
- [ ] CAS → VFS → Planner → Apply flow works end-to-end
- [ ] MCP tools route through RTT fabric
- [ ] Multi-language stubs ready for use

**Testing:**
- [ ] Unit tests pass (all components)
- [ ] Integration tests pass (end-to-end flows)
- [ ] Chaos tests execute successfully
- [ ] Performance benchmarks documented

**Documentation:**
- [ ] README.md complete with quickstart
- [ ] Architecture documentation comprehensive
- [ ] API documentation generated
- [ ] Deployment guide available
- [ ] Troubleshooting guide created

**Security & Compliance:**
- [ ] SBOM generated and complete
- [ ] Artifacts signed with Ed25519
- [ ] Trust chain validated
- [ ] No unsigned critical components

**Quality:**
- [ ] No duplicate files across providers
- [ ] Deterministic plan hashing confirmed
- [ ] WAL crash recovery validated
- [ ] Performance targets documented

---

## 6. Risk Mitigation

### 6.1 Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| File conflicts between dropins | Medium | High | Background Explore agent detects early; manual merge if needed |
| Missing dependencies across phases | Low | High | Dependency graph enforced; agents verify before proceeding |
| Integration failures at boundaries | Medium | Medium | Test after each phase with test-writer-fixer agent |
| Performance targets not achievable | Medium | Low | Document targets, provide tuning guide, note simulation limits |
| Platform incompatibilities (Windows) | Medium | Medium | Provide fallback implementations; document platform-specific steps |
| Agent coordination overhead | Low | Low | Agents observe only, don't block execution |
| Build failures (Rust/Go/Node) | Low | Medium | Provide build instructions, document dependencies |
| FUSE/WinFsp setup complexity | Medium | Medium | Document as optional; provide materialization fallback |

### 6.2 Rollback Strategy

**Per-Phase Rollback:**
- Each phase is atomic
- Verify before proceeding to next phase
- Git commit after each successful phase
- Can rollback to any previous phase via `git reset`

**Emergency Rollback:**
```bash
# View commit history
git log --oneline

# Rollback to phase N
git reset --hard <commit-hash>

# Verify state
git status
```

**Verification Before Commit:**
- Background agents report clear
- Tests pass for current phase
- No file conflicts detected
- User approval obtained (if interactive)

---

## 7. Success Metrics

### 7.1 Quantitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Dropins integrated | 12/12 (100%) | File count verification |
| File conflicts | 0 | Git status clean |
| Automation pipeline success | 100% | Scripts 00-50 all exit 0 |
| Test pass rate | 100% | All unit + integration tests pass |
| P0 criteria met | 10/10 (100%) | Acceptance checklist |
| P1 criteria met | 6/6 (100%) | Acceptance checklist |
| P2 criteria met | 3/5 (60%+) | Acceptance checklist |
| Documentation completeness | 95%+ | Doc coverage review |
| Build success rate | 100% | Rust/Go/Node compile |

### 7.2 Qualitative Metrics

| Metric | Assessment Criteria |
|--------|---------------------|
| Code quality | Clean, maintainable, well-structured |
| Documentation clarity | Easy to understand, comprehensive |
| Architecture consistency | Follows PRD design, no ad-hoc deviations |
| Production readiness | Can be deployed with documented steps |
| Extensibility | New providers/tools easy to add |
| Security posture | Signatures enforced, trust chain clear |

---

## 8. Timeline Summary

### 8.1 Phase Overview

```
Phase 1:  Foundation                  [rtt_dropin.zip]                    - Base setup
Phase 2:  CAS Registry                [cas_vfs_starter.zip]               - Storage layer
Phase 3:  Signing Infrastructure      [rtt_signed_plans_starter.zip]      - Security
Phase 4:  Constraint Solver           [rtt_solver_constraints.zip]        - Intelligence
Phase 5:  Placement Optimizer         [rtt_placement_churn.zip]           - NUMA aware
Phase 6:  ILP Admission Control       [rtt_exact_admission.zip]           - Exact solver
Phase 7:  Elite Automation            [rtt_elite_addon.zip]               - Build system
Phase 8:  MCP Integration             [rtt_mcp_ingest_signed_plans.zip]   - Tool bridge
Phase 9:  Production Components       [rtt_next_upgrades.zip]             - Rust/Go/Node
Phase 10: Universal Stubs             [universal_stubs.zip]               - Multi-lang
Phase 11: MCP Optimization            [rtt_mcp_dropin + mcp_opt_shims]    - Performance
Phase 12: Verification & Testing      [Comprehensive validation]          - Final checks
```

**Total:** 12 sequential phases with continuous background verification

### 8.2 Estimated Execution Time

- **Automated Extraction:** ~5 minutes (unzip all archives)
- **File Organization:** ~10 minutes (place in correct locations)
- **Build Steps:** ~15 minutes (Rust/Go/Node compilation)
- **Test Execution:** ~20 minutes (full test suite)
- **Documentation:** ~10 minutes (generate final docs)
- **Verification:** ~10 minutes (agent reports + manual review)

**Total Estimated Time:** ~70 minutes for full integration

*Note: Actual time may vary based on system performance and build dependencies*

---

## 9. Post-Completion Activities

### 9.1 Documentation Deliverables

**Core Documentation:**
1. `README.md` - Project overview, quickstart, architecture summary
2. `docs/QUICKSTART.md` - Step-by-step setup guide
3. `docs/ARCHITECTURE.md` - Detailed system architecture
4. `docs/API.md` - API reference for all components
5. `docs/DEPLOYMENT.md` - Production deployment guide
6. `docs/TROUBLESHOOTING.md` - Common issues and solutions
7. `docs/CONTRIBUTING.md` - Development guidelines

**Technical Documentation:**
8. `docs/CAS-REGISTRY.md` - Content-addressed storage guide
9. `docs/PLANNER.md` - Constraint solver documentation
10. `docs/FABRIC.md` - Lane types and performance
11. `docs/MCP-INTEGRATION.md` - MCP bridge usage
12. `docs/SECURITY.md` - Signing, capabilities, sandboxing

### 9.2 Runnable Examples

**Example Scenarios:**
1. Basic routing (agent → tool → service)
2. MCP integration (Claude tools via RTT)
3. Multi-provider routing (Claude + OpenAI simultaneously)
4. Chaos testing (simulate failures)
5. Performance tuning (autotune workflow)

**Example Locations:**
- `examples/01-basic-routing/`
- `examples/02-mcp-integration/`
- `examples/03-multi-provider/`
- `examples/04-chaos-testing/`
- `examples/05-performance-tuning/`

### 9.3 Production Readiness Checklist

**Pre-Production:**
- [ ] Security hardening guide reviewed
- [ ] Monitoring setup (flight recorder → APM)
- [ ] Backup strategy for WAL and CAS
- [ ] Systemd service configured and tested
- [ ] Resource limits tuned (CPU, memory, file descriptors)
- [ ] Network policies configured (if applicable)

**Production Deployment:**
- [ ] Deploy to staging environment first
- [ ] Run smoke tests on staging
- [ ] Execute chaos tests on staging
- [ ] Monitor metrics for 24+ hours
- [ ] Document any platform-specific issues
- [ ] Prepare rollback plan

**Operational:**
- [ ] On-call runbook created
- [ ] Alerting thresholds configured
- [ ] Log aggregation set up
- [ ] Incident response plan documented
- [ ] Regular backup schedule established
- [ ] Update/patch strategy defined

### 9.4 Future Enhancements

**Short-Term (Next Sprint):**
- Implement full FUSE/WinFsp VFS daemon
- Complete SHM ring implementation (replace stubs)
- Add TLA+ formal specification
- Implement full autotune with real trace data
- Expand chaos test coverage

**Medium-Term (Next Quarter):**
- Add support for remote MCP servers (WebRTC/QUIC)
- Implement advanced schedulers (EDF, CBS, WFQ)
- Add NUMA thread pinning
- Create web-based management UI
- Build metrics dashboard

**Long-Term (Next Year):**
- Support for distributed RTT (multi-node)
- Advanced placement with machine learning
- Cross-platform VFS (Windows native)
- Plugin marketplace for connectors
- Enterprise features (RBAC, audit trails)

---

## 10. Conclusion

This RSD plan provides a comprehensive, phase-by-phase approach to integrating all 12 RTT dropin archives into a production-ready system. Key highlights:

✅ **Completeness** - All dropins mapped to correct locations
✅ **Safety** - Background agents verify without blocking
✅ **Determinism** - Sequential phases with clear dependencies
✅ **Quality** - Continuous testing and validation
✅ **Documentation** - Comprehensive guides for all stakeholders
✅ **Production-Ready** - Meets all P0 and P1 acceptance criteria

**Final Deliverable:** A fully functional, deterministic, secure, and observable relay terminal tool that enables zero-duplication multi-agent, multi-provider orchestration with hot-swappable routing, signed plans, and content-addressed storage.

---

## Appendix A: Dropin Archive Details

See [docs/DROPIN-MAPPING.md](./DROPIN-MAPPING.md) for detailed file-by-file mapping.

## Appendix B: Agent Coordination Details

See [docs/AGENT-COORDINATION.md](./AGENT-COORDINATION.md) for agent responsibilities and protocols.

## Appendix C: Acceptance Criteria Details

See [docs/ACCEPTANCE-CRITERIA.md](./ACCEPTANCE-CRITERIA.md) for complete validation checklists.

## Appendix D: Phase Execution Guide

See [docs/PHASE-GUIDE.md](./PHASE-GUIDE.md) for detailed phase-by-phase instructions.

## Appendix E: Architecture Overview

See [docs/ARCHITECTURE.md](./ARCHITECTURE.md) for system architecture diagrams and explanations.

---

**Document Version:** 1.0
**Last Updated:** 2025-10-27
**Status:** Approved - Ready for Execution
**Next Action:** Begin Phase 1 extraction and integration
