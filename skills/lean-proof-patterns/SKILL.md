---
name: lean-proof-patterns
description: Use when writing, refactoring, or debugging Lean proofs and you need a stable translation from mathematical reasoning into explicit tactics, controlled rewriting, or maintainable proof structure.
---

# Lean Proof Patterns

Use this skill when the work is primarily about proving things in Lean rather than planning a project or searching for existing lemmas. It is especially useful when translating informal mathematics into Lean, cleaning up a rough proof, or replacing exploratory tactics with checked-in code.

## Core Workflow

1. Classify the proof step before touching tactics.
   - introduction or elimination
   - rewriting or normal-form change
   - case split or induction
   - arithmetic or algebraic closure
   - extensionality or structure unpacking
2. Start with the simplest explicit proof shape that matches the mathematics.
   - `intro`, `rintro`, `obtain`, `constructor`, `use`
   - `have`, `suffices`, `show`, `change`
   - `calc` for chains of equalities or inequalities
3. During exploration, use search tactics freely.
   - `exact?`, `apply?`, `rw?`, `simp?`, `hint`
   - do not leave them in finished code
4. Before finishing, pin the proof down.
   - replace bare `simp` with `simp only [...]` when possible
   - replace search tactics with explicit lemmas
   - factor repeated proof fragments into helper lemmas

## Production-Proof Rules

- Prefer small `have` steps and `calc` blocks over large opaque tactic scripts.
- Use automation that matches the goal shape.
  - `ring`, `field_simp`, `linarith`, `nlinarith`, `omega`, `positivity`, `norm_num`
  - `gcongr`, `fun_prop`, `continuity`, `measurability` when the domain fits
- In performance-sensitive proofs, do not leave broad automation in place just
  because it closes the goal. If a large `nlinarith`/`linarith` is only combining
  already-named inequalities, replace it with monotonicity lemmas and a `calc`.
  Prefer `linarith only [...]` so the hypothesis set stays small. Treat
  `Real.rpow` and `Real.exp` expressions as opaque atoms when possible; extract
  the algebraic core over abstract reals if unfolding them causes excessive work.
- Follow the repository's linter policy. Unused proof-locals,
  dead `simp` arguments, do-nothing tactics, and `<;>` applied to a single goal
  are mechanical fixes. Audit an unused *binder in the statement* against the
  source before changing it. A source premise may remain necessary to preserve
  the approved statement even if this proof does not use it. A frozen signature
  changes only through an author-approved successor and renewed audits.
- Keep rewriting intentional.
  - `rw` for a specific rewrite
  - `simp_rw` under binders
  - `conv` only when targeted rewriting is genuinely needed
- Replace broad definitional bridges like `simpa [many, local, definitions]`
  with `exact`, `rfl`, or `dsimp` plus targeted `rw` when possible.
- Separate discovery from final form.
  - development proofs may use search and broad automation
  - checked-in proofs should be stable, readable, and predictable

## Statement Hygiene

The statement must say what you claim, independently of how far the proof has
got. When a step will not close, fix the proof; never reshape the goal into
something provable.

- A genuine predicate defined by the source, such as an induction state, may be
  a literal `def : Prop`, provided it takes the objects it constrains as
  parameters. A theorem-shaped predicate, standing-assumption package, result
  bundle, or generic “input/bridge/consequence” interface may not replace a
  source theorem. `def myEstimate : Prop := ∀ ...` consumed as
  `theorem main (h : myEstimate) : Goal` leaves the mathematics untouched and
  only hides it from the reader and from the status report.
- No placeholder definition and no fallback body. A definition must already
  denote the intended object on its whole carrier; do not add a default branch
  so that a later statement can quantify over an unfinished construction.
- No hypothesis that is a proof step, estimate, or witness of the target rather
  than a premise of the source. If the source proves `A → B`, intermediate
  claims belong in the proof or in helper lemmas; `A → Step → B` is a different
  theorem.
- No hypothesis that is the conclusion itself at a weaker scale, radius, or
  domain.

A conditional theorem is legitimate when every hypothesis is a source premise,
a separately approved standing assumption, or an external input recorded as a
trust boundary. It is not legitimate when a hypothesis is the part of the
argument that is unfinished. All of these forms elaborate and pass the build,
and naming one honestly in the handoff does not make the statement correct. A
text linter that checks placeholders and banned tactics will not catch them, so
check project-owned `Prop` definitions by hand and treat a nullary one as an
unproved theorem until shown otherwise. When the input you need does not exist,
stop and report the exact missing statement.

## Module Files

For repositories using Lean's module system, follow the pinned toolchain's
visibility rules and the project's chosen header conventions.

- **Header.** The file starts with a copyright comment, then `module`, then
  `public import` for what statements need and plain `import` for proof-only
  dependencies. The module docstring follows, then `public section`.
- **Definition bodies are hidden** unless the definition is `@[expose]`. A
  public theorem that needs to unfold a definition fails with "Not a
  definitional equality … must be exposed", even in the same file. This is
  verified for `rfl`; expect the same for `decide` and for cross-module
  unfolding. Fix it either by proving and using
  an unfolding lemma (`f_def`, `f_apply`), or by exposing a definition whose
  body is its meaning. Never weaken the statement to avoid the error.
- **Proofs are never exported.** Nothing downstream may depend on how a
  theorem was proved.
- **Registry interfaces.** If a publication registry imposes additional
  visibility rules on comparison, challenge, or solution files, apply those
  rules only to the relevant export interface.

See the `lean-project-architecture` skill's `references/module-system.md` for
the full rules.

## Debugging Heuristics

- If Lean is not seeing the goal in the right form, try `show`, `change`, or an explicit helper lemma before escalating to clever tactics.
- If automation nearly works, inspect what it wants and feed it the missing monotonicity, positivity, or side inequalities.
- If the proof is repeating the same shape, stop and extract a lemma instead of copying tactics.
- When the task is elaboration cleanup, profile before and after each candidate
  change, and keep only edits that improve the relevant profiler category.
  Treat wall time as secondary when the machine is busy.

## References

- Read [references/math-to-lean.md](references/math-to-lean.md) when you need a phrasebook from informal proof language to Lean proof moves.
- Read [references/tactics-and-automation.md](references/tactics-and-automation.md) when choosing tactics, deciding between exploration and production proofs, or debugging automation/performance issues.
