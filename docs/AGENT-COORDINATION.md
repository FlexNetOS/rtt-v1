# RTT Agent Coordination Strategy

**Purpose:** Background agent verification without blocking main execution
**Last Updated:** 2025-10-27

---

## Overview

Background agents run in parallel to **observe, verify, and report** without blocking main execution. They act as safety nets and quality gates, not gatekeepers.

**Key Principle:** Agents verify, don't block (unless critical failure detected)

---

## Agent Roster

### 1. Explore Agent
**Phases:** 1, 2, 10
**Purpose:** File structure verification and cataloging

**Responsibilities:**
- Verify extracted files match expected structure
- Detect file conflicts before they occur
- Catalog components for cross-reference
- Report missing dependencies

**Launch Trigger:** After file extraction, before git commit

**Outputs:**
- File structure report
- Conflict warnings
- Missing file alerts

---

### 2. test-writer-fixer Agent
**Phases:** 2, 3, 7, 12
**Purpose:** Test execution and validation

**Responsibilities:**
- Run validation scripts after extraction
- Execute unit tests for components
- Report test failures with details
- Verify integration points working

**Launch Trigger:** After component extraction, when tests available

**Outputs:**
- Test pass/fail reports
- Integration validation
- Coverage analysis

---

### 3. backend-architect Agent
**Phases:** 4, 5, 6, 8
**Purpose:** Architecture consistency review

**Responsibilities:**
- Review API contracts
- Validate integration patterns
- Check design consistency
- Report architectural issues

**Launch Trigger:** After architecture-heavy phases (solver, placement, MCP)

**Outputs:**
- Architecture review
- Design consistency report
- Integration warnings

---

### 4. devops-automator Agent
**Phases:** 7, 9, 11
**Purpose:** Build and deployment verification

**Responsibilities:**
- Verify build configurations
- Test automation scripts
- Check systemd services
- Validate deployment readiness

**Launch Trigger:** After automation/build-related phases

**Outputs:**
- Build status reports
- Automation test results
- Deployment checklist

---

### 5. workflow-optimizer Agent
**Phases:** Continuous (all phases)
**Purpose:** Progress tracking and optimization

**Responsibilities:**
- Track overall integration progress
- Identify bottlenecks
- Report missing cross-references
- Suggest workflow improvements

**Launch Trigger:** Runs continuously throughout integration

**Outputs:**
- Progress dashboard
- Bottleneck analysis
- Optimization suggestions

---

## Coordination Protocol

### Launch Pattern

```
Phase N Start
    ↓
Main: Extract files
    ↓
Main: Launch background agent(s) with Task tool
    ↓
Main: Continue with verification (non-blocking)
    ↓
Main: Check agent reports (async)
    ↓
Main: Address critical issues if any
    ↓
Main: Git commit
    ↓
Phase N Complete
```

### Communication Flow

```
┌─────────────┐
│ Main Thread │
└──────┬──────┘
       │
       ├─ Launch Agent (Task tool)
       │       ↓
       │  ┌─────────────────┐
       │  │ Background Agent│
       │  └────────┬────────┘
       │           │
       │           ├─ Verify files
       │           ├─ Run tests
       │           ├─ Check structure
       │           │
       ├─ Continue execution
       ├─ Organize files
       ├─ Run local checks
       │
       │  Background completes
       │           │
       ├←──────────┴─ Report findings
       │
       ├─ Review reports
       ├─ Address issues
       │
       └─ Git commit
```

### Report Format

Agents report in structured format:

```json
{
  "agent": "explore",
  "phase": 2,
  "status": "complete",
  "findings": {
    "critical": [],
    "warnings": [
      "File viewfs/README.md exists, will merge"
    ],
    "info": [
      "25 files extracted successfully",
      "Directory structure matches specification"
    ]
  },
  "recommendations": [
    "Review merged README.md for conflicts"
  ]
}
```

### Priority Levels

| Level | Description | Action |
|-------|-------------|--------|
| **CRITICAL** | Missing dependencies, file conflicts, broken tests | BLOCK: Must fix before proceeding |
| **WARNING** | Style issues, potential problems, merge conflicts | REVIEW: Consider fixing |
| **INFO** | Status updates, confirmations | LOG: For reference |

---

## Agent Task Examples

### Phase 1: Explore Agent

**Task:**
```
Verify Phase 1 extraction (rtt_dropin.zip):
- Confirm .rtt/ directory created with expected structure
- Verify 5 manifests in .rtt/manifests/
- Check schemas/ has 3 JSON schemas
- Confirm tests/validate.py exists
- Report any missing files or unexpected extras
```

**Expected Report:**
```
✓ .rtt/ directory structure correct
✓ 5 manifests found (.rtt/manifests/*.json)
✓ 3 schemas found (schemas/*.schema.json)
✓ validate.py present (tests/validate.py)
⚠ README.md will conflict with project README (recommend rename)
```

---

### Phase 2: test-writer-fixer Agent

**Task:**
```
Validate Phase 2 CAS registry:
- Run tools/cas_ingest.py on agents/common/*.agent.json
- Verify SHA256 hashes created in .rtt/registry/cas/sha256/
- Test tools/cas_pack.py generates packfile
- Run tools/view_materialize.py on views/claude.view.json
- Report any failures with details
```

**Expected Report:**
```
✓ cas_ingest.py executed successfully (3 agents ingested)
✓ SHA256 entries created (.rtt/registry/cas/sha256/*)
✓ Packfile generation successful (.rtt/registry/pack/agents.pack)
✓ View materialization works (providers/claude/.claude/agents/)
✓ All CAS operations functional
```

---

### Phase 3: test-writer-fixer Agent

**Task:**
```
Validate Phase 3 signing infrastructure:
- Generate test keypair with tools/keys_ed25519.py
- Build and sign plan with tools/plan_build.py
- Verify signature with tools/plan_verify.py
- Test determinism (run plan_build.py twice, compare hashes)
- Report signature validation results
```

**Expected Report:**
```
✓ Keypair generated successfully
✓ Plan built and signed (plans/latest.json)
✓ Signature verifies correctly
✓ Determinism confirmed (hash1 == hash2)
✓ Signing infrastructure operational
```

---

### Phase 7: devops-automator Agent

**Task:**
```
Validate Phase 7 automation pipeline:
- Run auto/00-bootstrap.py
- Run auto/10-scan_symbols.py
- Run auto/20-depdoctor.py
- Run auto/30-generate_connectors.py
- Run auto/40-plan_solver.py
- Run auto/50-apply_plan.py
- Report any script failures with error details
```

**Expected Report:**
```
✓ 00-bootstrap.py - directories initialized
✓ 10-scan_symbols.py - symbols indexed
✓ 20-depdoctor.py - dependencies unified
✓ 30-generate_connectors.py - stubs generated
✓ 40-plan_solver.py - plan created
✓ 50-apply_plan.py - plan applied
✓ Full automation pipeline operational
```

---

### Phase 9: devops-automator Agent

**Task:**
```
Validate Phase 9 build systems:
- Build Rust components (tools/rtt_sign_rs, fabric/shm)
- Build Go components (tools/rtt_sign_go)
- Install Node dependencies (pnpm install)
- Test driver protocol (sample Rust/Python/Go/Node drivers)
- Report build status and any errors
```

**Expected Report:**
```
✓ Rust builds successful (all crates compile)
✓ Go builds successful (all modules compile)
✓ Node dependencies installed (pnpm success)
✓ Driver protocol consistent across languages
✓ Build system fully operational
```

---

## Cross-Phase Verification

Workflow-optimizer agent tracks dependencies across phases:

```
Phase 2 (CAS) → Phase 3 (Signing) → Phase 4 (Solver)
                     ↓
              Agent verifies:
              - CAS operational before signing
              - Signing works before solver
              - Each phase builds on previous
```

**Example Report:**
```
Phase 4 starting...
↓
Checking Phase 2 dependencies:
  ✓ CAS registry operational (.rtt/registry/cas/)
  ✓ Packfile present (.rtt/registry/pack/agents.pack)
↓
Checking Phase 3 dependencies:
  ✓ Signing tools available (tools/*_ed25519.py)
  ✓ Test keypair generated
  ✓ plans/ directory exists
↓
All dependencies satisfied for Phase 4
✓ Safe to proceed with constraint solver
```

---

## Failure Handling

### Critical Failure Example

```
Phase 3: test-writer-fixer Agent
↓
Task: Verify signing infrastructure
↓
CRITICAL: plan_verify.py reports signature invalid
↓
Main Thread: HALT
↓
User notification: "Signature verification failed in Phase 3"
↓
Wait for manual resolution
```

### Warning Example

```
Phase 2: Explore Agent
↓
Task: Verify file structure
↓
WARNING: viewfs/README.md already exists (will merge)
↓
Main Thread: CONTINUE (non-blocking)
↓
Log warning for review
↓
Proceed with extraction
↓
Manual merge later if needed
```

---

## Benefits of Background Verification

1. **Early Detection** - Issues found before they cascade
2. **Non-Blocking** - Main execution continues unimpeded
3. **Parallel Validation** - Testing while extracting
4. **Expert Perspectives** - Specialized agents for different concerns
5. **Continuous Monitoring** - Workflow-optimizer tracks progress
6. **Safety Net** - Critical issues caught before commit

---

## Agent Effectiveness Metrics

Track agent value during integration:

| Metric | Target |
|--------|--------|
| Critical issues caught | 0 (ideal: catch in planning) |
| Warnings generated | 5-10 (helpful, not noisy) |
| False positives | <10% (high signal-to-noise) |
| Time overhead | <10% (mostly parallel) |
| Issues prevented | Measurable (avoided conflicts, missing files) |

---

## Summary

Background agents provide:
- ✅ Continuous verification without blocking
- ✅ Specialized domain expertise
- ✅ Early issue detection
- ✅ Progress tracking
- ✅ Safety net for critical failures

They do NOT:
- ❌ Block execution for warnings
- ❌ Make decisions (human in control)
- ❌ Modify files (observe only)
- ❌ Introduce delay (run in background)

**Result:** Faster, safer integration with expert oversight

---

**End of Agent Coordination Strategy**

For phase execution details, see [PHASE-GUIDE.md](./PHASE-GUIDE.md)
For overall plan, see [RSD-PLAN.md](./RSD-PLAN.md)
