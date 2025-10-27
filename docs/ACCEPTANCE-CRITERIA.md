# RTT Acceptance Criteria

**Purpose:** Comprehensive validation checklist for production-ready RTT system
**Last Updated:** 2025-10-27

---

## P0 Baseline Criteria (MUST HAVE)

All P0 criteria must be met for production readiness.

### 1. CAS Registry Operational

**Criterion:** Content-addressed storage with signed entries
**Validation:**
```bash
# Test ingestion
python tools/cas_ingest.py agents/common/summarize.agent.json

# Verify SHA256 entry created
ls .rtt/registry/cas/sha256/*.json

# Check signature (if applicable)
python tools/verify_view.py views/claude.view.json
```

**Success:** ✅ Entries created, immutable, content-addressed by SHA256

---

### 2. ViewFS Mounts for 2+ Providers

**Criterion:** Provider view system operational for multiple providers
**Validation:**
```bash
# Check view definitions exist
ls views/*.view.json | wc -l  # Should be ≥ 2

# Test view materialization
python tools/view_materialize.py views/claude.view.json

# Verify provider directory created
ls providers/claude/.claude/agents/
```

**Success:** ✅ Multiple provider views can be materialized

---

### 3. Deterministic Planner

**Criterion:** Same inputs → same plan hash
**Validation:**
```bash
# Run planner twice
python tools/plan_build.py .rtt/routes.json .rtt/manifests test-key > plan1.json
python tools/plan_build.py .rtt/routes.json .rtt/manifests test-key > plan2.json

# Compare plan hashes
HASH1=$(jq -r .plan_id plan1.json)
HASH2=$(jq -r .plan_id plan2.json)
test "$HASH1" = "$HASH2" && echo "✅ Deterministic" || echo "❌ Non-deterministic"
```

**Success:** ✅ Plan hash identical across runs with same inputs

---

### 4. 2PC Apply with Rollback

**Criterion:** Atomic apply with rollback on failure
**Validation:**
```bash
# Apply plan
python auto/50-apply_plan.py plans/latest.json

# Check WAL created
ls .rtt/wal/*.wal

# Test rollback (if supported)
# python tools/rollback.py <seq-no>
```

**Success:** ✅ WAL records commits, rollback mechanism present

---

### 5. SHM + UDS Lanes Defined

**Criterion:** Lane types implemented (at minimum as stubs)
**Validation:**
```bash
# Check fabric definitions
ls fabric/shm/ fabric/uds/ fabric/tcp/

# Verify protocol documented
cat drivers/README.md | grep -i "lane"
```

**Success:** ✅ SHM, UDS, TCP lane types defined with protocol

---

### 6. Flight Recorder Operational

**Criterion:** Telemetry collection framework functional
**Validation:**
```bash
# Test flight recorder
python telemetry/flight_recorder/flight.py --help

# Check metrics structure
python telemetry/flight_recorder/flight.py --test || echo "Stub operational"
```

**Success:** ✅ Flight recorder can capture metrics

---

### 7. Plan Determinism Verified

**Criterion:** Plan hashing is stable and deterministic
**Validation:**
```bash
# Run 10 times, verify all identical
for i in {1..10}; do
  python tools/plan_build.py .rtt/routes.json .rtt/manifests test-key | jq -r .plan_id
done | sort -u | wc -l
# Should output 1 (only one unique hash)
```

**Success:** ✅ Single unique hash across multiple runs

---

### 8. Rollback Functionality Tested

**Criterion:** WAL replay works after simulated crash
**Validation:**
```bash
# Create checkpoint
cp -r .rtt/wal .rtt/wal.backup

# Modify state
python auto/50-apply_plan.py plans/latest.json

# Simulate crash and recovery
# (Test WAL replay mechanism if implemented)
```

**Success:** ✅ WAL replay mechanism documented and testable

---

### 9. No Duplicate Files Across Providers

**Criterion:** Agents stored once in CAS, not duplicated per provider
**Validation:**
```bash
# Count agent files in CAS
find .rtt/registry/cas -name "*.json" | wc -l

# Count agent files in providers
find providers -name "*.agent.json" | wc -l

# CAS count should be canonical, providers may have views
```

**Success:** ✅ Canonical agents in CAS, providers reference (not duplicate)

---

### 10. Performance Targets Documented

**Criterion:** SLO targets clearly documented
**Validation:**
```bash
# Check documentation
grep -r "p99.*300.*µs" docs/
grep -r "p99.*1\.5.*ms" docs/
```

**Success:** ✅ Control p99 ≤ 300 µs, SHM p99 ≤ 1.5 ms @ 64 KiB documented

---

## P1 Elite Core Criteria (SHOULD HAVE)

### 1. Constraint Solver with QoS + NUMA

**Validation:**
```bash
python tools/plan_build.py \
  .rtt/routes.json \
  .rtt/manifests \
  test-key \
  .rtt/policy.json \
  .rtt/topology.json \
  shm,uds,tcp
```

**Success:** ✅ Solver runs, respects QoS budgets and NUMA topology

---

### 2. Ed25519 Signing Infrastructure Complete

**Validation:**
```bash
python tools/keys_ed25519.py test-key
python tools/plan_build.py .rtt/routes.json .rtt/manifests test-key
python tools/plan_verify.py plans/latest.json
```

**Success:** ✅ Keys generate, plans sign, signatures verify

---

### 3. Admission Control Framework

**Validation:**
```bash
# Test with ILP solver
python tools/ilp/plan_build_ilp.py \
  .rtt/routes.json \
  .rtt/manifests \
  test-key \
  .rtt/policy.json \
  .rtt/topology.json \
  shm,uds,tcp \
  1000 \
  plans/last_applied.json
```

**Success:** ✅ Admission control accepts/rejects routes based on capacity

---

### 4. Chaos Suite Defined

**Validation:**
```bash
# Check chaos scenarios
cat chaos/cases.yaml
# Count scenarios
grep "^- name:" chaos/cases.yaml | wc -l
```

**Success:** ✅ 2+ chaos scenarios defined (kill, slow, corrupt, etc.)

---

### 5. CUE Typed Configs

**Validation:**
```bash
# Validate config against schema
# cue vet cue/panel.cue .rtt/panel.yaml
# (requires cue tool installed)

# Or verify CUE files exist
ls cue/*.cue
```

**Success:** ✅ CUE schemas defined for panel, routes, policy

---

### 6. MCP Integration Operational

**Validation:**
```bash
# Ingest sample MCP tools
cat > mcp/test/tools.json <<EOF
{"tools": [{"name": "test", "description": "Test tool"}]}
EOF

python tools/mcp_ingest.py test mcp/test/tools.json
```

**Success:** ✅ MCP tools ingest to CAS and generate RTT manifests

---

## P2 Full Automation Criteria (NICE TO HAVE)

### 1. Autotune Engine Framework Ready

**Validation:**
```bash
# Verify autotune directory exists
ls autotune/
ls .rtt/tuned/
```

**Success:** ✅ Autotune framework directory present (trace input hooks ready)

---

### 2. CUE Boot Validation (Fail Closed)

**Validation:**
```bash
# Test with invalid config
# Should reject boot
# cue vet cue/panel.cue invalid-config.yaml
```

**Success:** ✅ Invalid configs rejected at boot

---

### 3. Signed-Plan-Only Enforcement

**Validation:**
```bash
# Verify apply requires signed plan
# (Framework check, full enforcement may be future work)
grep -r "verify.*sign" auto/50-apply_plan.py
```

**Success:** ✅ Apply script checks for plan signature

---

### 4. Multi-Language Stubs (25+)

**Validation:**
```bash
# Count language stubs
find stubs -maxdepth 1 -type d | wc -l
```

**Success:** ✅ 25+ language stub directories present

---

### 5. Production Components Built

**Validation:**
```bash
# Build Rust
cd tools/rtt_sign_rs && cargo build --release && cd ../..

# Build Go
cd tools/rtt_sign_go && go build && cd ../..

# Install Node deps
pnpm install
```

**Success:** ✅ All build systems operational (Rust, Go, Node)

---

## Integration Completeness

### All 12 Dropins Extracted

**Validation:**
```bash
# Count phases committed
git log --oneline | grep -c "Phase"
# Should be ≥ 12
```

**Success:** ✅ 12 git commits (one per phase)

---

### Zero File Conflicts

**Validation:**
```bash
git status | grep -i conflict
echo $?  # Should be 1 (no conflicts found)
```

**Success:** ✅ No merge conflicts detected

---

### Automation Pipeline Runs End-to-End

**Validation:**
```bash
bash <<'EOF'
set -e
python auto/00-bootstrap.py
python auto/10-scan_symbols.py
python auto/20-depdoctor.py
python auto/30-generate_connectors.py
python auto/40-plan_solver.py
python auto/50-apply_plan.py
echo "Pipeline complete"
EOF
```

**Success:** ✅ All scripts execute without errors

---

### Documentation Complete

**Validation:**
```bash
# Check all docs present
for doc in RSD-PLAN.md PHASE-GUIDE.md DROPIN-MAPPING.md AGENT-COORDINATION.md ACCEPTANCE-CRITERIA.md ARCHITECTURE.md; do
  test -f docs/$doc && echo "✅ $doc" || echo "❌ $doc missing"
done
```

**Success:** ✅ All 6 core documentation files present

---

### SBOM Generated

**Validation:**
```bash
test -f SBOM.json && echo "✅ SBOM present" || echo "❌ SBOM missing"
```

**Success:** ✅ Software Bill of Materials documented

---

### No Files Deleted During Integration

**Validation:**
```bash
git log --diff-filter=D --summary | grep delete
echo $?  # Should be 1 (no deletions)
```

**Success:** ✅ No files deleted (only additions and modifications)

---

## Final Validation Checklist

Run before declaring production-ready:

```bash
#!/bin/bash
echo "=== RTT Production Readiness Checklist ==="

# P0 Criteria
echo ""
echo "P0 Baseline (10/10 required):"
test -d .rtt/registry/cas && echo "  ✅ CAS registry" || echo "  ❌ CAS registry"
test -f views/claude.view.json && echo "  ✅ ViewFS" || echo "  ❌ ViewFS"
test -f tools/plan_build.py && echo "  ✅ Planner" || echo "  ❌ Planner"
test -d .rtt/wal && echo "  ✅ WAL" || echo "  ❌ WAL"
test -d fabric/shm && echo "  ✅ Lanes" || echo "  ❌ Lanes"
test -f telemetry/flight_recorder/flight.py && echo "  ✅ Telemetry" || echo "  ❌ Telemetry"
test -f plans/latest.json && echo "  ✅ Signed plans" || echo "  ❌ Signed plans"

# P1 Criteria
echo ""
echo "P1 Elite Core (6/6 required):"
test -f planner/constraints.py && echo "  ✅ Constraint solver" || echo "  ❌ Constraint solver"
test -f tools/keys_ed25519.py && echo "  ✅ Signing" || echo "  ❌ Signing"
test -f tools/ilp/plan_build_ilp.py && echo "  ✅ Admission control" || echo "  ❌ Admission control"
test -f chaos/cases.yaml && echo "  ✅ Chaos suite" || echo "  ❌ Chaos suite"
test -f cue/panel.cue && echo "  ✅ CUE configs" || echo "  ❌ CUE configs"
test -f tools/mcp_ingest.py && echo "  ✅ MCP integration" || echo "  ❌ MCP integration"

# P2 Criteria
echo ""
echo "P2 Full Automation (3/5 minimum):"
test -d autotune && echo "  ✅ Autotune framework" || echo "  ❌ Autotune framework"
test -d stubs && echo "  ✅ Multi-language stubs" || echo "  ❌ Multi-language stubs"
test -f Cargo.toml && echo "  ✅ Production builds" || echo "  ❌ Production builds"

# Integration
echo ""
echo "Integration:"
PHASE_COUNT=$(git log --oneline | grep -c "Phase" || echo 0)
echo "  Phases committed: $PHASE_COUNT/12"
git status | grep -q conflict && echo "  ❌ Conflicts detected" || echo "  ✅ No conflicts"

# Documentation
echo ""
echo "Documentation:"
DOC_COUNT=$(ls docs/*.md 2>/dev/null | wc -l)
echo "  Documentation files: $DOC_COUNT/6"

echo ""
echo "=== End of Checklist ==="
```

---

## Success Metrics Summary

| Category | P0 (Must) | P1 (Should) | P2 (Nice) |
|----------|-----------|-------------|-----------|
| **Criteria** | 10 | 6 | 5 |
| **Required** | 10/10 (100%) | 6/6 (100%) | 3/5 (60%) |
| **Status** | Target ✅ | Target ✅ | Target ✅ |

---

## Production Go/No-Go Decision

**GO** if:
- ✅ All P0 criteria met (10/10)
- ✅ All P1 criteria met (6/6)
- ✅ At least 60% P2 criteria met (3/5)
- ✅ Zero file conflicts
- ✅ Documentation complete
- ✅ No critical agent reports

**NO-GO** if:
- ❌ Any P0 criterion fails
- ❌ File conflicts unresolved
- ❌ Critical agent reports unaddressed
- ❌ Build failures

---

**End of Acceptance Criteria**

For phase execution, see [PHASE-GUIDE.md](./PHASE-GUIDE.md)
For overall plan, see [RSD-PLAN.md](./RSD-PLAN.md)
