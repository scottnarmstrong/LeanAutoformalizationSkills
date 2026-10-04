# Portable Lean and Mathlib lessons

The theorem names below are useful search seeds. Verify signatures in the
project's pinned Mathlib version.

## Preserve dependencies and quantifier order

The allowed dependencies of a public constant are part of the theorem. These
statements differ:

```lean
-- The witness may depend on `x`.
theorem pointwise (x : X) : ∃ C : ℝ, P x C := by ...

-- One witness works for every `x`.
theorem uniform : ∃ C : ℝ, ∀ x : X, P x C := by ...
```

Audit every binder before an existential, including type indices, instance
arguments, record witnesses, and `let` bindings. If `h : R x` precedes `∃ C`,
then the witness may depend on both `x` and the proof or data `h`, even if only
some fields of `h` are meant to be permitted dependencies.

For every source-facing estimate:

1. copy the complete permitted dependency set from the source;
2. inspect Lean's binder order and implicit parameters;
3. inspect types and indices of bundled hypotheses;
4. inspect the actual witness used by the proof;
5. prove any local constant is bounded by a uniform one;
6. obtain an independent statement audit.

Monotonicity in a displayed constant helps only after the local witness has a
uniform upper bound. Keep branch-specific work constants separate until the
matching exponent or prefactor absorbs them.

Do not repair a dependency mismatch by adding assumptions that encode proof
steps. Change the statement's binder structure or prove the missing uniform
bound.

## Package PDE solvers in layers

For a variational PDE, a stable sequence is:

1. define the weak formulation;
2. prove invariance under any gauge or constant shift;
3. prove the energy identity and coercive lower bound;
4. prove uniqueness at the weakest useful level, often gradient equality;
5. build existence with the appropriate Hilbert-space theorem;
6. choose a canonical solution only after existence and uniqueness are clear.

For a closed constraint space, transport a closed submodule into an existing
Hilbert carrier rather than recreating the full Banach/Hilbert API. To prove a
generated submodule lies in an orthogonal or zero-integral constraint, define a
continuous linear functional, place generators in its kernel, package the
kernel as closed, and apply `Submodule.closure_le`.

When an integrability goal contains a coefficient acting on a gradient, first
obtain an `L²` bound for the coefficient-field product, then combine two `L²`
facts with the appropriate dot-product integrability lemma. This is often more
stable than proving the quadratic integrand directly.

## Small algebra beats global normalization

- For cancellation involving division, prove the exact small equality with
  `field_simp` under explicit nonzero hypotheses, then rewrite the inequality.
- For successor sums, use `Finset.sum_range_succ` in a local lemma and `ac_rfl`
  for reassociation.
- For finite nonnegative `ℓᵖ` estimates, search around
  `Real.rpow_add_rpow_le_add` and `Real.rpow_inv_rpow` before rebuilding a
  finite-dimensional norm proof.
- Write `Finset.sum` explicitly when notation at the end of a `calc` causes
  parser ambiguity.
- Give `Finset.sup'` its finset, nonempty witness, and function explicitly when
  the semilattice metavariable is stuck.
- Keep `Real.exp`, `Real.log`, and `Real.rpow` outside `ring_nf` and nonlinear
  arithmetic. Prove an algebraic lemma over named real variables.

Use `linarith only [...]` when a short linear certificate exists. Use
`nlinarith` only when products of hypotheses are essential, and keep its input
set explicit.

## Matrix and finite-dimensional APIs

For square real matrices, `Matrix.inv_def` expresses the inverse through the
determinant and adjugate. This often supports continuity or measurability using
`Continuous.matrix_det`, `Continuous.matrix_adjugate`, and `measurable_inv`.
Useful search seeds include:

- `Matrix.transpose_nonsing_inv`;
- `Matrix.inv_smul`, `Matrix.inv_diagonal`;
- `Matrix.nonsing_inv_mul`, `Matrix.mul_nonsing_inv`;
- `Matrix.mulVec_injective_iff_isUnit`;
- `Matrix.diagonal_mul`, `Matrix.mul_diagonal`;
- the `Matrix.swap_*` family.

Make matrix types explicit around overloaded inverse and entry projections:

```lean
Measurable (fun x => (((A x : Matrix (Fin d) (Fin d) ℝ)⁻¹) i j))
```

For matrix-valued Bochner integrals, remember that a matrix is an iterated Pi
type. Use `Integrable.eval`, `Integrable.of_eval`, and `eval_integral`
entrywise. Check both normed-space and Borel-space instances before debugging
the proof term.

To prove a matrix is scalar under symmetries, a direct route is: sign changes
kill off-diagonal entries, coordinate swaps identify diagonal entries, and
`ext` finishes.

## Measurability, locality, and transport

Keep these claims distinct:

- a deterministic observable depends only on a restriction;
- it is measurable for a restriction-generated sigma-algebra;
- compositions with a random field are measurable on the sample space;
- observables on separated regions are independent.

A semantic locality proof does not supply joint measurability. Define the
restriction map and its comap sigma-algebra, prove the observable measurable
there, then pull it back along the random field. Push independence to smaller
comap sigma-algebras with `indep_of_indep_of_le_left` and
`indep_of_indep_of_le_right` rather than unfolding independence on sets.

For finite families, build a measurable tuple, compose with a measurable sum or
average, and transport independence with `IndepFun.comp`. For an a.e. version
of a deterministic theorem, use:

```lean
filter_upwards [hAE] with x hx
exact deterministic_theorem hx
```

For measure-preserving transformations, package set membership, measure, and
integral transport once. Law invariance is often most reusable as a
Banach-valued integral statement; scalar entry corollaries can follow.

## Function spaces and limits

Bundled `Lp` elements are valuable when completeness and normed-space algebra
drive the proof. Bare functions plus `eLpNorm` can avoid difficult coercion
bridges. Keep both options available and cross the boundary in a small helper.

Useful patterns:

- `eLpNorm_mono` compares norms; `eLpNorm_mono_real` accepts a real majorant.
- `tendstoInMeasure_of_tendsto_eLpNorm` and
  `TendstoInMeasure.exists_seq_tendsto_ae` can turn norm convergence into an
  a.e.-convergent subsequence.
- `aestronglyMeasurable_of_tendsto_ae` supplies measurability of an a.e. limit.
- `MemLp.exists_boundedContinuous_eLpNorm_sub_le` supports density arguments:
  prove convergence for bounded continuous tests, then control approximation
  errors by Hölder.
- Restrict `MemLp` to a subset before transporting it across a scalar multiple
  or an explicitly equal measure.

Do not add unconditional shift-invariance simp lemmas for totalized integrals
or `eLpNorm.toReal`; state the required integrability hypotheses.

In `Lp.ext` proofs, first show the explicit pointwise identity, then convert it
to an a.e. equality. Broad `simp` across coercions and quotient representatives
is fragile.

## Useful analysis idioms

- For finite maxima of measurable real functions, search for
  `Finset.measurable_sup'`, `Finset.sup'_apply`, `Finset.mul₀_sup'`, and
  `Finset.sup'_mul₀`.
- Convert `gamma`-style real powers at natural exponents with
  `Real.rpow_natCast` when needed.
- Change tail-event membership to its underlying inequality before arithmetic.
- Recover a finite-measure instance from integrability of the constant-one
  function when the available hypothesis implies it indirectly.
- Pull constants through real integrals with the lemma matching the expression
  orientation, often `integral_const_mul`.
- For shifted derivatives, state the intermediate composition in the exact
  form Lean inferred, then normalize with `simpa [Function.comp]`.
- When a norm theorem leaves an implicit ambient space unresolved, supply the
  vector argument explicitly.

## Elaboration and module hygiene

When a theorem becomes slow after adding a proof-carrying index, avoid threading
that proof through a large dependent expression. Build a lightweight adapter or
a nondependent view near the boundary.

Avoid partial application of very large theorems while pinning only late
implicit parameters. Supply the main data explicitly or introduce small
constructor lemmas. Giant abbreviations that pre-wire dozens of arguments can
be more expensive than an explicit final application.

Narrow imports are a proof-engineering tool. If a large file is split, keep
shared definitions genuinely upstream and elementary cleanup lemmas in leaves.
Profile every new child; splitting without reducing repeated imports or local
contexts may only redistribute cost.

If typeclass synthesis dominates, test a scoped private cache for the recurring
head class. Do not cache derived classes indiscriminately. Validate the owning
file and downstream consumers, since instance placement can change exported
elaboration behavior.

## Public theorem surfaces and proof status

Separate internal recovery, transport, and witness theorems from source-facing
endpoints. Freeze the intended endpoint statement before polishing its backend.
Audit source binders, carriers, definitions, constant dependencies, and
consumption independently of compilation.

Compilation and `#print axioms` cannot detect a theorem that is true but weaker
than its source because of quantifier order. Conversely, a source dependency
edge does not assert that a Lean theorem exists or is proved. Maintain separate
records for source topology and Lean proof status.

Temporary hypothesis-driven scaffolding must have a discharge pass. If caller
surfaces keep growing, stop adding wrappers and decide which assumptions should
be proved, bundled as genuine standing data, made definitional, or removed.
Never treat aliases or theorem-shaped proposition packages as proof progress.

## Recording new lessons

A portable entry should include:

- the pinned Lean and Mathlib versions;
- a minimal code shape or theorem-name search seed;
- the observed profile phase or error;
- the intervention and why it is mathematically sound;
- an A/B check and any downstream regression check;
- limitations and conditions under which the advice should not be applied.

Exclude workstation paths, personal names, private project history, model
instructions, and campaign-specific timing claims.
