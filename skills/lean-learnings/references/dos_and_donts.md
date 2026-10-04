# Planning an analysis formalization

These are design prompts, not universal requirements. Apply them to the
mathematics and the repository's declared scope.

## Start from a narrow dependency-complete theorem

Choose a theorem that exercises the essential interfaces without requiring the
most general geometry, weakest stochastic assumptions, or broadest function
space library. Write the exact source statement and its permitted constant
dependencies first. Generalize when a downstream theorem creates pressure.

Build prerequisite layers in dependency order. For a multiscale PDE project,
that might mean:

1. canonical geometric objects and finite combinatorics;
2. the small function-space package actually consumed later;
3. deterministic PDE or variational estimates;
4. semantic locality and measurability;
5. stochastic independence or concentration;
6. iteration and the final limit theorem.

This is an example sequence. Change it when the proof has a different spine.

## Model geometry and scale conventions explicitly

Pick one canonical boundary convention for partitions, often half-open cells,
and prove membership, disjointness, covering, parent/child, and measure formulas
early. Normalize scale indices relative to the object that owns them when that
removes irrelevant global arithmetic.

Avoid adding adaptive geometry before the fixed geometry supports the first
target theorem. Avoid open sets as primary partition objects when boundary
overlap creates persistent bookkeeping.

## Build only the analytic package consumed downstream

For Besov, Sobolev, or related spaces, begin with the definitions, projection
estimates, duality, embeddings, and completeness facts required by the target.
Projection or finite-scale formulations are often easier to combine with
multiscale geometry than a fully abstract library, but use the existing Mathlib
API when it already provides the needed theorem.

Keep ellipticity, dimension, exponent, and domain dependencies explicit.
Separate local work constants from public uniform constants. Fix gauges when a
PDE determines a solution only modulo constants.

## Separate deterministic, measurable, and stochastic claims

Prove deterministic locality as a semantic statement before using independence.
Define the relevant local sigma-algebras or restriction maps explicitly and
prove measurability when the observable is introduced. A pointwise local
observable is not automatically measurable for an intended sigma-algebra.

For random fields, choose between sample-space maps and laws deliberately. A
sample-space map with an action often makes stationarity and local independence
easy to state; a law-centric API may be better for invariance and pushforward
arguments. Provide a tested bridge rather than silently identifying the two.

Concrete product models are useful integration tests for abstract probability
interfaces. Strong finite-range assumptions can be a reasonable first target
when they match the source theorem; later weakening should be a separate phase.

## Keep APIs under pressure

- Bundle recurring structural data when it reduces real caller burden.
- Keep one-off scalar inequalities local unless they recur.
- Separate carrier transport from function-space packaging.
- Replace long chained projections in signatures with named accessors or typed
  intermediate facts.
- In `Lp.ext` proofs, prove a pointwise identity and then the a.e. equality.
- Remove disposable notation and wrappers that have no downstream consumer.

A long hypothesis list deserves an audit. Some arguments belong in a focused
structure, some should be proved locally, and some reveal that an unproved step
has been smuggled into the public theorem. Bundling does not legitimize an
assumption absent from the source.

## Common failure modes

- The geometry layer lacks exact partition and boundary lemmas.
- A general-purpose function-space library becomes a side project.
- Probability infrastructure is built before local observables exist.
- Iteration theorems carry many free scalar parameters rather than one coherent
  record or a few derived quantities.
- Foundational modules import application-level constructors.
- A theorem is weakened by placing `∃ C` after parameters from which `C` must
  be uniform.
- Mathematical elegance is confused with elaboration efficiency; abstraction
  is added without profiling or a consuming theorem.
- A source dependency graph is treated as evidence that Lean declarations are
  proved.

## Decision rule

Before adding a definition or abstraction, identify the next theorem that will
consume it, the source statement it supports, and the import direction it
creates. If those are unclear, keep the design local until evidence appears.
