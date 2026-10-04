---
name: lean-project-architecture
description: Use when planning a Lean formalization, selecting and freezing author-approved declarations, choosing module boundaries, designing reusable APIs, or staging a large proof project into stable phases.
---

# Lean project architecture

Use this skill when the main task is project design rather than one proof.
Turn the mathematical program into stable source-facing Lean declarations,
ordinary implementation modules, and a dependency graph that can be built
incrementally. Repository rules override this skill.

## The constitutional surface is actual Lean code

Select a small surface: main roots, subsection or induction gates, and
definitions whose meaning changes them. Do not freeze every helper lemma.

Only an actual final Lean declaration can be approved, manifested, frozen, or
used as a dependency-graph anchor. Markdown “contracts,” candidate APIs,
tracked probes, placeholder declarations, temporary carriers, fallback bodies,
and promises of later characterization are planning debris, not mathematics.
Pre-approval elaboration may use an untracked temporary file containing the
exact intended final command; delete it after use.

For each source-facing declaration:

1. pin the mathematical source, errata, and author rulings;
2. transcribe its premises, conclusion, quantifier order, constant/witness
   scope, and split/joint policy;
3. identify and recursively inspect every meaning-carrying carrier, definition,
   typeclass, and bundled assumption;
4. elaborate the exact final theorem type or exact final definition body;
5. obtain independent source/binder/semantics review;
6. show the complete Lean command to the author; and
7. only after approval, put one declaration in one frozen file and bind its
   source, path, fully qualified export, frozen bytes, and state in a manifest.

A topic list or source transcription is useful planning evidence but has no
declaration status. Old Lean code and old graphs are evidence to mine only
after the source-facing code is fixed.

## Freeze keystone theorem statements

An exact author-approved keystone proposition or theorem should initially have
the manifest-bound proof body `by sorry` and state `DRAFT_SORRY`. Freeze it
before graph extraction and proof assignment, rather than allowing its type to
track proof convenience. Its type, binders, imports, and meaning-carrying
definitions are already final. It is `FROZEN_UNPROVED`, not proof progress, and
production/provider modules may not import or consume it.

Allow this only in one-declaration frozen files with manifest identity, source
and declaration hashes, a named provider, and enforced quarantine. All other
`sorry`, all axioms, and every provisional definition remain forbidden.

Definition types and bodies are never provisional and neither contain nor
depend on a draft placeholder. A genuine manuscript-defined predicate may be
a literal `def : Prop`; a theorem-shaped predicate, assumption package, result
bundle, or generic “input/bridge/consequence” proposition may not replace a
theorem.

## Source-characterized definitions

A definition is acceptable only when its body already denotes the manuscript
object on its whole public carrier. Do not use an over-broad carrier plus an
`if`/`dite`/zero/default branch, choose an arbitrary non-unique witness, or
land a reconstruction whose source identity remains a future theorem.

If the source defines an object as the unique object satisfying `Φ`:

1. freeze the exact well-definedness theorem `∃! x, Φ x` as a theorem goal;
2. prove, seal, and independently audit it;
3. define the object from that proved theorem; and
4. land the definition together with a separately named, sorry-free theorem
   asserting its full source characterization and uniqueness.

The well-definedness theorem may not assume response existence, integrability,
linearity, quadraticity, representability, or another proof step unless the
source states it as a premise. Those are dependencies to prove and apply. A
Classical.choose from the proved ∃! is permitted; a fallback or non-unique
choice is not.

Treat the definition and characterization theorem as one semantic unit:
give each a manifest entry, land them in the same commit, version and audit
them together, and route every downstream graph node through
the characterization theorem rather than the raw result type. A literal source
formula or predicate may instead be defined directly after its body and carrier
have passed the same audit.

## Dependency and module architecture

1. Build the source dependency graph against exact frozen exports.
   - distinguish external black boxes, reusable infrastructure, and
     paper-specific steps;
   - make graph edges proof obligations, never added hypotheses;
   - record alternative routes explicitly instead of conjoining them;
   - review topology independently.
2. Put theorem providers below anchors in the import DAG. Providers target
   separate exports and never import drafts. Until a frozen anchor is sealed
   and audited, its registered provider module/export is itself quarantined
   from every other consumer.
3. Keep reusable infrastructure separate from paper-specific assembly.
4. Put declarations in the earliest focused module where they naturally belong.
5. Minimize imports in foundational files.
6. Search Mathlib and approved upstream APIs before inventing definitions.
7. Build APIs before downstream proofs:
   - the real definitions;
   - source characterization and basic access lemmas;
   - extensionality and simplification lemmas;
   - stable notation and coercion policy.
8. Split work into phases with stop/go checkpoints. Seal a theorem by changing
   only its proof body to a short `by exact Provider.result`, then run exact
   statement, axiom, and source audits.

## Lean module system (when supported or required)

When the selected Lean toolchain and project policy use the module system,
design every regular `.lean` file as a module from the start. A module cannot
import a non-module file, so mixed dependency trees must be ported bottom-up.
Do not impose this layout on a toolchain or established project that does not
support or require it.

- **File shape.** Copyright comment; `module`; imports; module docstring;
  `public section` (or `@[expose] public section`).
- **Imports.** `public import` whatever the public interface needs; plain
  `import` for proof-only dependencies.
- **Exposure.** Definition bodies are hidden unless `@[expose]`, even from
  exported theorems in the same file. Expose source-facing, frozen and
  Challenge definitions.
- **Dependencies.** Check at planning time that every dependency is modular.
  Port bottom-up, before freezing statements when the order is still open.
- **Size.** Follow the project's limit. Registry submissions may impose a
  10,000-line cap.
- **Checks.** Run [scripts/check_lean_modules.py](scripts/check_lean_modules.py)
  `--root <repo>` when the repository adopts this module/registry profile
  (stage new files first; it reads the git index). It enforces the module
  header, configured line cap, and no symlinked `.lean` files. If the project
  contains `comparator.json`, it also applies the bundled registry checks.
  Its lexer helpers are the model for a project's own checkers.

Read [references/module-system.md](references/module-system.md) before writing
or porting a repository that uses Lean modules, and its "Checker scripts"
section before writing or porting any script that reads modular Lean source.

## Statement-integrity rules

- A source-facing theorem has exactly source premises, standing assumptions,
  typing data, and explicit author rulings. Proof obligations stay in proofs.
- Expand project-owned structures and typeclasses during audit; one bundled
  argument can hide dozens of excess hypotheses.
- Audit binder order for uniform constants. An existential `C` must precede
  every parameter on which the source says it is independent.
- If one source lemma is split, require explicit author approval. Preserve a
  shared constant or witness in one joint declaration unless independent
  choices are expressly allowed.
- Conditional helpers are ordinary internal lemmas with distinct names. They
  never certify or replace the source-facing theorem.
- Frozen declarations are immutable. A defect requires an author-approved
  versioned successor and invalidates dependent graph/audit evidence; never add
  a premise or silently substitute a helper.

## Performance and maintenance

- Keep files focused and within repository size limits.
- Prefer small helper lemmas over monolithic proofs.
- Obey repository heartbeat policy; a default-heartbeat failure is an
  architectural signal when overrides are forbidden.
- Profile before changing architecture or adding typeclass caches.
- Treat linter cleanliness and build stability as design concerns.
- Preserve other sessions' files and follow project-specific build, cache,
  staging, and landing rules.

## References

Read [references/project-architecture.md](references/project-architecture.md)
for definition engineering, file organization, Mathlib-facing conventions,
performance guidance, and cleanup expectations. Read
[references/module-system.md](references/module-system.md) for module-system
file shape, visibility, porting, and conditional registry limits.
