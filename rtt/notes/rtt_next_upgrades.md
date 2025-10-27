Download. Drop in and iterate.

* [rtt_next_upgrades.zip](sandbox:/mnt/data/rtt_next_upgrades.zip)

## What you got

* VFS daemon skeleton

  * `viewfs/rust-fuse/` FUSE stub for Linux/macOS.
  * `viewfs/windows/README.md` WinFsp plan.

* Ed25519 signing

  * `tools/rtt_sign_rs/` Rust CLI: gen, sign, verify.
  * `tools/rtt_sign_go/` Go CLI: gen, sign, verify.

* Planner

  * `planner/rtt_planner_rs/` emits a deterministic plan and optionally signs it.

* Drivers

  * Rust, Python, Go, and Node stubs that speak JSON over stdio.
  * Shared protocol documented in `drivers/README.md`.

* SHM ring

  * `fabric/shm/` Rust crate with header and SPSC ring placeholders.

* JS/TS/PNPM

  * `package.json`, `pnpm-workspace.yaml`, `.npmrc`, `.pnpmfile.cjs`, `tsconfig.json`.
  * Node driver is a workspace member.

## Next steps

1. Build sign tool.

   ```
   cd tools/rtt_sign_rs && cargo build --release
   ./target/release/rtt-sign gen
   ```
2. Emit a plan and sign it.

   ```
   cd planner/rtt_planner_rs
   cargo build --release
   ../../tools/rtt_sign_rs/target/release/rtt-sign gen > /tmp/keys
   PRIV=$(grep '^priv:' /tmp/keys | cut -d: -f2)
   ./target/release/rtt-planner ../../.rtt/routes.json ../../.rtt/manifests ../../plans/0001.json "$PRIV"
   ```
3. Replace materialization with VFS. Implement lookups in `rtt-viewfs` that read CAS and overlays. Mount:

   ```
   sudo ./target/debug/rtt-viewfs providers/claude/.claude/agents
   ```
4. Implement the ring and replace placeholders in `rtt-fabric-shm`.
5. Flesh out each driver: map `Probe/Open/Tx/Rx/Close/Health` to real transports.
6. Add provider-specific Node tools under the workspace if needed. Configure with pnpm:

   ```
   pnpm i
   ```

This covers upgrades 1–5 with runnable stubs and a clean path to production.
