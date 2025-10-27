# RTT Dropin Archive Mapping Reference

**Purpose:** Complete file-by-file mapping of where each dropin archive component belongs in the project structure
**Audience:** Integration engineers, automation scripts, verification tools
**Last Updated:** 2025-10-27

---

## Overview

This document provides the definitive mapping of all 12 dropin archives to their final locations in the RTT project structure. Use this as a reference during integration to ensure files are placed correctly and to verify nothing is missing.

**Total Archives:** 12
**Total Estimated Files:** ~500+ files across all dropins
**Conflicts:** 0 expected (non-overlapping structures)

---

## Quick Lookup Table

| Phase | Archive | Key Directories Created | Files Added |
|-------|---------|------------------------|-------------|
| 1 | rtt_dropin.zip | .rtt/, schemas/, tests/ | ~25 |
| 2 | cas_vfs_starter.zip | .rtt/registry/, agents/, overlays/, views/, providers/, tools/ | ~35 |
| 3 | rtt_signed_plans_starter.zip | tools/, plans/, security/ | ~10 |
| 4 | rtt_solver_constraints.zip | planner/, tools/ (updates) | ~5 |
| 5 | rtt_placement_churn.zip | placement/, .rtt/topology.json | ~5 |
| 6 | rtt_exact_admission.zip | tools/ilp/ | ~3 |
| 7 | rtt_elite_addon.zip | auto/, cue/, spec/, telemetry/, chaos/, systemd/, agent/, llama/, autotune/ | ~25 |
| 8 | rtt_mcp_ingest_signed_plans.zip | tools/ (updates), connector-mcp/, mcp/ | ~10 |
| 9 | rtt_next_upgrades.zip | viewfs/, fabric/, drivers/, tools/ (Rust/Go), configs (package.json, Cargo.toml, go.mod) | ~100+ |
| 10 | universal_stubs.zip | stubs/ | ~200+ |
| 11 | rtt_mcp_dropin.zip | mcp/ (provider configs) | ~10 |
| 12 | mcp_opt_shims_bundle.zip | mcp/opt-shims/ | ~5 |

---

## Phase 1: rtt_dropin.zip

**Source Archive:** `rtt/dropin/rtt_dropin.zip`
**Size:** ~10KB
**Purpose:** Foundation layer - base .rtt structure, schemas, tests

### File Mapping

```
rtt_dropin/                                     →  Project Root
├── .rtt/                                       →  .rtt/
│   ├── panel.yaml                              →  .rtt/panel.yaml
│   ├── policy.json                             →  .rtt/policy.json
│   ├── routes.json                             →  .rtt/routes.json
│   ├── manifests/                              →  .rtt/manifests/
│   │   ├── core.api.metrics.json               →  .rtt/manifests/core.api.metrics.json
│   │   ├── core.bus.events.json                →  .rtt/manifests/core.bus.events.json
│   │   ├── idp.api.auth.json                   →  .rtt/manifests/idp.api.auth.json
│   │   ├── obs.extension.logger.ndjson.json    →  .rtt/manifests/obs.extension.logger.ndjson.json
│   │   └── ui.hook.refresh.json                →  .rtt/manifests/ui.hook.refresh.json
│   ├── drivers/                                →  .rtt/drivers/
│   │   └── README_DRIVERS.md                   →  .rtt/drivers/README_DRIVERS.md
│   ├── cache/                                  →  .rtt/cache/
│   │   └── .keep                               →  .rtt/cache/.keep
│   ├── wal/                                    →  .rtt/wal/
│   │   └── .keep                               →  .rtt/wal/.keep
│   └── sockets/                                →  .rtt/sockets/
│       └── .keep                               →  .rtt/sockets/.keep
├── schemas/                                    →  schemas/
│   ├── rtt.symbol.schema.json                  →  schemas/rtt.symbol.schema.json
│   ├── rtt.policy.schema.json                  →  schemas/rtt.policy.schema.json
│   └── rtt.routes.schema.json                  →  schemas/rtt.routes.schema.json
├── tests/                                      →  tests/
│   └── validate.py                             →  tests/validate.py
└── README.md                                   →  README-rtt-dropin.md (renamed to avoid conflict)
```

### Key Files Description

- **panel.yaml**: Panel configuration (API listen, scan roots, routing preferences)
- **policy.json**: ACL, QoS, pinning, failover rules
- **routes.json**: Desired route state
- **manifests/**: 5 sample symbol manifests with contracts
- **schemas/**: JSON schemas for validation
- **validate.py**: Offline validation script

---

## Phase 2: cas_vfs_starter.zip

**Source Archive:** `rtt/dropin/cas_vfs_starter.zip`
**Size:** ~15KB
**Purpose:** CAS registry, view engine, content-addressed storage

### File Mapping

```
cas_vfs_starter/                                →  Project Root
├── .rtt/                                       →  .rtt/ (merges with Phase 1)
│   ├── registry/                               →  .rtt/registry/
│   │   ├── cas/                                →  .rtt/registry/cas/
│   │   │   └── sha256/                         →  .rtt/registry/cas/sha256/
│   │   │       ├── bcbe05d6...45c90.json       →  .rtt/registry/cas/sha256/bcbe05d6...45c90.json
│   │   │       ├── f073d791...e0b2e.json       →  .rtt/registry/cas/sha256/f073d791...e0b2e.json
│   │   │       └── 997752be...301373.json      →  .rtt/registry/cas/sha256/997752be...301373.json
│   │   ├── pack/                               →  .rtt/registry/pack/
│   │   │   ├── agents.pack                     →  .rtt/registry/pack/agents.pack (generated)
│   │   │   └── index.lut                       →  .rtt/registry/pack/index.lut (generated)
│   │   ├── trust/                              →  .rtt/registry/trust/
│   │   │   └── keys/                           →  .rtt/registry/trust/keys/
│   │   │       └── dev-ed25519.pub             →  .rtt/registry/trust/keys/dev-ed25519.pub
│   │   ├── index.json                          →  .rtt/registry/index.json
│   │   └── manifests/                          →  .rtt/manifests/ (merges)
├── agents/                                     →  agents/
│   └── common/                                 →  agents/common/
│       ├── summarize.agent.json                →  agents/common/summarize.agent.json
│       ├── search.agent.json                   →  agents/common/search.agent.json
│       └── code_fix.agent.json                 →  agents/common/code_fix.agent.json
├── overlays/                                   →  overlays/
│   ├── provider/                               →  overlays/provider/
│   │   └── claude/                             →  overlays/provider/claude/
│   │       └── summarize.patch.json            →  overlays/provider/claude/summarize.patch.json
│   └── env/                                    →  overlays/env/
│       └── prod/                               →  overlays/env/prod/
│           └── _global.patch.json              →  overlays/env/prod/_global.patch.json
├── views/                                      →  views/
│   └── claude.view.json                        →  views/claude.view.json
├── providers/                                  →  providers/
│   └── claude/                                 →  providers/claude/
│       └── .claude/                            →  providers/claude/.claude/
│           └── agents/                         →  providers/claude/.claude/agents/
├── tools/                                      →  tools/
│   ├── apply_overlay.py                        →  tools/apply_overlay.py
│   ├── cas_ingest.py                           →  tools/cas_ingest.py
│   ├── cas_pack.py                             →  tools/cas_pack.py
│   ├── view_materialize.py                     →  tools/view_materialize.py
│   └── view_to_rtt.py                          →  tools/view_to_rtt.py
└── viewfs/                                     →  viewfs/
    └── README.md                               →  viewfs/README.md (initial)
```

### Key Files Description

- **CAS registry**: Content-addressed storage with SHA256 hashing
- **Packfile**: Memory-mapped file for zero-copy reads
- **Index**: ID@version → SHA256 mapping
- **Trust keys**: Public keys for signature verification
- **Canonical agents**: Single source of truth for agents
- **Overlays**: Provider and environment-specific patches
- **View engine**: Tools to materialize views from CAS + overlays

---

## Phase 3: rtt_signed_plans_starter.zip

**Source Archive:** `rtt/dropin/rtt_signed_plans_starter.zip`
**Size:** ~8KB
**Purpose:** Ed25519 signing, plan generation, verification

### File Mapping

```
rtt_signed_plans_starter/                       →  Project Root
├── tools/                                      →  tools/ (merges)
│   ├── ed25519_helper.py                       →  tools/ed25519_helper.py
│   ├── keys_ed25519.py                         →  tools/keys_ed25519.py
│   ├── sign_view.py                            →  tools/sign_view.py
│   ├── verify_view.py                          →  tools/verify_view.py
│   ├── plan_build.py                           →  tools/plan_build.py
│   └── plan_verify.py                          →  tools/plan_verify.py
├── plans/                                      →  plans/
│   └── (generated at runtime)                  →  plans/*.plan.json (runtime)
├── .rtt/registry/keys/                         →  .rtt/registry/keys/
│   └── private/                                →  .rtt/registry/keys/private/ (created, not populated)
└── security/                                   →  security/
    └── caps.schema.json                        →  security/caps.schema.json (from docs)
```

### Key Files Description

- **ed25519_helper.py**: PyNaCl wrapper with fallback
- **keys_ed25519.py**: Key generation (gen, export)
- **plan_build.py**: Deterministic plan builder with signing
- **plan_verify.py**: Plan signature verification
- **plans/**: Directory for signed plans (*.plan.json)
- **private/**: Private key storage (NOT committed to git)

---

## Phase 4: rtt_solver_constraints.zip

**Source Archive:** `rtt/dropin/rtt_solver_constraints.zip`
**Size:** ~12KB
**Purpose:** Constraint solver, version meet, QoS checks

### File Mapping

```
rtt_solver_constraints/                         →  Project Root
├── planner/                                    →  planner/
│   ├── constraints.py                          →  planner/constraints.py
│   └── solver.py                               →  planner/solver.py
└── tools/                                      →  tools/ (updates)
    └── plan_build.py (updated)                 →  tools/plan_build.py (merged/updated)
```

### Key Files Description

- **constraints.py**: Constraint definitions (version meet, QoS, ACL)
- **solver.py**: Greedy constraint solver
- **plan_build.py**: Enhanced with constraint validation

---

## Phase 5: rtt_placement_churn.zip

**Source Archive:** `rtt/dropin/rtt_placement_churn.zip`
**Size:** ~10KB
**Purpose:** NUMA placement, churn minimization

### File Mapping

```
rtt_placement_churn/                            →  Project Root
├── placement/                                  →  placement/
│   └── numa/                                   →  placement/numa/
│       ├── topology.py                         →  placement/numa/topology.py
│       ├── packing.py                          →  placement/numa/packing.py
│       └── optimizer.py                        →  placement/numa/optimizer.py
├── planner/                                    →  planner/ (merges)
│   └── placement.py                            →  planner/placement.py
├── .rtt/                                       →  .rtt/
│   └── topology.json                           →  .rtt/topology.json
└── tools/                                      →  tools/ (updates)
    └── plan_build.py (updated)                 →  tools/plan_build.py (merged/updated)
```

### Key Files Description

- **topology.py**: NUMA domain detection
- **packing.py**: Capacity-aware symbol packing
- **optimizer.py**: Local search with churn weighting
- **placement.py**: Integration module for planner
- **topology.json**: Node capacity definitions

---

## Phase 6: rtt_exact_admission.zip

**Source Archive:** `rtt/dropin/rtt_exact_admission.zip`
**Size:** ~8KB
**Purpose:** ILP solver for exact optimization

### File Mapping

```
rtt_exact_admission/                            →  Project Root
└── tools/                                      →  tools/
    └── ilp/                                    →  tools/ilp/
        └── plan_build_ilp.py                   →  tools/ilp/plan_build_ilp.py
```

### Key Files Description

- **plan_build_ilp.py**: ILP solver using PuLP (binary placement, admission control)

---

## Phase 7: rtt_elite_addon.zip

**Source Archive:** `rtt/dropin/rtt_elite_addon.zip`
**Size:** ~15KB
**Purpose:** Automation pipeline, telemetry, chaos, systemd

### File Mapping

```
rtt_elite_addon/                                →  Project Root
├── auto/                                       →  auto/
│   ├── 00-bootstrap.py                         →  auto/00-bootstrap.py
│   ├── 10-scan_symbols.py                      →  auto/10-scan_symbols.py
│   ├── 20-depdoctor.py                         →  auto/20-depdoctor.py
│   ├── 30-generate_connectors.py               →  auto/30-generate_connectors.py
│   ├── 40-plan_solver.py                       →  auto/40-plan_solver.py
│   └── 50-apply_plan.py                        →  auto/50-apply_plan.py
├── cue/                                        →  cue/
│   └── panel.cue                               →  cue/panel.cue
├── spec/                                       →  spec/
│   ├── invariants.md                           →  spec/invariants.md
│   └── tla/                                    →  spec/tla/ (placeholder)
├── telemetry/                                  →  telemetry/
│   └── flight_recorder/                        →  telemetry/flight_recorder/
│       └── flight.py                           →  telemetry/flight_recorder/flight.py
├── chaos/                                      →  chaos/
│   └── cases.yaml                              →  chaos/cases.yaml
├── systemd/                                    →  systemd/
│   └── rtt-panel.service                       →  systemd/rtt-panel.service
├── agent/                                      →  agent/
│   └── agent_bus.py                            →  agent/agent_bus.py
├── llama/                                      →  llama/
│   ├── README.md                               →  llama/README.md
│   └── call_llama.py                           →  llama/call_llama.py
├── autotune/                                   →  autotune/ (created, placeholder)
└── .rtt/tuned/                                 →  .rtt/tuned/ (created)
    └── profile.json                            →  .rtt/tuned/profile.json (template)
```

### Key Files Description

- **auto/00-50**: Full automation pipeline (bootstrap → apply)
- **cue/panel.cue**: Typed config schema
- **spec/invariants.md**: Runtime invariant definitions
- **flight.py**: Flight recorder for telemetry
- **cases.yaml**: Chaos test scenarios
- **rtt-panel.service**: Systemd service definition
- **agent_bus.py**: Local UDS pub/sub for agents
- **call_llama.py**: Optional LLM integration

---

## Phase 8: rtt_mcp_ingest_signed_plans.zip

**Source Archive:** `rtt/dropin/rtt_mcp_ingest_signed_plans.zip`
**Size:** ~12KB
**Purpose:** MCP integration, tool ingestion, autowire

### File Mapping

```
rtt_mcp_ingest_signed_plans/                    →  Project Root
├── tools/                                      →  tools/ (merges)
│   ├── mcp_ingest.py                           →  tools/mcp_ingest.py
│   ├── agents_ingest.py                        →  tools/agents_ingest.py
│   ├── skills_ingest.py                        →  tools/skills_ingest.py
│   ├── invariants_check.py                     →  tools/invariants_check.py
│   └── plan_build.py (updated with --autowire) →  tools/plan_build.py (merged/updated)
├── connector-mcp/                              →  connector-mcp/
│   ├── bridge.py                               →  connector-mcp/bridge.py
│   └── config/                                 →  connector-mcp/config/
└── mcp/                                        →  mcp/
    ├── claude/                                 →  mcp/claude/ (created)
    ├── openai/                                 →  mcp/openai/ (created)
    ├── mistral/                                →  mcp/mistral/ (created)
    └── shared/                                 →  mcp/shared/ (created)
```

### Key Files Description

- **mcp_ingest.py**: MCP tools.json → CAS + RTT manifests
- **agents_ingest.py**: Agents → CAS
- **skills_ingest.py**: Skills → CAS
- **invariants_check.py**: Pre-sign safety gates
- **bridge.py**: MCP-RTT connector bridge

---

## Phase 9: rtt_next_upgrades.zip

**Source Archive:** `rtt/dropin/rtt_next_upgrades.zip`
**Size:** ~50KB
**Purpose:** Production Rust/Go/Node components

### File Mapping

```
rtt_next_upgrades/                              →  Project Root
├── viewfs/                                     →  viewfs/ (merges)
│   ├── rust-fuse/                              →  viewfs/rust-fuse/
│   │   ├── Cargo.toml                          →  viewfs/rust-fuse/Cargo.toml
│   │   ├── src/                                →  viewfs/rust-fuse/src/
│   │   │   └── main.rs                         →  viewfs/rust-fuse/src/main.rs
│   └── windows/                                →  viewfs/windows/
│       └── README.md                           →  viewfs/windows/README.md
├── tools/                                      →  tools/ (merges)
│   ├── rtt_sign_rs/                            →  tools/rtt_sign_rs/
│   │   ├── Cargo.toml                          →  tools/rtt_sign_rs/Cargo.toml
│   │   ├── src/                                →  tools/rtt_sign_rs/src/
│   │   │   └── main.rs                         →  tools/rtt_sign_rs/src/main.rs
│   └── rtt_sign_go/                            →  tools/rtt_sign_go/
│       ├── go.mod                              →  tools/rtt_sign_go/go.mod
│       └── main.go                             →  tools/rtt_sign_go/main.go
├── planner/                                    →  planner/ (merges)
│   └── rtt_planner_rs/                         →  planner/rtt_planner_rs/
│       ├── Cargo.toml                          →  planner/rtt_planner_rs/Cargo.toml
│       └── src/                                →  planner/rtt_planner_rs/src/
│           └── main.rs                         →  planner/rtt_planner_rs/src/main.rs
├── fabric/                                     →  fabric/
│   ├── shm/                                    →  fabric/shm/
│   │   ├── Cargo.toml                          →  fabric/shm/Cargo.toml
│   │   ├── src/                                →  fabric/shm/src/
│   │   │   └── lib.rs                          →  fabric/shm/src/lib.rs
│   ├── uds/                                    →  fabric/uds/
│   └── tcp/                                    →  fabric/tcp/
├── drivers/                                    →  drivers/
│   ├── rust/                                   →  drivers/rust/
│   ├── python/                                 →  drivers/python/
│   ├── go/                                     →  drivers/go/
│   ├── node/                                   →  drivers/node/
│   └── README.md                               →  drivers/README.md
├── package.json                                →  package.json
├── pnpm-workspace.yaml                         →  pnpm-workspace.yaml
├── .npmrc                                      →  .npmrc
├── .pnpmfile.cjs                               →  .pnpmfile.cjs
├── tsconfig.json                               →  tsconfig.json
├── Cargo.toml                                  →  Cargo.toml (workspace)
└── go.mod                                      →  go.mod
```

### Key Files Description

- **viewfs/rust-fuse**: FUSE VFS daemon (Linux/macOS)
- **rtt_sign_rs**: Rust signing CLI
- **rtt_sign_go**: Go signing CLI
- **rtt_planner_rs**: Rust constraint planner
- **fabric/shm**: SHM SPSC ring (Rust crate)
- **drivers/***: Multi-language driver SDKs
- **package.json, Cargo.toml, go.mod**: Build configs

---

## Phase 10: universal_stubs.zip

**Source Archive:** `rtt/dropin/universal_stubs.zip`
**Size:** ~100KB
**Purpose:** 25+ language connector stubs

### File Mapping

```
universal_stubs/                                →  Project Root
└── stubs/                                      →  stubs/
    ├── python/                                 →  stubs/python/
    ├── node/                                   →  stubs/node/
    ├── typescript/                             →  stubs/typescript/
    ├── bash/                                   →  stubs/bash/
    ├── powershell/                             →  stubs/powershell/
    ├── ruby/                                   →  stubs/ruby/
    ├── php/                                    →  stubs/php/
    ├── perl/                                   →  stubs/perl/
    ├── lua/                                    →  stubs/lua/
    ├── go/                                     →  stubs/go/
    ├── rust/                                   →  stubs/rust/
    ├── java/                                   →  stubs/java/
    ├── c/                                      →  stubs/c/
    ├── cpp/                                    →  stubs/cpp/
    ├── csharp/                                 →  stubs/csharp/
    ├── swift/                                  →  stubs/swift/
    ├── kotlin/                                 →  stubs/kotlin/
    ├── dart/                                   →  stubs/dart/
    ├── julia/                                  →  stubs/julia/
    ├── haskell/                                →  stubs/haskell/
    ├── ocaml/                                  →  stubs/ocaml/
    ├── clojure/                                →  stubs/clojure/
    ├── groovy/                                 →  stubs/groovy/
    ├── r/                                      →  stubs/r/
    ├── pascal/                                 →  stubs/pascal/
    ├── [20+ more placeholders...]              →  stubs/[language]/
    └── README.md                               →  stubs/README.md
```

### Key Files Description

- **25+ runnable stubs**: Full connector implementations
- **20+ placeholder stubs**: Documentation with protocol
- **README.md**: Universal JSON-over-stdio protocol

---

## Phase 11a: rtt_mcp_dropin.zip

**Source Archive:** `rtt/dropin/rtt_mcp_dropin.zip`
**Size:** ~8KB
**Purpose:** MCP provider configurations

### File Mapping

```
rtt_mcp_dropin/                                 →  Project Root
├── mcp/                                        →  mcp/ (merges)
│   ├── claude/                                 →  mcp/claude/
│   │   └── tools.json                          →  mcp/claude/tools.json
│   ├── openai/                                 →  mcp/openai/
│   │   └── tools.json                          →  mcp/openai/tools.json
│   └── mistral/                                →  mcp/mistral/
│       └── tools.json                          →  mcp/mistral/tools.json
└── connector-mcp/                              →  connector-mcp/ (merges)
    └── (additional configs)                    →  connector-mcp/
```

---

## Phase 11b: mcp_opt_shims_bundle.zip

**Source Archive:** `rtt/dropin/mcp_opt_shims_bundle.zip`
**Size:** ~10KB
**Purpose:** MCP performance optimizations

### File Mapping

```
mcp_opt_shims_bundle/                           →  Project Root
└── mcp/                                        →  mcp/ (merges)
    └── opt-shims/                              →  mcp/opt-shims/
        ├── batching.py                         →  mcp/opt-shims/batching.py
        ├── pooling.py                          →  mcp/opt-shims/pooling.py
        ├── caching.py                          →  mcp/opt-shims/caching.py
        └── README.md                           →  mcp/opt-shims/README.md
```

---

## Complete Project Structure

After all 12 phases, the final project structure:

```
/home/deflex/rtt/rtt-v1/
├── .rtt/                           # Runtime configuration
│   ├── panel.yaml
│   ├── policy.json
│   ├── routes.json
│   ├── topology.json
│   ├── manifests/
│   ├── drivers/
│   ├── cache/
│   ├── wal/
│   ├── sockets/
│   ├── registry/
│   │   ├── cas/sha256/
│   │   ├── pack/
│   │   ├── trust/keys/
│   │   ├── keys/private/
│   │   └── index.json
│   └── tuned/
├── agents/                         # Canonical agents
│   └── common/
├── auto/                           # Automation pipeline
│   ├── 00-bootstrap.py
│   ├── 10-scan_symbols.py
│   ├── 20-depdoctor.py
│   ├── 30-generate_connectors.py
│   ├── 40-plan_solver.py
│   └── 50-apply_plan.py
├── agent/                          # Agent coordination
│   └── agent_bus.py
├── autotune/                       # Tuning framework
├── chaos/                          # Chaos testing
│   └── cases.yaml
├── connector-mcp/                  # MCP bridge
│   ├── bridge.py
│   └── config/
├── cue/                            # Typed configs
│   └── panel.cue
├── docs/                           # Documentation
│   ├── RSD-PLAN.md
│   ├── PHASE-GUIDE.md
│   ├── DROPIN-MAPPING.md
│   ├── AGENT-COORDINATION.md
│   ├── ACCEPTANCE-CRITERIA.md
│   └── ARCHITECTURE.md
├── drivers/                        # Driver SDKs
│   ├── rust/
│   ├── python/
│   ├── go/
│   ├── node/
│   └── README.md
├── fabric/                         # Lanes
│   ├── shm/
│   ├── uds/
│   └── tcp/
├── llama/                          # LLM integration
│   ├── call_llama.py
│   └── README.md
├── mcp/                            # MCP tools
│   ├── claude/
│   ├── openai/
│   ├── mistral/
│   ├── shared/
│   └── opt-shims/
├── overlays/                       # Overlays
│   ├── provider/
│   └── env/
├── placement/                      # NUMA placement
│   └── numa/
├── planner/                        # Constraint solver
│   ├── constraints.py
│   ├── solver.py
│   ├── placement.py
│   └── rtt_planner_rs/
├── plans/                          # Signed plans
├── providers/                      # Provider views
│   └── claude/.claude/agents/
├── rtt/                            # Original dropins
│   └── dropin/*.zip
├── schemas/                        # JSON schemas
├── security/                       # Security
│   └── caps.schema.json
├── spec/                           # Formal spec
│   ├── invariants.md
│   └── tla/
├── stubs/                          # Language stubs
│   ├── python/
│   ├── node/
│   ├── [23+ more...]
│   └── README.md
├── systemd/                        # Systemd service
│   └── rtt-panel.service
├── telemetry/                      # Observability
│   └── flight_recorder/
├── tests/                          # Tests
│   └── validate.py
├── tools/                          # Tooling
│   ├── ed25519_helper.py
│   ├── keys_ed25519.py
│   ├── sign_view.py
│   ├── verify_view.py
│   ├── plan_build.py
│   ├── plan_verify.py
│   ├── cas_ingest.py
│   ├── cas_pack.py
│   ├── view_materialize.py
│   ├── view_to_rtt.py
│   ├── mcp_ingest.py
│   ├── agents_ingest.py
│   ├── skills_ingest.py
│   ├── invariants_check.py
│   ├── ilp/
│   ├── rtt_sign_rs/
│   └── rtt_sign_go/
├── viewfs/                         # VFS daemon
│   ├── rust-fuse/
│   └── windows/
├── views/                          # View definitions
├── package.json                    # Node config
├── pnpm-workspace.yaml             # PNPM workspace
├── .npmrc                          # NPM config
├── tsconfig.json                   # TypeScript config
├── Cargo.toml                      # Rust workspace
├── go.mod                          # Go module
├── .gitignore                      # Git ignore
├── LICENSE                         # License
├── README.md                       # Main README
└── SBOM.json                       # Bill of materials
```

---

## Conflict Detection

### Potential Overlaps (Resolved)

| File | Phase 1 | Phase 2+ | Resolution |
|------|---------|----------|------------|
| tools/plan_build.py | - | Created P3, Updated P4,P5,P8 | Merge updates |
| .rtt/manifests/ | Created P1 | Used P2+ | Merge manifests |
| viewfs/README.md | - | Created P2, Expanded P9 | Merge content |
| README.md | Dropin P1 | Project root | Rename dropin to README-rtt-dropin.md |

### Files NOT to Commit

```
.rtt/registry/keys/private/       # Private keys (security)
.rtt/cache/*                      # Runtime cache
.rtt/wal/*                        # Runtime WAL
.rtt/sockets/*                    # Runtime sockets
target/                           # Rust build artifacts
node_modules/                     # Node dependencies
*.pyc                             # Python bytecode
__pycache__/                      # Python cache
.DS_Store                         # macOS metadata
```

### .gitignore Recommendations

```gitignore
# Private keys
.rtt/registry/keys/private/

# Runtime directories
.rtt/cache/*
.rtt/wal/*
.rtt/sockets/*
!.rtt/cache/.keep
!.rtt/wal/.keep
!.rtt/sockets/.keep

# Build artifacts
target/
node_modules/
dist/
build/

# Language-specific
*.pyc
__pycache__/
*.so
*.dylib
*.dll
*.exe

# OS-specific
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
```

---

## Verification Checklist

After integration, verify:

### File Counts

```bash
# Expected counts
find .rtt -type f | wc -l        # ~15-20 files
find agents -type f | wc -l      # ~3 files
find auto -type f | wc -l        # ~6 files
find docs -type f | wc -l        # ~6 files
find drivers -type d | wc -l     # ~4 directories
find mcp -type f | wc -l         # ~10-15 files
find planner -type f | wc -l     # ~5-10 files
find stubs -type d | wc -l       # ~25+ directories
find tools -type f -name "*.py" | wc -l  # ~15-20 Python tools
```

### Directory Structure

```bash
# Verify key directories exist
for dir in .rtt agents auto chaos connector-mcp cue docs drivers fabric llama mcp overlays placement planner plans providers schemas security spec stubs systemd telemetry tests tools viewfs views; do
  [ -d "$dir" ] && echo "✓ $dir" || echo "✗ $dir MISSING"
done
```

### No Conflicts

```bash
# Verify no git conflicts
git status | grep -i "conflict" && echo "CONFLICTS DETECTED" || echo "✓ No conflicts"

# Verify no deleted files
git log --diff-filter=D --summary | grep delete && echo "DELETIONS DETECTED" || echo "✓ No deletions"
```

---

## Quick Reference Commands

### Find Dropin Source for a File

```bash
# Example: Where did cas_ingest.py come from?
grep -r "cas_ingest.py" docs/DROPIN-MAPPING.md
# Answer: Phase 2 - cas_vfs_starter.zip
```

### Verify File Placement

```bash
# Example: Verify panel.yaml in correct location
test -f .rtt/panel.yaml && echo "✓ Correct" || echo "✗ Wrong location"
```

### List All Files from a Phase

```bash
# Example: List all files from Phase 7
awk '/^## Phase 7/,/^## Phase [8-9]/' docs/DROPIN-MAPPING.md | grep "→"
```

---

**End of Dropin Mapping Reference**

For detailed phase execution instructions, see [PHASE-GUIDE.md](./PHASE-GUIDE.md)
For overall plan, see [RSD-PLAN.md](./RSD-PLAN.md)
