# Advanced analysis formalization patterns

These recipes preserve reusable detail from several analysis developments.
Names belonging to Mathlib are search seeds whose signatures must be checked in
the pinned version. Generic names in snippets are schematic.

## Weighted depth averages do not control spatial maxima

Suppose nonnegative weights `w j` sum to one over a depth index and a
multiscale quantity has the form

```text
sum j, w j * ‖max over spatial cells at depth j of X(cell)‖
```

The probability normalization is in `j`; it does not imply monotonicity in a
separate spatial scale. In particular, stationarity identifies the law of each
translate but does not identify a norm of a maximum over many translates with
the norm of one translate. Cardinality or maximal-inequality factors generally
remain.

Before simplifying a normalized multiscale expression:

1. expand the definition far enough to distinguish depth sums, spatial sums,
   and spatial suprema;
2. state exactly which index carries the probability weights;
3. determine whether stationarity applies to one observable or to a maximum;
4. prove the spatial comparison, including cardinality and root factors;
5. compare the Lean quantity with the source, which may use an average where
   the implementation uses a maximum.

This is also a constant-uniformity check: a constant independent of scale
cannot be obtained merely by renaming a scale-dependent spatial maximum.

## Weighted Neumann problems and gauges

For a coefficient-weighted Neumann problem, quotienting by constants or fixing
the mean-zero gauge makes coercivity visible. A reusable construction is:

1. choose a Hilbert carrier for mean-zero functions or a coercive graph norm;
2. define the weighted bilinear form;
3. prove boundedness from the coefficient upper bound;
4. prove coercivity from ellipticity and a Poincare/coercive estimate;
5. solve with `IsCoercive.continuousLinearEquivOfBilin` or the repository's
   Lax--Milgram wrapper;
6. transport the result back to the public mean-zero function type;
7. prove the weak equation and uniqueness in the fixed gauge.

If the coefficient acts on gradients in an `L²` Hilbert space, package the
pointwise coefficient action as an operator field once. Prove its norm bound
and measurability there instead of repeating pointwise arguments in every PDE
file.

Avoid a broad `simpa` when comparing the recovered solution with the graph
solution: unfold only the local abbreviations and apply the exact transport
lemma to the explicit term. This prevents simplification from erasing the
structure needed to match the theorem.

For forcing invariant under adding a constant, prove the gauge-invariance
lemma independently. On zero-trace test spaces this often follows from the
vanishing integral of the gradient, expanded coordinatewise.

## Closed Hilbert subspaces for constrained solutions

When the natural constraint is represented as a closed subspace of one `L²`
model but Lax--Milgram lives in an equivalent Hilbert model, transport the
subspace by `ClosedSubmodule.comap` along a continuous linear equivalence:

```lean
def transportedConstraint : ClosedSubmodule ℝ H :=
  constraint.comap equiv.symm.toContinuousLinearMap
```

After solving in `transportedConstraint`, map the vector back and use
`ClosedSubmodule.mem_comap` to recover membership in `constraint`.

For a constraint defined as the closure of generators, prove annihilation by a
continuous linear functional as follows:

1. define `ell : E →L[ℝ] ℝ`;
2. prove each generator belongs to `LinearMap.ker ell.toLinearMap`;
3. view the kernel as a closed submodule;
4. apply `Submodule.closure_le`.

This pattern handles orthogonality, zero averages, and vanishing component
integrals without unfolding topological closure.

Recovering a concrete zero-trace witness may require separate bridges:
orthogonality gives a potential representative, zero-average data fixes the
affine ambiguity, and a trace theorem upgrades the representative to the
zero-trace type. Keep these as audited mathematical lemmas; do not add them as
hypotheses to the final existence theorem.

When normalizing an integral by a positive volume, make the inverse sign fact
explicit if `positivity` is brittle:

```lean
have hvolInv : 0 ≤ volume⁻¹ := inv_nonneg.mpr hvolume.le
```

## Finite sums and real powers

For `q ≥ 1` and nonnegative `f`, the finite inequality

```lean
(Finset.sum s fun i => f i ^ q) ^ (1 / q) ≤
  Finset.sum s fun i => f i
```

can be proved by induction using `Real.rpow_add_rpow_le_add` for the two-term
step and `Real.rpow_inv_rpow` to normalize powers. This is often lighter than
building a finite-dimensional `Lp` instance.

For finite geometric sums over ranges, search for
`geom_sum_Ico_le_of_lt_one`, rewrite with `Finset.range_eq_Ico`, and keep the
simplifier set narrow:

```lean
simp only [Finset.range_eq_Ico, pow_zero, div_eq_mul_inv, one_mul]
```

If binder notation fails at the end of a `calc`, use the explicit form
`Finset.sum s (fun i => ...)`. If `Finset.sup'` leaves a semilattice
metavariable, supply `s`, its nonempty witness `H`, and `f` explicitly.

Variable real powers need explicit endpoint branches. For a positive exponent
at `x = 0`, use `Real.zero_rpow` with its nonzero-exponent side condition.
At exponent zero use `Real.rpow_zero`; do not expect `simp` to infer a
variable-exponent side condition.

## Matrix measurability and integration

Write the matrix type around overloaded inverse and projection operations:

```lean
Measurable (fun x => ((((A x : Matrix ι ι ℝ)⁻¹ : Matrix ι ι ℝ)) i j))
```

For inverse measurability, `Matrix.inv_def` reduces the task to determinant,
adjugate, scalar inverse, and scalar multiplication. Search for
`Continuous.matrix_det`, `Continuous.matrix_adjugate`, and `measurable_inv`.

For a restricted matrix field defined with an `if`, function-level `simpa` may
not see the intended equality. Use `measurable_pi_iff`, `convert` one entry at
a time, then finish by `funext` and `by_cases hx : x ∈ U`.

A type synonym for matrices may have a measurable-space instance without the
`BorelSpace` instance needed by Bochner integration. Expose the underlying Pi
type when a local bridge is mathematically correct:

```lean
instance : BorelSpace (Matrix ι κ ℝ) := by
  infer_instance
```

Check both layers: matrix normed-space infrastructure and Borel/measurable
infrastructure are supplied by different imports.

For `F : Ω → Matrix ι κ ℝ`, use the iterated Pi API:

```lean
MeasureTheory.Integrable.eval
MeasureTheory.Integrable.of_eval
MeasureTheory.eval_integral
```

Apply `Integrable.eval` twice to obtain entry integrability, and
`eval_integral` twice to rewrite `(∫ x, F x ∂μ) i j`. A single integrability
witness for the whole matrix should usually be projected to blocks or entries,
rather than replaced by many independent assumptions. When a negated lambda
does not match `Integrable.neg`, try the pointwise-shaped `Integrable.neg'`.

## Operator-valued maps and norms

For `T : Ω → (E →L[ℝ] F)`, the standard evaluation bridge is
`ContinuousLinearMap.measurable_apply`. If a construction is linear from a
finite-dimensional source, define its `LinearMap`, use
`LinearMap.continuous_of_finiteDimensional`, and obtain measurability from
continuity.

For operator bounds, search first for
`ContinuousLinearMap.opNorm_le_bound` and
`ContinuousLinearMap.opNorm_le_iff`. Supply the pointwise estimate
`‖T x‖ ≤ C * ‖x‖` explicitly.

If the source or target may be trivial, avoid introducing a `Nontrivial`
instance merely to simplify an operator-norm inequality. A literal scalar
multiple bound may close with `norm_smul_le`; a zero branch may close after
`rw [norm_zero]`. This keeps dimension-zero cases valid.

## Lebesgue differentiation for multiscale projections

For a Pi space with the sup norm, metric balls are coordinate boxes; useful
search names include `closedBall_pi`, `ball_pi`, `Real.closedBall_eq_Icc`, and
`Real.ball_eq_Ioo`. This observation is carrier-dependent and should not be
transferred to a Euclidean-norm carrier without norm comparison.

For convergence of cell-average projections:

1. extend an integrable function outside the domain by an indicator;
2. select the unique cell at depth `n` containing `x`;
3. identify its average with an average over a shrinking ball or an admissible
   differentiation basis;
4. apply `IsUnifLocDoublingMeasure.ae_tendsto_average`;
5. rewrite back to the projection.

Parenthesize restricted measures in eventual statements:

```lean
∀ᵐ x ∂(μ.restrict s), Tendsto (fun n => P n f x) atTop (𝓝 (f x))
```

For shifted sequences use `Filter.tendsto_add_atTop_nat` instead of rebuilding
filter arithmetic.

## Pairing, telescoping, and projection limits

For a finite Besov-type pairing estimate, separate exact identities from
inequalities:

1. prove a one-cell decomposition;
2. prove a global one-step projection recursion;
3. telescope to an exact finite-depth identity;
4. apply `abs_add_le`, `Finset.abs_sum_le_sum_abs`, and discrete Holder.

If a definition hides `let D := cellsAtDepth ...`, reproduce the `let`, use
`change` to expose `D`, and then apply `Finset.sum_add_distrib` or
`Finset.mul_sum`. Reindex shifted ranges with `Finset.sum_range_succ'`.

An `eLpNorm.toReal` bound does not recover finiteness of the underlying
`eLpNorm`. If a dual test needs local `MemLp`, carry that fact in the
admissibility predicate. For a piecewise-constant projection, prove a one-step
`MemLp` lemma and transport it across an a.e. equality with `MemLp.congr_norm`.

When a normalized child measure is a scalar multiple of a restricted parent
measure, prove that measure identity by `Measure.ext`, `Measure.smul_apply`, and
`Measure.restrict_apply`. Then use

```lean
hf.restrict childSet
MeasureTheory.MemLp.of_measure_le_smul
```

to transport `MemLp` to the child. Keep the scalar inequality and its finiteness
side conditions explicit.

To pass from bounded tests to general `L^{p'}` tests:

1. prove projection contraction in `L^p`;
2. approximate the test by bounded continuous functions using
   `MeasureTheory.MemLp.exists_boundedContinuous_eLpNorm_sub_le`;
3. apply bounded-test convergence;
4. bound both approximation errors by Holder.

Take a supremum only after proving a pointwise bound for one admissible test.
Do not install shift-invariance simp lemmas without the integrability assumptions
that make totalized integrals and `toReal` expressions meaningful.

## Restriction sigma-algebras and finite-family independence

Let a restriction-generated sigma-algebra be a comap along a restriction map.
For nested regions, prove monotonicity from the composition identity for two
restrictions. Prove the observable measurable for the restriction-generated
sigma-algebra using a measurable factorization or an equivalent argument.
Semantic locality alone does not supply measurability.

Independence of the restriction sigma-algebras for every pair of separated
regions yields finite-family independence when each new support is separated
from the union of previous supports. Pairwise independence of individual
observables alone is insufficient. At the induction step, apply the region-level
assumption to the new support and the previous union. A reusable route is:

1. restriction-sigma monotonicity;
2. measurability of finite intersections in the union support;
3. an `iIndep` theorem for restriction sigma-algebras;
4. `iIndepFun` for measurable local observables;
5. `ProbabilityTheory.iIndepFun.indepFun_finset` for a finite block.

Build finite sums and averages by first building a measurable tuple, then
compose with `Finset.measurable_sum`, `measurable_pi_apply`, and
`measurable_const_smul`. Transport independence through the sum or average with
`ProbabilityTheory.IndepFun.comp`.

If notation such as `MeasurableSet[m] s` misparses in a dependent context,
write `@MeasurableSet Ω m s`. A measurable-space inequality `h : m₁ ≤ m₂`
acts as `h s hs`, with both the set and its proof.

Prove finite-color or block decompositions as equalities of observable values
before applying `norm_sum_le` or concentration inequalities. This separates
combinatorics from normed probability and avoids elaboration through wrappers.

## Concentration architecture

Do not assume a moment inequality recovers a sharp stretched-exponential tail.
For example, a Rosenthal bound with an extra factor of `p` may lose the moment
growth needed for a target Orlicz or tail class. Compare exponents first; use a
Chernoff/truncation proof when the moment route changes the claimed scale.

A maintainable concentration development separates:

1. scalar real inequalities;
2. mgf and tail transport;
3. truncation decomposition;
4. independent-sum endpoints;
5. application-specific block or partition averages.

For Young-conjugate exponent arguments, useful search seeds are
`Real.holderConjugate_iff_eq_conjExponent`,
`Real.young_inequality_of_nonneg`, and
`Real.summable_pow_mul_exp_neg_nat_mul`. For exponential integrability,
`hf.exp.aestronglyMeasurable` supplies measurability from `AEMeasurable f μ`,
and `Integrable.mono'` is often the final domination step.

Turn event membership into its scalar inequality with `change` before doing
arithmetic. Name set inclusions before calling `measureReal_mono`, and normalize
associativity before cancellation:

```lean
have hscaled : c * (A * t) < c * X ω := by
  simpa [mul_assoc] using hω
exact lt_of_mul_lt_mul_left hscaled hc
```

## Compiler-gate proof patterns

When the mathematics is finished but elaboration stalls at a small gate:

- Use `congrArg namedFunction h` rather than an anonymous lambda if the lambda
  creates a large inferred type. Define `namedFunction` locally with its full
  domain and codomain.
- For matrix equalities, `congrArg (fun M => M i j)` is usually a good,
  sufficiently typed projection; then simplify with entry formulas.
- Supply `MemLp` scalar/restriction transports explicitly instead of asking
  `simpa` to infer a measure identity and scalar bound together.
- In `by_cases h : condition`, give each branch its witness immediately. This
  prevents a later existential or subtype constructor from being inferred
  across incompatible branch contexts.
- When a tactic unexpectedly closes all goals, remove obsolete bullet branches
  and use the direct theorem (`mul_le_mul`, for example).
- Replace chained projections in large dependent signatures with a typed local
  abbreviation or a fully namespaced call.
- Split exact finite-parameter estimates from approximation or limit closure.
  The two proofs use different contexts and convergence APIs.

These are compiler-facing changes only when the resulting terms prove the same
statement. Re-audit binders and axioms after any refactor.

## Head-instance cache: conditions and validation

Test a private head-class cache only when profiling shows repeated typeclass
synthesis in a file with a large, recurring variable/include context:

Place a cache at top level, before the large consumer namespace or section,
with only the parameters it needs. A schematic cache shape is:

```lean
variable {ι : Type*} [Fintype ι]
private instance : Fintype ι := inferInstance
```

A cache inside the large section may reproduce the expensive context and fail
to help its consumers. Closed instance goals are better candidates than goals
whose target type is still an unresolved metavariable.

Cache head classes that recur literally. Do not add derived classes merely
because they can be inferred from the head class. Placement can affect importers
and differs across Lean versions, namespaces, and exported environments.

Validation must use the repository's guarded build procedure:

1. record a warm profile and wall time before the change;
2. change only the cache;
3. rebuild the owning file without invalidating dependency artifacts;
4. repeat enough runs to distinguish noise;
5. profile representative downstream consumers;
6. remove the cache if the gain is not repeatable or a sibling regresses.

If imports dominate, a cache is the wrong lever. If simplification dominates,
restrict the simp set. Splitting a file without reducing repeated contexts may
increase total work. Heartbeat options change a limit, not the underlying cost.
