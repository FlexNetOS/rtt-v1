Download. Drop in and run.

* [rtt_mcp_ingest_signed_plans.zip](sandbox:/mnt/data/rtt_mcp_ingest_signed_plans.zip)

## Direct answer

Yes. This implements the most current elite pattern: content-addressed registry, virtual provider views, signed plan-only execution, deterministic overlays, constraint solver inputs tied to QoS and topology, zero-copy lanes, ruthless observability, and autotuning. There is no hidden formula beyond “Specify → Prove → Generate → Measure → Autotune” plus CAS+VFS and signed plans. Your gap was automation across MCP tools, skills, and agents, and gating plan generation on invariants.

## What the new builder adds

* **MCP ingest**: reads `mcp/<provider>/tools.json`, writes immutable CAS entries, and emits RTT manifests.

  * `tools/mcp_ingest.py`
* **Agents ingest**: canonical agents into CAS.

  * `tools/agents_ingest.py`
* **Skills ingest**: skills into CAS for capability matching.

  * `tools/skills_ingest.py`
* **Autowire**: optional `--autowire` maps Agents↔MCP Tools by name or shared skills.

  * `tools/plan_build.py`
* **Invariant gate**: refuses plan if endpoints are missing, duplicated, or self-looped.

  * built-in in `plan_build.py`; also a standalone `tools/invariants_check.py`.
* **Signing**: produces signed `plans/<plan_id>.json` and `plans/latest.json`.

## How to run

```bash
# 0) Keys
python tools/keys_ed25519.py dev-ed25519

# 1) Ingest
python tools/agents_ingest.py agents/common/*.agent.json
python tools/mcp_ingest.py claude mcp/claude/tools.json
python tools/skills_ingest.py skills/*.skill.json

# 2) Build plan with autowire and invariants gate
python tools/plan_build.py .rtt/routes.json .rtt/manifests dev-ed25519 agents/common claude skills --autowire

# 3) Verify
python tools/plan_verify.py plans/latest.json
```

## “Gate plan generation on a quick invariant check”

Function: block plan emission when cheap safety rules fail. It prevents bad graphs before signing or apply. The gate runs **before** plan hashing and signing.

Minimum invariants:

* **Existence**: every `from` and `to` appears as a `symbol.saddr` in `.rtt/manifests/`.
* **No duplicates**: no repeated `(from,to)` pairs.
* **No self-loops**: `from != to` unless explicitly allowed.
* **Optional fast checks you can add**:

  * Fan-out rules: one active `to` per `(from, class!=bus)`.
  * Version meet not empty for compatible endpoints.
  * Policy prefilter: route allowed by ACL.
  * Budget sanity: default QoS present on both ends.

Outcome:

* If any invariant fails → exit non-zero with a JSON error list. No plan file is written. Nothing gets signed.

## What you were missing

* A unified **catalog ingest** for agents, MCP tools, and skills into CAS.
* An **autowire step** to propose routes based on names and capabilities.
* A **pre-sign gate** that enforces invariants and keeps bad plans out.
* A clean **signed-plan artifact** as the only input to apply.

If you want semver “version meet” checks, QoS-budget checks, or NUMA-aware placement in the planner next, say “add solver constraints” and I will extend `plan_build.py` accordingly.
