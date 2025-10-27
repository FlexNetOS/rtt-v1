No. Symlinks and proxy refs are a stopgap. The top solution is a local content-addressed registry with virtual provider views and signed immutable manifests. Use symlinks or proxy files only as a last fallback.

## Why symlinks and proxies are not ideal

**Symlinks**

* Break on Windows without Developer Mode.
* Unstable in zips and some VCS tools.
* Cross-drive paths fail.
* Security scanners often flag them.

**Proxy refs**

* Require a custom resolver in every consumer.
* Many tools treat them as data, not pointers.
* Extra disk I/O and parse overhead.

## Secret formula

**Single immutable truth → Virtual views → Signed plans → Deterministic overlays → Zero-copy reads.**

## What the top 0.001% do

### 1) Local CAS registry (immutable, signed)

* Store every agent manifest once by hash.

```
.rtt/registry/
  cas/sha256/<32>/.../<hash>.json   # canonical agent
  index.json                        # id → hash, version sets
  trust/keys/*.pub                  # allowed signers
```

* Manifests are content-addressed and signed.
* All providers resolve through this registry.

### 2) Virtual provider views (no disk copies)

* Expose provider trees as a **virtual filesystem**.
* Linux/macOS: FUSE. Windows: WinFsp.
* Each provider sees `/.claude/agents/*` etc, but files are projections from CAS at read time.
* Views apply policy and overlays on the fly. Nothing is duplicated.

```
[CAS registry] → [View engine] → mount: /providers/claude/.claude/agents
```

**Fallback order**

1. VFS mount (FUSE/WinFsp).
2. Hardlinks (same filesystem only).
3. Symlinks (when allowed).
4. Proxy JSON (last resort).

### 3) Deterministic overlays instead of forks

* Three layers merged at read time:

  * **Base**: canonical agent in CAS.
  * **Provider overlay**: provider-specific tweaks.
  * **Environment overlay**: dev/prod site flags.
* Merge via JSON-Patch or CUE with fixed precedence: env > provider > base.
* Result is deterministic and cacheable by hash.

```
result_hash = H( base_hash, provider_patch_hash, env_patch_hash )
```

### 4) Signed “plan-only” projections

* A projection is not ad-hoc files. It is a **signed plan**:

```
plans/provider.claude.view.json
{
  "provider":"claude",
  "agents":[{"id":"summarize","use":"sha256:...","overlays":["provider:claude","env:prod"]}],
  "sign":{"alg":"ed25519","key_id":"...","sig":"..."}
}
```

* The view engine materializes only signed plans.
* MCP connectors read through the mounted view. RTT accepts the plan hash.

### 5) Zero-copy reads

* Pack all agent JSON into a single **memory-mapped packfile** with an index.

```
.rtt/registry/pack/agents.pack
.rtt/registry/pack/index.lut   # key: sha256 → {offset,len}
```

* Provider views serve slices from the packfile. No parsing until needed.
* Cold start and cache locality improve.

## Architecture

```
[Agents in CAS + packfile] ─→ [View Engine + Overlays] ─→ (FUSE/WinFsp mount) ─→ [/providers/<p>/.<p>/agents/*]
                                            │
                                            └─→ [RTT Planner] uses the same CAS and signed plans
```

## Pros and cons

| Approach                    | Pros                                                 | Cons                                   |
| --------------------------- | ---------------------------------------------------- | -------------------------------------- |
| Symlinks                    | Simple                                               | Cross-platform pain, fragile packaging |
| Proxy refs                  | Portable                                             | Requires custom resolver, extra I/O    |
| Hardlinks                   | Zero dup, fast                                       | Same volume only, metadata oddities    |
| **VFS views (FUSE/WinFsp)** | No dup, policy at read time, overlays, fastest scale | Needs a small daemon                   |
| **Packfile + VFS**          | Best cold start, zero-copy slices                    | Build step, index management           |

## Minimal spec to implement

**CAS index**

```json
{
  "agents": {
    "summarize@1": "sha256:ab12...",
    "search@1": "sha256:cd34..."
  },
  "signers": ["ed25519:ops-root"]
}
```

**Overlay rule**

```json
{
  "merge": "cue|json-patch",
  "precedence": ["env","provider","base"]
}
```

**View plan**

```json
{
  "provider":"claude",
  "mount": "/providers/claude/.claude/agents",
  "entries":[
    {"id":"summarize@1", "hash":"sha256:ab12...", "overlays":["provider:claude","env:prod"]}
  ],
  "sign": {...}
}
```

## Actionable path for you

1. Keep your current symlink/proxy setup as a temporary fallback.
2. Add a **CAS registry** under `.rtt/registry/` and write an index.
3. Add a tiny **view engine** that can: resolve CAS by hash, apply overlays, serve via FUSE/WinFsp.
4. Create a **packfile** for agents and a LUT index. Memory-map it.
5. Switch MCP connectors to read from the mounted view.
6. Make RTT accept only **signed plan projections** for provider routes.

## What you were missing

* Content-addressed immutability and signatures at the agent level.
* Virtualized provider trees with deterministic overlays.
* Memory-mapped packfiles for zero-copy projection.
* Plan-only materialization with signatures to prevent drift.

This removes duplication, locks correctness, and scales across providers with minimal latency.
