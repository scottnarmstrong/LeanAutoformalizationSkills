---
name: lean-elaboration
description: Diagnose and improve Lean 4 elaboration performance in a repo — locate genuine hot spots, route by profile phase, apply the proven levers (consumer import narrowing, nlinarith elimination, targeted simp-only, head-class caches, leaf splits, folding hypothesis types to the abbrev their consumer expects, naming the function in congr), and A/B every change. Use when a repo builds slowly, a file blows past heartbeats, before landing perf edits, or when planning an elaboration campaign.
---

# Lean Elaboration Improvement

This guidance distills repeated A/B measurements from large Lean 4 and Mathlib
repositories. The examples preserve useful magnitudes and negative results
without carrying private project history into the workflow. Full evidence:
[references/evidence.md](references/evidence.md).

Companion skills: **lean-elaboration-test** (the repo-level measurement
snapshot — run it first to find candidates), **lean-learnings** (ambient-space
and reusable Mathlib guidance).

## Rule zero

**Improve elaboration by measurement, not by taste.** A proof that looks
cleaner can be slower; a verbose proof can be much faster. The measured studies' costliest
mistakes were interventions rolled out by analogy or aesthetics: a "cleanup"
file-split added +360s wall-clock in one afternoon; a cache rolled out to a
sibling file regressed it. Every intervention gets a profile before and an A/B
after, and speculative edits that don't move the numbers are reverted before
commit.

## The loop

1. **Find candidates at repo level** — run the lean-elaboration-test snapshot;
   take the heavy tail (files ≥10s/≥20s/≥30s build wall-clock) from the build
   log.
2. **Confirm each candidate with a warm own-file profile** — build wall-clock
   includes upstream rebuilds, olean writes, and contention; it overstates
   own-file cost by ~2.5× routinely. The ground truth is:
   ```bash
   <repo-approved-lean-command> --profile <Root>/<Path>/File.lean 2>&1 | tail -25
   ```
   Read the `cumulative profiling times` block. A "50s file" usually has 1–3s
   of fixable cost. If `import` dominates, **the file is not fixable locally**
   — the lever is upstream, or in what this file imports; do not touch its proofs.
3. **Route by dominant phase** (dominant = >5s AND >25% of total):

   | Dominant phase | Meaning | Action |
   |---|---|---|
   | `typeclass inference` | instance search / overloaded algebra | head-class cache (guards below); explicit instance args; definitional bridges |
   | `interpretation` | tactic execution — `nlinarith`/`linarith`/`polyrith` | explicit bounds + monotonicity lemmas + `calc`; `positivity` |
   | `simp` | simp engine / definitional unfolding | `simp only` with explicit list — but only where single calls exceed ~1s; `rfl`/`exact`/`dsimp`+`rw` for definitional bridges |
   | `elaboration` | term elaboration, big unification | **run the `sorry`-substitution test first** (below); then lever 8, narrow wide simp chains, extract standalone lemmas, check for `Real.rpow`/`Real.exp` entering numeric tactics |
   | `import` | upstream olean load | fix upstream or narrow this file's imports; NOT a local proof problem |
   | `tactic execution` | tactic doing real work post-elab | check for `congr` events (lever 9); split the proof, extract a helper |
   | `type checking` | large terms | break into named `have`s / helper lemmas |

3b. **Before touching any proof, ask whether the cost is even in the proof.**
   Replace the suspect declaration's body with `sorry` and re-profile. If the
   phase total is **unchanged**, the cost is in elaborating the *statement*, and
   no tactic, simp, cache, or import lever can touch it — go to lever 8. This
   one-minute test prevents whole afternoons of proof tuning against a signature
   problem. (Measured: a file at 9.55s elaboration read 9.57s with both proof
   bodies `sorry`d.) A sibling declaration with the same hypotheses but a
   cheaper conclusion is the control that confirms it.

   **Locating anonymous events.** `--profile` often reports statement cost as
   bare `elaboration took 5.3s` with no declaration name. Bisect by inserting
   `#exit` at successive line numbers in an untracked copy and re-profile. A
   short bisection usually pins the cost to one declaration without editing
   tracked source.

4. **Apply ONE intervention** — never stack changes before measuring.
5. **A/B and keep-or-revert** — compare a baseline and one edited variant of
   the same file; use at least three runs if relying on wall-clock. Profile deltas are
   wall-clock-noise-immune and win when they disagree. Keep the edit only if
   the relevant phase drops ≥2s (or ≥10%) without moving cost somewhere worse.
   Three consecutive failures of one technique on a file family = stop
   applying that technique to the family.

## The levers, ranked by reliability

### 1. Import-load reduction in consumers (the biggest structural lever)
Remove/narrow imports in the files that *consume* a heavy module; never
"quarantine" by splitting the upstream file while re-exporting everything
(that failed: same content, 2.5× cost across three files). Verify
symbol-level: enumerate the imported module's public API by grep and check
usage — naive candidate lists have a **~50% false-positive rate**
(load-bearing instances/tactics), so build-verify each removal in the first
pass, not a follow-up. Avoid umbrella imports: import the precise provider
file, not the namespace facade. Measured: one consumer-side sweep cut whole
consumer groups 22–46% and a single file −59% with zero content change.

### 2. `nlinarith`/`linarith` elimination from arithmetic closers
Once nonlinear facts are named hypotheses, close with monotonicity lemmas
(`add_le_add`, `sub_le_sub_right`, `mul_nonpos_of_nonpos_of_nonneg`) and
`calc`; use `positivity` for pure sign goals; prefer `linarith only [...]`.
Measured: interpretation 14.6s → 3.15s; a file's `nlinarith` count 7 → 0 with
own-file cost halved. **Near `Real.rpow`/`Real.exp`: extract the pure-algebra
core as a standalone lemma over abstract reals** so numeric tactics never
enter transcendental terms (`set`-bound exp-lets unfold inside `nlinarith`
and cause expensive weak-head normalization; use `clear_value` or opaque
variables).

### 3. Targeted `simp` narrowing — bimodal, so check the precondition
`simp`/`simpa` → `simp only`, or better `exact`/`rfl`/`dsimp [defs]; rw [law]`
for definitional bridges. **Works spectacularly** on files where individual
simp calls exceed ~1s (18.8s → 0.3s). **Null result** as a blanket file-scope
sweep where peaks are <1s (−0.2s against ±3s noise — reverted). Screen with
the profile's per-call `simp took Nms` lines; skip calls under ~200ms. Commit
only on >3s sustained file-level A/B.

### 4. Head-class instance caches (`private instance ... := inferInstance`)
For files with big `variable`/`include` blocks (≥50 lines, referencing things
like `[NeZero d]`, `[IsProbabilityMeasure P]`, or project-type-indexed
instances): cache each recurring head-class once so resolution happens once
per file and propagates via olean to importers. Guards, all mandatory —
learned from a rollout in which 4 of 6 planned caches were inapplicable and
1 of the remaining 2 was null:
- **Only above the 5s floor**: below 5s cumulative typeclass inference, caches
  typically *hurt* (disambiguation overhead).
- **Only for CLOSED instance searches.** A cache cannot terminate an *open*
  search whose goal head is still a metavariable (e.g. `SMul ℝ ?α` from
  elaborating `•` before the type family is known) — it only lengthens the
  candidate list. Diagnose with `trace.Meta.synthInstance` before choosing:
  closed search → cache; open search → **type ascriptions at the
  elaboration-order pinch** (measured: 8→0 SMul events, −91% typeclass, where
  the prescribed cache was refuted by A/B).
- **Placement is load-bearing**: top-level / namespace-level, **outside any
  `section ... variable` block** — section scoping hides the cache and it
  silently does nothing (the operative distinction is top-level vs
  section-scoped, not namespace membership).
- **Leaf-first**: in an import chain, cache the leaf only; a redundant cache
  upstream of an already-cached file *regressed* +1.2s.
- **Cache only head-classes the file actually uses**; never derived classes.
- **Never roll out by analogy**: identical brackets gave PASS on one file and
  FAIL on its direct sibling. A/B each file.
- Propagation check: if downstream consumers improve <0.5s, the cache didn't
  propagate — placement is wrong.
- When creating a structurally similar file, check whether it should import a
  cached provider or needs its own measured cache. Several cacheless variants
  once added more than 1,000 seconds of CPU in one build.

### 5. Leaf splitting with DAG-shaped imports
Splitting pays only when it changes what gets loaded or unblocks parallelism:
push the parent's heavy imports down to only the sub-modules that need them
(grep symbol counts per line range), make sub-module edges a DAG not a chain,
and let independent halves be siblings. Splitting a file while consumers
still transitively need all parts is a pure loss (import preamble + olean
overhead ×N). File-size discipline (~1,000–1,500-line ceiling) is about
edit-iteration latency and parallelism, not cumulative CPU.

### 6. Standalone lemma extraction / clean-context elaboration
Extract an expensive mathlib call or a heavy algebraic step into a
`private lemma` with a minimal signature: instances resolve once, the call
site is a cheap application, and each lemma gets its own heartbeat budget.
This is also the escape from single-expensive-unification walls. Related:
keep membership/proof arguments out of heavy dependent surfaces; avoid
partially-applied heavy theorems with pinned late implicits; prefer small
constructor lemmas over monolithic wired-up `abbrev`s.

### 7. Statement hygiene that doubles as perf
- >10 named hypotheses on a theorem → compress (structure bundle, typeclass
  instances, caller-side `norm_num`, definitional `let`s). LLM agents don't
  feel signature pain — one theorem reached 85 hypotheses / 539-line
  signature before anyone flagged it.
- Unused section variables / auto-bound instances are per-declaration
  instance-search cost; keep the linter at zero.
- rfl `_def` lemmas instead of `simp only [thedef]` unfolding of heavy
  definitions.

### 8. Fold a hypothesis type to the abbrev its consumer expects
The single highest-yield statement-level fix found so far (−98% elaboration,
three times). **Precondition:** a hypothesis is written in fully *unfolded*
form, and the **conclusion feeds it into a dependent term** whose own signature
declares that argument through an `abbrev`. Lean then discharges the
unfolded-vs-abbrev defeq for the entire binder block, repeatedly.

```lean
-- costly: hypothesis unfolded, but `perturb` declares its arg as `FluxIntegrable U a u`
theorem foo (hu : ∀ φ : Test U, IntegrableOn (fun x => ⟪A x (u.grad x), φ.grad x⟫) U) :
    P (perturb u w hu) = ...
-- cheap: same proposition, stated the way the consumer expects
theorem foo (hu : FluxIntegrable U a u) : P (perturb u w hu) = ...
```

Because the abbrev is definitionally the term, **this is notation, not
semantics**: the statement is unchanged and no consumer needs touching. Verify
with a full build anyway. The tell is verbosity *plus* dependent use — a sibling
with the identical unfolded block but no dependent consumer costs ~0 ms, so do
not "clean up" verbose binders that nothing consumes; you will gain nothing.

**Sweeping for it:** grep is too weak (the unfolded text varies with binder
names and formatting). Parse instead — for each declaration, split the signature
at the top-level `:` with a paren-depth counter, then flag any explicit binder
whose type is long (>90 chars) and contains `fun`/`∀` **and** whose name occurs
in the conclusion. On a 600k-line repo that yielded 42 candidates in 22 files;
profiling showed all but three had elaboration <450 ms. Expect a low hit rate
and profile before editing — the detector finds the shape, not the cost.

### 9. Name the function in `congr`
`congr`/`congr 1` searches for a congruence decomposition. When you already know
which function is being peeled, name it: `refine congrArg f ?_`. Same subgoals,
no search.

```lean
congr 1                                  -- 5.6s
refine congrArg (· ^ (1 / p.toReal)) ?_  -- ~0s, goal `X = Y` as before
```

Bare `congrArg _ ?_` usually fails to infer `f` — supply it (`congrArg Real.sqrt`,
`congrArg (HMul.hMul _)`, `congrArg (· ^ e)`). Typical goals: `f a = f b` after a
`rw` through an `rfl`-lemma, or after a `change`. Screen a repo by profiling
modules whose build-wall is ≥10s and which contain `congr`, then grep the profile
for `Tactic.congr took` — costs cluster bimodally at either <100 ms or >2.5s, so
the expensive ones are unmistakable. Measured: 9.10s → 0.85s, 8.28s → 3.28s,
6.35s → 0.65s.

## The negative catalog — do not retry these

- `set_option maxHeartbeats` / `synthInstance.maxHeartbeats` bumps: changes
  the failure threshold, not the cost. Treat a default-heartbeat failure as a
  design signal. If the repository bans overrides, treat that as a hard rule.
- `attribute [reducible]` on instances: shifts synthesis cost to defeq checks.
- Splitting a slow file "for performance" without import/variable-block
  changes: cumulative CPU stays flat or rises.
- Section-scoped `private instance` caches: inert, silently.
- "Backup" caches for derived classes (`FiniteDimensional` alongside an
  existing chain): regressed when tried.
- Blind unused-import removal from grep lists: ~50% false positives; the
  single biggest predicted win of one audit broke the build.
- Structural dedup/helper extraction from similarity audits: 2 of 3 failed
  line-by-line inspection; discount such candidates 50–70%.
- Tuning namespace orchestrator/facade files: their cost is olean
  deserialization; splitting moves it around.
- Chasing "diffuse typeclass" files (thousands of sub-100ms searches, no
  dominant head-class): proof restructuring left 8.5s → 8.5s. This is the
  structural floor; accept it or reconsider the ambient types (see
  `lean-learnings`).
- Trusting a profile taken while other agents/users use the CPUs, or
  comparing a parallel batch profile with a serial one.
- `#print axioms` (or other `#`-commands) left in source files: they re-run
  at every rebuild — measured at 98% of one module's elaboration cost. Put
  axiom audits in probe files outside the build root.

## Sharp edges

- **`touch` does not reliably invalidate** because Lake uses content hashes.
  Use a repository-provided guarded invalidation command. If none exists,
  resolve and remove only the exact project-owned module artifacts after
  confirming the path cannot enter a dependency tree.
- **Do not use `lake clean` for profiling.** It can erase dependency caches.
  Invalidate only the repository-owned artifacts needed for the measurement,
  under the repository's authorization rules.
- **Profile totals don't sum to wall-clock**: olean serialization and IR
  compilation are uncategorized. Use the phase breakdown to pick the lever,
  wall-clock/A-B to judge success.
- `lean --profile` truncates events under 100ms; diffuse files underreport in
  per-decl listings but show in the cumulative block. For per-declaration
  attribution of unattributed elaboration time, rerun with
  `-D trace.profiler.output=<file>.json`.
- **Elaboration cost compounds with downstream load**: files get slower with
  zero edits as new callers exercise their theorem surfaces. A regression
  with no proportional line growth is load compounding or contention, not
  necessarily new bad code — check predicted (Δlines × prior ms/line) vs
  actual ΔCPU before hunting a culprit file.
- **Compute which bound you are under before optimizing anything.** Two
  numbers: the work-floor (`total CPU / cores`) and the critical chain
  (longest weighted import path). The larger one is your wall-clock. The same
  repo can be **chain-bound on a dev box and work-bound in CI** — one measured
  case: 11,350s CPU / 1,767s chain is chain-bound on 8 cores (floor 1,419s, so
  only on-chain fixes help) but work-bound on a 4-core runner (floor 2,838s, so
  *every* CPU saving converts). Off-chain work is not worthless; it is worthless
  *for the machine shape where the chain dominates*. Say which one you optimized
  when you report a win.
- Cumulative-CPU savings convert to wall-clock only through the critical
  path; under ~5× parallelism much of a saved file's time was already
  overlapped. When the heavy tail is flat, further per-file work has
  diminishing wall-clock returns.

## Repository-wide mode

For a repo-wide effort (not a single hot file):

1. **Snapshot first** (lean-elaboration-test), then triage the top-30 into
   cost classes: include-block typeclass families (cache), tactic-bound
   arithmetic (lever 2), simp-bound (lever 3), import-bound (lever 1 on
   consumers, or leave), orchestrators/facades (leave), genuine analytic
   content (leave), diffuse-typeclass (leave/accept).
2. Fix the **roots**, expect transitive gains; if the ten downstream files
   don't improve, that's diagnostic, not bad luck.
3. **One intervention per commit**, perf-only commits (no statement changes —
   if a proof restructuring seems needed, profile first and ask), A/B
   evidence in the commit or report.
4. Re-run the snapshot at matched parallelism to score the work; write
   the dated report; keep the heavy-tail tier counts (≥10/20/30s) as the
   local trend metric.
5. **Codify demonstrated local invariants in the repo's agent instructions** —
   for example, caches in measured hot areas or profiling before a split.
   Keep local policy separate from portable guidance.
6. Know when to stop: when the tail is 3 files of diffuse typeclass and the
   only lever left is the critical path, further per-file tuning is not worth
   agent time.
