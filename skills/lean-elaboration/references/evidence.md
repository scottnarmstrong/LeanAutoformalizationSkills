# Evidence base for Lean elaboration guidance

This is a portable record of repeated A/B observations from large Lean 4 and
Mathlib repositories. Project names, private file names, dates, and machine
paths are intentionally omitted. The observations identify mechanisms to test, not predicted speedups.
Private benchmark figures have been omitted; re-measure each intervention locally.

## Measurement corrections

Several corrections mattered more than any individual optimization:

- Build-log time is not own-file elaboration time. Parallel contention,
  dependency load, artifact serialization, and native compilation can inflate
  it. Observed build logs sometimes substantially overstated fixable own-file
  cost; direct profiles were needed to isolate it.
- Wall-clock comparisons require the same timing tool and comparable
  parallelism. User CPU is more stable across differently scheduled runs, but
  still needs the same target, toolchain, and source scope.
- A default build target can silently omit modules. One long-running report
  series missed a substantial subtree until the root target was audited.
- Presence of other Lean processes does not prove contamination. Treat a run
  as contention-bound when multiple signals agree: logged work rises while
  user CPU falls, implied parallelism shifts materially, and individual files
  move in opposite directions.
- Sub-second jobs may be absent from Lake's timing lines. State the visible
  fraction instead of presenting their sum as total CPU.
- Existing reports are evidence. Before diagnosing a new regression, compare
  the exact module set and read prior measurements; a remembered baseline may
  predate added modules or changed build coverage.

## Head-class instance caches

Top-level private instances can remove repeated closed instance searches in a
file with a large shared context. The successful pattern was:

1. Profile a file where cumulative typeclass inference is a material part of
   own-file elaboration.
2. Identify a repeated closed goal for a head class.
3. Add one top-level cache outside section-variable scopes.
4. Re-profile the file and representative consumers.

Results were sharply bimodal. One family of files saved tens of seconds each,
while most proposed caches were inapplicable, neutral, or slower. A redundant
cache above an already cached leaf made elaboration slower. Section-local
caches appeared to elaborate but did not help downstream declarations.

An especially important counterexample involved repeated goals shaped like
`SMul ℝ ?m`: the target type was still a metavariable. Adding a cache
lengthened search. Type ascriptions at the point where elaboration first needed
the type removed the repeated events and substantially reduced typeclass time.
Use `trace.Meta.synthInstance` to distinguish closed searches from open ones.

## Import narrowing and file splits

Consumer-side import narrowing produced some of the largest structural wins:
groups of consumers improved substantially with no theorem changes. The effective method was to enumerate the
provider's public API, check actual symbol and instance use, and build after
each first-pass removal.

Text-only unused-import guesses had a high false-positive rate, in observed audits, because instances and tactic
extensions were load-bearing without textual references.

Splitting a heavy module without changing what consumers import was a loss:
the same declarations still loaded, while extra import preambles and artifact
overhead were added. A split helps only when it narrows transitive closures or
creates genuinely independent branches in the import DAG. Do not re-export all
new leaves from the old core if reduced load is the goal.

## Arithmetic and simplification

Replacing broad nonlinear arithmetic closers with named inequalities,
monotonicity lemmas, `calc`, `positivity`, or `linarith only [...]` substantially reduced
tactic interpretation time in measured files. In
another case, extracting a pure real-algebra helper kept `Real.exp` and
`Real.rpow` terms outside `nlinarith` and substantially reduced file time.

`simp only` is valuable only when profiles show expensive simp calls. A
targeted edit reduced a dominant call by an order of magnitude. A blanket
file-wide narrowing where calls were already sub-second changed less than run
noise and was reverted. Screen individual calls first.

## Statement elaboration

When unattributed elaboration dominates, replace a suspect proof body with
`sorry` in an untracked experimental copy. If the cost is unchanged, the
statement is expensive. In observed cases expensive declarations remained expensive with their
proofs replaced, while similar declarations with simpler conclusions were cheap.

The cause was an unfolded, long hypothesis type passed as a dependent argument
to a function whose signature expected an `abbrev` for exactly that type.
Restating the hypothesis using the consumer's abbreviation preserved the
proposition by definitional equality and removed most of the elaboration cost in
the measured declarations.

A syntax-shaped repository sweep found dozens of similar-looking declarations,
but only a small subset were expensive. The pattern identifies candidates, not
proof of cost. Profile each declaration before editing it.

## Congruence search

When a profile attributes seconds to `Tactic.congr` and the outer function is
already known, replacing search with `refine congrArg f ?_` can remove most of
the cost. Measured files saw substantial reductions in tactic execution. Supply the
actual function; `congrArg _ ?_` often leaves the same inference problem.

## Diffuse costs and negative results

These interventions did not produce reliable wins:

- heartbeat increases, which move a failure threshold without reducing work;
- `attribute [reducible]` on instances, which can shift cost into
  definitional equality;
- derived-class “backup” caches;
- proof restructuring in files with thousands of small typeclass searches and
  no dominant head class;
- tuning import-only facade modules;
- structural helper extraction proposed from textual similarity alone;
- leaving `#print axioms` or other diagnostic commands in compiled sources.

One in-source axiom diagnostic accounted for nearly all measured elaboration in
its module. Keep axiom checks in untracked probes or a dedicated audit target,
while continuing to run them as part of proof-integrity verification.

## Machine shape

Compute both:

- the work floor: total project CPU divided by available cores;
- the critical chain: the longest weighted import path.

The larger constrains wall-clock. For a hypothetical build with 800 CPU-seconds
of work and a 120-second
critical chain, the lower bound is chain-dominated on eight cores
(`max(800/8, 120) = 120`) and work-dominated on four
(`max(800/4, 120) = 200`). An off-chain CPU saving can lower the work bound on
the smaller runner while leaving the larger runner's critical chain unchanged.
State which bound an optimization affects.

## Evidence standard

For each proposed change, preserve:

1. the baseline command, toolchain, target, and warm/cold state;
2. the dominant profile phase and the specific event or declaration;
3. one intervention at a time;
4. an A/B using the same conditions, with repeated wall-clock samples when
   profiler phase totals are unavailable;
5. the result, including null and negative results;
6. statement-fidelity, axiom, and repository build checks after the edit.

Do not carry numeric thresholds into a repository as policy unless its own
measurements support them.
