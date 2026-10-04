---
name: lean-orchestrator
description: Coordinate a large multi-agent Lean 4 formalization around exact author-approved declarations, source-level dependency graphs, independent statement audits, bounded proof tasks, and safe landings. Use when planning or running parallel Lean work, reviewing proof status, landing integrated results, or repairing a campaign affected by statement drift or hypothesis smuggling.
---

# Lean formalization orchestrator

Read the repository's agent instructions, orchestration rules, plan, and active
ledgers before acting. Keep the process small enough that the author can inspect
and operate it. If an author has selected the frozen-anchor workflow below but a
repository policy still imposes a blanket zero-`sorry` development rule, treat
that as a policy mismatch to amend before graph extraction; do not silently
abandon statement freezing.

## Freeze keystone statements; only proofs may be provisional

The mathematical interface is the actual Lean declaration. A Markdown note,
“contract,” candidate declaration, tracked scratch probe, intended API,
placeholder type/body, convenience specialization, or promise of later
characterization is not formalization. It may not be approved, manifested,
frozen, used as a graph anchor, consumed by a proof, or counted as progress.

Before author approval, every theorem type and every definition type and body
must be the exact intended final declaration, with its real source carriers,
binders, quantifier order, and imports. A transient untracked file may check
that this exact command elaborates; delete it after use. Do not commit a
candidate or probe.

Once the author approves an exact keystone proposition or theorem, freeze it
immediately with the manifest-bound body `by sorry` and state `DRAFT_SORRY`.
Do not postpone the freeze until its proof is known: that recreates the
statement-drift failure this workflow is designed to prevent. The statement is
already final. It is `FROZEN_UNPROVED`, cannot satisfy a proved dependency, and
cannot be imported by production/provider code. Definitions neither contain
nor depend on this exception.

Every draft exception must be the sole public declaration in its frozen file
and have a unique manifest entry recording its source/version, exact export,
declaration/ABI hash, provider, exact allowed body, quarantine, and
`DRAFT_SORRY` state. All unmanifested `sorry`, `admit`, custom axioms,
placeholder definitions, and conclusion-shaped hypotheses remain forbidden.

A genuine predicate defined by the source, such as an induction state, may be a
literal `def : Prop`. A theorem-shaped predicate, standing-assumption package,
result bundle, or generic “input/bridge/consequence” interface may not replace a
source theorem.

## Admit definitions by their mathematics

A definition must already mean the source object on its whole public carrier.
Reject fallback zero/default branches, valid-locus-only semantics, arbitrary
witness choices, over-broad carriers with invented off-source behavior, and
reconstruction formulas whose equivalence to the source is promised for later.

When the source defines an object as the unique object satisfying a property:

1. write the exact well-definedness theorem (`exists`/`existsUnique`) using the
   real source carriers;
2. obtain independent source/binder/semantics review and author approval of its
   exact Lean type;
3. freeze it as a theorem goal, then prove, seal, and audit it;
4. only after that proof is available, write the final definition from it; and
5. land the definition with a separately named, sorry-free theorem asserting
   the complete source characterization and uniqueness.

The well-definedness theorem may contain only source premises, standing
assumptions, typing data, and explicit author rulings. Response existence,
integrability, linearity, quadraticity, symmetry, representability, and other
steps needed to prove it are graph dependencies, never binders. Once uniqueness
is proved, Classical.choose from that ∃! is legitimate; choosing from mere
existence or a non-unique family is forbidden.

The definition and characterization are one semantic unit, even when the
one-declaration-per-file rule puts them in separate files. Review and version
them together, give each a manifest entry, and land them in the same commit.
Every downstream graph node and proof depends on the
characterization theorem, not merely on the definition's codomain. If the
source instead gives a literal formula or predicate, audit and freeze that
literal body; do not invent an existence theorem merely for ceremony.

## Freeze the source-facing declarations

Do this before extracting their proof graph or assigning downstream proof work.

1. Select a small constitutional surface: main roots, subsection/induction
   gates, and definitions whose meaning changes them. Do not freeze every
   helper lemma.
2. Transcribe each target from a pinned source and approved errata. Record
   source ranges, premises, conclusion, quantifier order, constant/witness
   scope, split decisions, and unresolved questions. These notes are evidence,
   not a substitute declaration. Old Lean and old graphs are mining evidence
   only after this source pass.
3. Resolve every meaning-carrying Lean definition and carrier. Expand bundled
   assumptions and typeclass inputs far enough to expose their logical content.
4. Elaborate the exact final command transiently, then have a reviewer who did
   not write it compare that command directly with the source. Reject the first
   premise, field, fallback, or semantic choice not justified by source data,
   standing assumptions, typing, or an explicit author ruling.
5. Show the author the complete exact declaration: imports, explicit/implicit/
   instance binders, result, and a definition's whole body. Approval of a topic
   or prose summary is not approval of unseen Lean code.
6. After approval, place one public declaration in one frozen Lean file and add
   exactly one project-owned manifest entry binding its source, path, fully
   qualified export, provider identity when applicable, frozen bytes, and
   state. Every frozen Lean file must have exactly one manifest owner.

A source theorem may be split only when the author approves the split. Preserve
a shared constant or witness in one joint declaration unless the author
explicitly permits independent choices.

## Build the source dependency graph

Build the graph only after its root declarations are actual approved anchors.

- Give each source theorem, substantive proof step, and external input a stable
  node ID and line-addressable source range.
- Point roots at exact manifest entries and frozen exports.
- Treat every edge as an obligation to prove and consume a result. It is never
  permission to copy a predecessor's conclusion into a hypothesis.
- Route uses of a source-characterized definition through its proved
  characterization theorem.
- Review topology independently for omissions, circles, wrong edge direction,
  hidden external inputs, undischarged conditional premises, and false
  parallelism.
- Keep proof status separate from topology; never infer proof from a file's
  existence or compilation alone.

Assign work from the dependency-ready frontier. Off-frontier work needs a
recorded reason, such as source-faithful infrastructure needed by several
nodes.

## Prove below the anchors

Providers are ordinary Lean modules below frozen declarations in the import
DAG. They prove the exact target from graph predecessors and approved external
inputs; they never import a draft target. While an anchor remains DRAFT_SORRY, its
registered provider module/export is also quarantined from every module except
the provider itself and that frozen anchor. Otherwise production could bypass
the frozen audit by importing the implementation theorem directly.

For each worker:

- give one bounded target, exact source/anchor identity, owned files, allowed
  dependencies, validation command, stop condition, and handoff format;
- repeat repository hard rules verbatim when required;
- forbid edits to frozen declarations and extra source-facing premises;
- require the worker to stop if the exact API is insufficient; and
- allow conditional internal helpers only under distinct names, never as a
  source theorem or a closed graph node.

When the environment supports delegation and the user or repository authorizes
it, use capable reviewers or subagents for independent, non-overlapping work.
Choose model capacity and reasoning effort to match the mathematical and audit
risk. Keep source interpretation, shared APIs, and decisions affecting several
packets with the orchestrator. Review every diff and run the relevant checks;
do not infer success from a worker's prose report.

## Seal and audit

Seal a theorem by changing only its registered proof body to a short exact
assembly such as:

```lean
by exact Project.Provider.result
```

Then run the project checker, compile the frozen export, inspect its axioms,
and obtain an independent audit. Mark it `PROVED` only when all pass.

The audit must verify:

- the frozen export and bytes match the author-approved code;
- source ranges and every binder/quantifier match the source and rulings;
- every meaning-carrying definition, carrier, normalization, and source watch
  item is faithful;
- no hard proof step is an explicit, implicit, instance, or bundled hypothesis;
- the provider actually consumes the intended predecessors;
- every conditional premise is discharged at each application; and
- project-owned declarations contain no unauthorized `sorryAx` or custom axiom.

Compilation is not a fidelity verdict. One extra premise fails as decisively as
sixty-five. A producer for that premise does not repair the frozen statement;
the producer belongs inside its proof.

If an approved declaration is wrong, stop. Obtain an author ruling, create a
versioned successor, re-anchor the graph, and invalidate dependent proof/audit
status. Never repair a frozen declaration in place for proof convenience.

## Lean module system (when supported or required)

When the pinned toolchain and repository policy use Lean modules, every regular
`.lean` file in the campaign should be a module. A module cannot import a
non-module file, so confirm the whole dependency path before freezing bytes.
Registry intake rules apply only when that registry is a project target.

- **At planning.** For a modular project, confirm that the toolchain, Mathlib,
  and every project-owned dependency are modular. A non-modular dependency
  requires an explicit project decision: port it first, bottom-up. Never work
  around it.
- **Frozen files.** Anchors and definitions are written as modules before
  approval, so frozen bytes never need a header move later. The `module` line,
  the imports, `public section` and the namespace lines belong to the frozen
  prefix. Frozen and source-facing definitions are `@[expose]`. The bundled
  `check_frozen_anchors.py` requires every frozen file to be a module (a
  legacy repository awaiting its port passes only with
  `--allow-non-module`). It rejects a frozen declaration or sealed export
  that the module does not export (outside `public section` and not
  `public`), and resolves `_root_.X` to `X`.
- **Worker briefs.** Repeat the repository's module rule when it applies.
- **Landing checks.** In a project adopting this profile, reject any tracked
  `.lean` file other than `lakefile.lean` whose first non-comment token is not
  `module`, and any
  `.lean` file over the configured limit: run
  `../lean-project-architecture/scripts/check_lean_modules.py`. Port the
  project's own checkers to the module system as well
  (`../lean-project-architecture/references/module-system.md`,
  "Checker scripts").
- **Legacy repositories.** Port a non-modular repository as its own
  campaign: mechanical pass, rebuild and repair, fresh-checkout rebuild,
  axiom and Comparator reruns, and recorded semantics-neutral hash moves for
  frozen files.

The file shape, exposure rules, porting procedure, and conditional registry
limits are in
`../lean-project-architecture/references/module-system.md`.

## Evidence, reporting, and landings

Treat `PROVED` as a two-key result: a prover supplies concrete evidence and a
fresh auditor tries to refute it. Report exact declarations, checks and output,
axioms, unresolved questions, draft count/paths, graph changes, and any relative
or excused-input status. Never collapse conditional and unconditional results
into one progress number.

Every campaign status report must include these explicit fields:

```text
DRAFT_ANCHORS: <count and paths>
UNREGISTERED_SORRIES: <count and paths>
DRAFT_IMPORT_VIOLATIONS: <count and paths>
SEALED_THIS_TURN: <count and exports>
```

Follow repository build and shared-checkout rules exactly. Never add custom
axioms, heartbeat overrides, unregistered placeholders, or oversized files.
Run required cache and upstream-integrity checks before Lean/Lake. Never wait,
stop, or refuse work merely because another Lean/Lake process is running;
process presence is not evidence of an upstream write. Preserve other sessions'
files and index entries; stage explicit paths, inspect the entire staged diff,
and use the repository's safe landing procedure.

## Worker brief

```text
Goal: <one bounded result>
Ownership: <files/ledger region; no other edits>
Frozen target: <ID, path, fully qualified export, pinned source/rulings>
Allowed inputs: <proved graph predecessors and approved external inputs>
Frozen files: read only; stop if the declaration appears wrong
Checks: <targeted compile, exact application, axioms, lint/ledger>
Stop condition: <precise obstruction or budget>
Hard rules: <repository-mandated text verbatim>; when the repository uses Lean
  modules, require a `module` header, `public import` for the interface, and
  `@[expose]` where bodies must unfold
Handoff: files; approach; exact checks/results; axioms; uncertainty; ledger update
```

For an audit brief, require a refute-first posture, no source edits, direct
source comparison, full binder and semantic-definition classification,
exact-export compilation, and explicit statement/hypothesis/consumption/axiom
verdicts.
