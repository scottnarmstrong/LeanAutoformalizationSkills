# Elaborating analysis proofs with structured carriers

## Scope

Nested carriers such as `EuclideanSpace ℝ (Fin d)`, bundled `Lp` elements,
continuous maps, and dependent subtypes can make otherwise small proofs costly.
The carrier is only one possible cause. Imports, reducibility, implicit
arguments, large local contexts, and automation can produce similar symptoms.

Profile a warm build first. Record the Lean and Mathlib versions, dominant
profile phase, wall time, and exact declaration. Apply one intervention at a
time and compare equivalent runs.

## Diagnose before changing the carrier

Typical signals of elaboration trouble include time in `isDefEq`, `whnf`, or
typeclass synthesis; metavariables whose printed types appear identical; and a
small theorem call becoming expensive only inside a large context.

Useful probes:

1. Reproduce the declaration in a narrow file with the same imports.
2. Make important types and implicit parameters explicit.
3. extract the suspect call into a helper with a minimal context.
4. Compare an explicit rewrite with `simp` or `simpa`.
5. Profile the file and a representative downstream consumer.

Do not raise heartbeat limits, add axioms, or add theorem hypotheses as a
substitute for fixing the proof. A repository may impose stricter rules.

## Reduce the local elaboration problem

### Extract narrow helpers

A helper with only the needed variables can isolate expensive unification and
make the main proof a simple application:

```lean
private lemma image_bound
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    {f : E → ℝ} (h : /* exact assumptions */) :
    /* exact conclusion */ := by
  exact /* Mathlib theorem with explicit arguments */
```

This is useful only when the helper states genuine mathematics. Do not move an
unproved proof step into its assumptions.

### Separate representation changes from estimates

Prove a distance inequality before converting it to ball membership:

```lean
have hdist : dist x y ≤ r := by
  exact distance_estimate ...
have hx : x ∈ Metric.closedBall y r := Metric.mem_closedBall.mpr hdist
```

Likewise, isolate coercions between bundled and unbundled functions, restricted
measures, subtypes, and continuous linear maps. This reveals which conversion
is expensive and keeps estimate proofs readable.

### Prefer the API matching the goal

- Use `eLpNorm_mono_real` when the majorant is real-valued and
  `eLpNorm_mono` when both sides are norms.
- A rewrite such as `tendsto_sub_nhds_zero_iff` can avoid synthesizing the
  additive structure required by a generic method call.
- For `ContDiffAt.differentiableAt`, a `WithTop` ordering side goal may be
  discharged by `simp` when arithmetic tactics do not match its type.
- After `gcongr`, inspect remaining goals; newer Mathlib versions may close
  branches automatically.

These theorem names and signatures can change. Confirm them with repository
search or `#check` in the pinned version.

### Control normalization

Use `rw`, `change`, typed intermediate facts, and `simpa only` when broad
simplification unfolds structured carriers or normalizes both sides into
different forms. For purely associative-commutative rearrangements, `ac_rfl`
is usually cheaper than `ring_nf`.

For a large expression, prove small identities first:

```lean
have hsum :
    (∑ i ∈ Finset.range (n + 1), f i) =
      (∑ i ∈ Finset.range n, f i) + f n := by
  simp [Finset.sum_range_succ]
```

Keep `Real.exp`, `Real.rpow`, norms, and integrals opaque while proving the
small scalar algebra that connects them.

## Choosing an ambient representation

`EuclideanSpace ℝ (Fin d)` provides an inner-product and Euclidean-norm API.
`Fin d → ℝ` provides a simpler Pi carrier whose default norm is generally the
sup norm. These are not definitionally interchangeable, even though their
finite-dimensional topologies and norms are equivalent.

Choose or change a carrier only after answering:

- Does the mathematics use an inner product, orthogonality, Euclidean balls,
  or a particular normalization?
- Which Mathlib theorem family will downstream proofs use?
- Will explicit norm-equivalence transports cost more than the current
  elaboration problem?
- Can the expensive boundary be isolated instead of migrated globally?
- Does profiling show that the carrier is actually dominant?

For coordinatewise or combinatorial work, a Pi carrier may be effective. For
Hilbert-space arguments, `EuclideanSpace` may provide the better API. A local
algebraic carrier plus explicit analytic transport is another valid design.

Bundled `Lp` and bare functions have a similar tradeoff. Bundled elements give
normed-space completeness and extensionality APIs; bare functions with
`eLpNorm` avoid some coercion and `toLp` bridges. Select the side that owns the
next theorem, and package the crossing in a tested helper.

## Instance-cache experiments

When profiling identifies repeated head-class synthesis in a large section,
a local private cache can be tested:

```lean
section
variable {ι : Type*} [Fintype ι]
private instance : Fintype ι := inferInstance
end
```

Cache only recurring head classes, keep the scope small, and A/B the file plus
downstream consumers. Placement and benefit depend on Lean's environment and
the import graph. Remove caches that do not show a repeatable improvement.

## Measure and function-space proof patterns

- In Fatou or dominated-convergence arguments, state the exact nonnegative
  `lintegral` bridge before converting to a real integral.
- Supply explicit boundedness or nontriviality data to order lemmas on
  `ENNReal` when inference cannot recover it.
- For matrix-valued integrals, use the Pi-type API (`Integrable.eval`,
  `eval_integral`) entrywise.
- In `Lp.ext` proofs, first prove one pointwise identity, then lift it to an
  almost-everywhere equality. Avoid one giant simplifier call across coercions.
- Put carrier transport in the lowest module that owns both representations;
  downstream theorem files should consume a small bridge API.

## Verification checklist

- The statement is unchanged in mathematical content and binder order.
- No axiom, placeholder, `sorry`, or proof-step hypothesis was introduced.
- The relevant file elaborates under the repository's normal heartbeat policy.
- Axiom checks and warning policy pass where required.
- The performance comparison used equivalent warm or cold conditions.
- Downstream consumers were checked when the change affects exported types,
  instances, or imports.
