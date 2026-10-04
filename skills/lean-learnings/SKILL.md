---
name: lean-learnings
description: Reusable Lean 4 and Mathlib lessons for analysis formalizations. Use when choosing an ambient carrier or repository layout, debugging elaboration and typeclass costs, preserving constant dependencies, or looking for recurring proof and API patterns.
---

# Lean Learnings

Use these empirical lessons as hypotheses to test, not as universal policy. Check
the repository's own instructions, inspect the definitions and imports in the
current version of Mathlib, profile before changing architecture, and A/B any
performance intervention.

## Reference map

| Situation | Reference |
|---|---|
| Organizing modules, imports, and namespaces | [references/repo_structure_policy.md](references/repo_structure_policy.md) |
| Diagnosing expensive carriers, instances, or large proofs | [references/Lean4_EuclideanSpace_Elaboration_Guide.md](references/Lean4_EuclideanSpace_Elaboration_Guide.md) |
| Planning an analysis, PDE, or probability development | [references/dos_and_donts.md](references/dos_and_donts.md) |
| Constant dependencies, quantifiers, Mathlib idioms, and proof shapes | [references/lean_learnings.md](references/lean_learnings.md) |
| Variational PDE, multiscale, Besov, locality, concentration, and compiler-gate recipes | [references/advanced_analysis_patterns.md](references/advanced_analysis_patterns.md) |

## Working principles

- Treat the dependency set and quantifier order of every public constant as part
  of the theorem. Audit types and instance arguments as well as named binders.
- Keep source statements, source dependency topology, Lean declarations, and
  Lean proof status distinct. A source dependency graph records source topology;
  it does not certify a Lean proof.
- Do not add axioms, placeholders, or proof-step hypotheses to make a theorem
  elaborate. Preserve the mathematical statement and change the proof or API.
- Profile the dominant phase before restructuring. Narrow imports, helper
  extraction, explicit arguments, local instance caches, and carrier changes
  address different causes.
- Treat `EuclideanSpace`, direct Pi types, bundled `Lp`, and bare functions as
  design choices with different APIs and elaboration costs. Change carriers only
  after checking the mathematics, downstream API, and measured cost.
- Keep nonlinear and transcendental expressions opaque while proving small
  algebraic side lemmas. Prefer controlled rewriting and minimal automation.
- Preserve dependency build artifacts according to the current repository's
  build policy. Never turn a project-specific cache rule into a general Lake
  command.
- Record a reproducible lesson: Lean/Mathlib version, minimal trigger, measured
  symptom, intervention, and an A/B check.

## Related skills

- `lean-workflow` — router for choosing the appropriate Lean workflow
- `lean-project-architecture` — declarations, module boundaries, and reusable APIs
- `lean-proof-patterns` — stable translations from mathematics to Lean proofs
- `lean-search-discovery` — finding existing Mathlib declarations
- `lean-elaboration` — profiling and improving elaboration performance
- `lean-statement-audit` — source, binder, semantics, consumption, and axiom checks
- `build-proof-dependency-graph` — source-level dependency topology
