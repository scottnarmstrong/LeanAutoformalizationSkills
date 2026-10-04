# Project Architecture for Research Formalization

> **Sources:** Mathlib contributing documentation; Baanen et al., "Growing Mathlib"
> (2026); Massot's Blueprint tool; Tao's PFR experience; Mathematics in Lean
> (Avigad & Massot). For compilation debugging, see
> [compilation-errors.md](https://github.com/cameronfreer/lean4-skills/blob/main/plugins/lean4/skills/lean4/references/compilation-errors.md).
> For performance, see
> [performance-optimization.md](https://github.com/cameronfreer/lean4-skills/blob/main/plugins/lean4/skills/lean4/references/performance-optimization.md).

## Scoping

1. State the top-level theorems precisely before writing code.
2. Map the intermediate dependency chain.
3. Survey Mathlib coverage for every concept in the chain.
4. If targeting Mathlib, post your plan on Zulip early.
5. Choose the right generality: `CommMonoid` when possible, `Field` only when needed.

### Faithfulness Gate For Formalizing A Paper Argument

When the user asks to formalize a theorem of the form "assumption A implies
conclusion B", the public theorem must not assume intermediate propositions
whose mathematical content is already one of the proof steps from A to B.

Bad pattern:

```lean
theorem final_from_A
    (hA : A)
    (hStep1 : Step1Consequence)
    (hStep2 : Step2Consequence)
    (hFinalBridge : AlmostB) :
    B := ...
```

This is a scaffold, not a formalization of the implication.  It may compile
without sorries and still fail the user goal.  If an intermediate estimate is
needed, prove it as a theorem from concrete definitions and approved imported
theorems before using it downstream.

Before implementation, freeze and audit the exact final theorem signature.  The
audit must reject:

- theorem hypotheses named or shaped like the desired intermediate conclusions;
- generic `...Consequence`, `...Input`, `...Bridge`, or `BudgetDomination`
  predicates that package hard analysis;
- "conditional certification" when the user asked for an unconditional
  implication relative to specified assumptions;
- any statement that would still be true if the main analytic work were simply
  assumed.

## Definition Engineering

- **No provisional mathematics.** A source-facing definition must have its
  exact final body and source meaning before it is frozen. Do not track or
  approve candidate APIs, fallback values, valid-locus totalizations, arbitrary
  witness choices, or definitions whose claimed meaning is deferred.
- **Characterization-defined objects.** If the source defines an object as the
  unique object satisfying `Φ`, first prove and audit `∃! x, Φ x`. Only then
  define the object, and land it with a sorry-free theorem asserting the full
  characterization and uniqueness. Downstream proofs use that theorem, not
  merely the object's codomain. The existence/uniqueness theorem may not assume
  its proof steps. A choice from the proved `∃!` is permitted; a fallback or
  non-unique choice is not.
- **Use Mathlib's definitions.** Prove equivalence if yours differs.
- **Typeclasses for structure:** `[CommRing R] [TopologicalSpace R] [TopologicalRing R]`
- **Bundled morphisms:** `R →+* S` (RingHom), not bare functions.
- **Prop-valued classes:** `[IsNoetherian R M]`, `Is*` prefix for nouns.
- **API lemmas immediately:** `@[simp]`, `@[ext]`, coercions, constructors.
- **Mark reducibility:** `@[reducible]` or `@[irreducible]` deliberately.
- **`autoImplicit false`** in lakefile to prevent free variables.

## File Organization

- One focused topic per file. ≤ 1500 lines (linter warns).
- Minimize imports. Each unused import slows compilation.
- File header: copyright, authors, `/-! ... -/` module docstring.
- Import order: Mathlib first, then project files. No blank lines between.

## The Blueprint Model

For projects with 20+ interconnected lemmas, use Patrick Massot's
[leanblueprint](https://github.com/leanprover-community/leanblueprint):
LaTeX proof sketches linked to Lean declarations, dependency graph, status tracking.
See Tao's PFR project for the model workflow.

## Mathlib Type Hierarchies

```
Algebra:     Monoid → Group → CommGroup
             Semiring → Ring → CommRing → Field
Topology:    TopologicalSpace → UniformSpace → MetricSpace
             T1Space → T2Space → CompactSpace
Analysis:    NormedAddCommGroup → NormedSpace → CompleteSpace (Banach)
             InnerProductSpace → CompleteSpace (Hilbert)
Morphisms:   OneHom → MonoidHom (→*) → RingHom (→+*) → AlgHom (→ₐ)
```

Use the weakest structure that suffices.

## Elaboration

- Profile slow proofs: `set_option profiler true in`
- `simp only [...]` not bare `simp`. Use `simp?` to discover.
- Follow the repository's heartbeat policy. If local overrides are permitted,
  scope a measured override to one declaration; otherwise split or refactor.
- Split large proofs into helper lemmas.
- Document elaboration workarounds in a shared markdown file.
- For deep typeclass debugging, see
  [instance-pollution.md](https://github.com/cameronfreer/lean4-skills/blob/main/plugins/lean4/skills/lean4/references/instance-pollution.md).

### Profile Before Architecture Changes

Treat elaboration work like performance engineering:

1. Record a quiet sequential baseline for the file.
2. Read cumulative profiler categories before choosing an intervention.
3. Make the smallest plausible change.
4. Recheck the file directly.
5. Rerun the same profile and keep only measured wins.

Use local proof edits for local proof costs:

- broad `simpa`/`simp` cost → exact definitional bridges, `rfl`, targeted `rw`,
  or `simp only`;
- heavy `nlinarith`/`linarith` interpretation → named inequalities,
  monotonicity lemmas, and `calc`;
- CLM/matrix typeclass cost → explicit arguments, small reusable API lemmas, or
  head-class caches when the file structure warrants them.

Use architecture changes only when the profile supports them. File splitting
helps if it reduces the variable/typeclass burden per theorem; it does not help
when import deserialization is the dominant cost.

### Head-Class Caches For Large Include Blocks

When creating or cloning a Lean file with a large `variable`/`include` block,
especially in a pattern-following theorem family, audit recurring typeclass
heads. If the file repeatedly carries classes such as
`[NeZero d]`, `[MeasureTheory.IsProbabilityMeasure P]`, or `Vec d`-indexed
instances, add a closed top-level cache section before the namespace:

```lean
section
variable {d : ℕ} [NeZero d]
  {P : MeasureTheory.Measure (CoeffField d)} [MeasureTheory.IsProbabilityMeasure P]
private instance : NeZero d := inferInstance
private instance : MeasureTheory.IsProbabilityMeasure P := inferInstance
end

namespace Project
```

Top-level placement matters: caches inside the namespace do not propagate
through oleans to downstream importers. Prefer importing the cached parent file
when cloning a slow `Base`/`Finite`/`Auxiliary` variant; if the clone must
duplicate the variable block, duplicate the cache too. Do not split files for
performance unless profiling shows that the split also reduces the variable
block or typeclass burden.

For project rebuild hygiene, avoid `lake clean` in large projects with cached
dependencies. Use targeted removal of project oleans or per-file oleans when a
fresh build is needed.

## Contributing to Mathlib

Follow https://leanprover-community.github.io/contribute/. Key points:
- Do not fork — use branches on the main repo.
- Naming, style, 100-char lines, docstrings, `#lint` clean.
- Human reviewer checks math, code quality, naming.
- Only the strongest approach to a topic is included.
- See also official `leanprover/skills` repo: `mathlib-pr`, `mathlib-review`.

## Cleanup Checklist

- [ ] Zero remaining draft or unregistered `sorry`s at release; during
      development, only manifest-bound frozen keystone theorem anchors may use
      the exact body `by sorry`
- [ ] `#lint` clean
- [ ] Docstrings on all public definitions
- [ ] Module docstring on every file
- [ ] `simp only [...]` (no bare `simp`)
- [ ] No `exact?`/`apply?` in finished code
- [ ] Minimal imports
- [ ] ≤ 100 char lines, ≤ 1500 line files
- [ ] Mathlib naming conventions
- [ ] Scoped `set_option`
