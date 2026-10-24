# Machine resources: keeping workers from overloading the machine

Many agents building Lean at once can push the load average to several times
the core count and exhaust memory. Builds then slow down for everyone, checks
die silently, and the agent harness may kill background jobs, such as a merge
halfway through its checks. Treat CPU, memory, and disk as campaign resources
that the orchestrator manages.

## Why per-agent limits are not enough

- **Lake has no job limit.** Each `lake build` starts about one compiler per
  core. "One build per agent" still means five agents start about five times
  the core count, for example 40 compilers on 8 cores.
- **Each compiler can use 1–2 GB of memory.** Thirty compiles need more memory
  than most machines have.
- **Duplicate recompilation is the real multiplier.** A fresh worktree
  compiles the whole project. A worktree based on an old main recompiles
  everything merged since then. Every helper of a long-unmerged branch
  recompiles that branch's modules. All of this runs in parallel, across
  worktrees.

## Measure first

Before acting, count what is running and attribute it:

```bash
nproc; cut -d' ' -f1-3 /proc/loadavg; free -g | sed -n 2p
pgrep -x lean | wc -l                       # running compilers
for p in $(pgrep -x lake); do               # each build: worktree, compiler count
  echo "$(readlink /proc/$p/cwd) $(pgrep -P $p -x lean | wc -l)"
done | sort
```

Count compiles started by other projects or sessions separately. The gate
below does not limit them, but they use the same cores.

## 1. A machine-wide compile gate

Limit the total number of compiles, not the number per agent. The bundled
[`../assets/lean-compile-gate.sh`](../assets/lean-compile-gate.sh) replaces
the toolchain's `lean` with a wrapper. Each compile of a `.lean` file waits
for one of N machine-wide `flock` slots. A slot is released when the compiler
exits, even if it is killed. Other invocations, such as `--version`,
`--print-prefix` and the language server, run directly.

- Set N to about cores − 1, and lower it if memory requires:
  N × (peak memory per compile) must leave headroom.
- Reserve one extra slot for the main checkout's merge checks
  (`LEAN_GATE_RESERVED`), so worker builds cannot block landings.
- Set `LEAN_GATE_PREFIXES` to the campaign's checkout and worktree
  directories when the toolchain is shared with other projects. Compiles of
  those other projects then run ungated.
- After installing, check that main is still up to date: `lake build
  --no-build` must succeed with no rebuild.
- Record how to remove the gate (rename `lean.real` back to `lean`).
  Reinstall it whenever the toolchain is reinstalled.
- Tell every worker: a build may print `waiting for a compile slot` and run
  slower. That is expected, not a hang. Do not retry, and do not start a
  second build.

## 2. Never recompile what main already built

- **Shared copy-on-write builds.** Mount each worktree's `.lake/build` as an
  overlay: a read-only snapshot of main's complete build below, and a
  private writable layer for the worktree above. Lake then sees a complete
  build and compiles only the modules the branch changed and their
  dependents. This needs overlayfs, normally root. Mounts do not survive a
  reboot.
- **Never hardlink a writable build to a shared copy.** Lean rewrites
  `.olean` files in place, which corrupts every linked copy. Hardlinks are
  safe only between read-only snapshots.
- **Refresh the snapshot after every merge into main**, then remount idle
  worktrees on it. Refuse to remount while a `lake` or `lean` process runs in
  that worktree. A stale snapshot makes every worktree recompile the merged
  modules at the same time.
- **Make snapshots incremental**, e.g. `rsync --link-dest=<previous
  snapshot>` into a new read-only directory. Delete unused snapshots after
  each refresh. Full copies fill a disk quickly.
- **Helpers of a branch far ahead of main** should stack the parent
  worktree's private layer, frozen read-only, on the parent's snapshot. Then
  they start fully built.

## 3. Merge often

Unmerged work is recompiled in every worktree that needs it. Landing ready
branches into main, then refreshing the snapshot, is usually the biggest
single saving. Ask long-running branches for a ready-for-main commit when
their helpers are rebuilding the same modules.

## 4. Worker discipline

Put these in every Lean worker brief:

- one targeted `nice -n 5 lake build <Module>` at a time, never several in
  parallel; build the modules being changed, not the whole project;
- a sub-orchestrator runs at most two helper builds at a time;
- research, review, and writing agents run no builds;
- after main advances: merge main, then move onto the new snapshot while idle.

The orchestrator runs heavy whole-project checks, such as import-all, freeze,
and full builds, one at a time and niced.

## 5. Make resource failures visible

- Merge checks must print build errors. A check that discards output makes an
  OOM-killed build look like an empty failure, or even a pass.
- If the harness or the OOM killer stops a merge or check, first make sure
  main is not left half-merged. Reset to the last verified commit and rerun
  the merge alone.
- When the load is high, find the cause with the measurements above before
  restarting work. Do not just wait. The rule against stopping because
  another Lean process is running still applies; the gate handles contention.
