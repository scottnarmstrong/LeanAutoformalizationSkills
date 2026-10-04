---
name: lean-statement-audit
description: Audit an exact manifest-bound Lean theorem or definition against its pinned mathematical source, with fail-closed binder, carrier, definition-body, characterization, consumption, and axiom checks. Use before approving a frozen declaration, after any frozen version change, before marking a source node proved, and before a theorem or section closure claim.
---

# Audit an exact frozen Lean declaration

The audit target is the actual frozen Lean declaration. A Markdown note,
“contract,” candidate, probe, helper, alias, facade, or similarly named theorem
is never a substitute.

For a theorem, proving B → A is not proving source statement A, even if B is
proved elsewhere. For a definition, constructing some inhabitant of the right
codomain is not defining the source object. Both errors move mathematics out of
the declaration while leaving Lean code that compiles.

## Only proofs may be provisional

Before author approval or manifestation, every theorem type and every
definition type/body must be the exact final source-facing declaration.
Pre-approval elaboration may use an untracked temporary file containing that
exact command; delete it after use. Tracked candidates and proposed Lean
surfaces have no audit status.

Only the proof body of an exact author-approved keystone theorem may be the
manifest-bound `by sorry` with state `DRAFT_SORRY`. This is the normal
statement-freezing stage, not a proof shortcut. Its statement is already final.
It is FROZEN_UNPROVED, unavailable,
non-importable by production/provider code, and not proof progress. Definitions
neither contain nor depend on this exception. Its registered provider
module/export is also quarantined from every consumer except the provider
itself and the frozen anchor until sealing and audit, so implementation code
cannot bypass the frozen export.

## Pin the exact target

Before reading implementation code, pin from the project manifest:

- versioned anchor ID;
- frozen path and fully qualified export;
- declaration kind and state;
- source revision, hash, and exact ranges;
- frozen declaration bytes/hashes;
- provider path/export for a theorem; and
- any author rulings and paired characterization export required by the
  repository workflow.

Recompute the mechanical values and stop on any mismatch. Every Lean file in
the frozen tree must have exactly one manifest owner. A graph node must name
this exact manifest entry and export.

Source transcriptions and audit reports are evidence only. They cannot override
the manuscript, adopted errata/rulings, or the exact author-approved Lean code.
A wrong declaration requires an author-approved versioned successor and
invalidation of dependent graph/audit evidence; never repair it in place.

## Reconstruct the mathematics independently

Read the raw source statement or definition and approved errata/rulings, not
its proof, old Lean code, or a prior audit summary. Record:

- all source premises;
- outer-to-inner quantifier order;
- exact conclusion or definiens/characteristic property;
- constant and witness scope;
- carrier, domain, normalization, notation, and endpoint conventions; and
- any author-approved split or domain-strengthening decision.

The source reviewer must be independent of the declaration author. Convenience
hypotheses, specializations, weaker conclusions, fallback values, and proof
obligations are not errata.

## Theorem audit: five-bin binder test

Enumerate every explicit, implicit, and instance binder. Recursively expand
project-owned assumption, witness, gate, structure, typeclass, and Prop aliases
so one bundle cannot hide many premises. Classify every logical input into
exactly one bin:

| Bin | Allowed meaning |
|---|---|
| SOURCE | Explicit premise of this source statement. |
| STANDING | Field of an independently audited source standing assumption. |
| TYPING | Pure type formation already implicit in the source conventions. |
| RULED | Exact author-approved correction, with ruling ID. |
| EXCESS | Any other result, estimate, gate, witness, or convenience premise. |

Any EXCESS is an automatic failure. A producer does not change its bin: apply
the producer in the proof and remove the binder. A source proof step is still a
proof step, not a theorem premise.

Also compare binder names/information/types, order, dependency, implicitness,
universal/existential scope, conclusion carrier, normalization, exponent,
window, and constant dependence. “C depends only on d” is enforced by
quantifier order, not prose.

The report must contain one row per expanded binder with a source/ruling
citation and counts for every bin. No table means no passing theorem audit.

## Definition audit: body and source characterization

First classify how the manuscript defines the object.

### Literal definition

If the source gives a formula or predicate, audit the complete Lean body
against that formula on the entire declared carrier. A genuine
manuscript-defined predicate may be a literal def : Prop. A theorem-shaped
predicate, assumption package, result bundle, or generic
“input/bridge/consequence” proposition fails.

### Characterization-defined object

If the source defines an object as the unique object satisfying Φ, the
definition is eligible only after:

1. the exact well-definedness theorem ∃! x, Φ x has been frozen, proved, and
   independently audited on the real source carriers;
2. the definition is constructed from that proved result, or from an already
   proved equivalent construction; and
3. a separately named, sorry-free theorem proves the complete source
   characterization and uniqueness for the exported definition.

Apply the theorem five-bin test to the well-definedness theorem itself.
Existence of response objects, integrability, linearity, quadraticity, symmetry,
representability, and other proof steps are EXCESS if assumed rather than
proved, unless the source explicitly states them as premises. Classical.choose
from the proved ∃! is legitimate; a choice from mere existence or a non-unique
family fails.

Audit the definition and characterization theorem as one semantic unit, even
when each occupies its own one-declaration file. Both must be manifested and
versioned together and landed in the same commit. Every downstream proof/graph use must depend on the
characterization theorem, not merely on the definition's result type.

Automatically fail a definition that uses or hides any of the following to
paper over missing mathematics:

- an if/dite/zero/default branch outside the source domain;
- a valid-locus-only theorem for a globally exported object;
- an arbitrary non-unique witness or selected family whose independence is
  deferred;
- an over-broad carrier with invented off-source semantics;
- a reconstruction or polarization whose equivalence to Φ is not already
  proved; or
- prose saying a later theorem will make the present definition faithful.

For any classical choice, identify the exact proved existence/uniqueness
theorem and verify choice independence through uniqueness. Check every
source-defining property—symmetry, normalization, locality, all-loadings
identity, or analogous structure—rather than accepting the codomain as a
surrogate.

A definition verdict has separate lines:

    BODY_MATCH: OK|FAIL
    PUBLIC_CARRIER: OK|FAIL
    WELL_DEFINEDNESS: OK|FAIL|N/A_LITERAL
    CHARACTERIZATION: OK|FAIL|N/A_LITERAL
    CHOICE_INDEPENDENCE: OK|FAIL|N/A
    DEFINITION_VERDICT: PASS|FAIL

Any failure is non-waivable. Compilation and a matching whole-file hash prove
only identity/elaboration, never mathematical meaning.

## Check semantic closure and exact use

Inspect every project-owned definition appearing in the declaration's type or
body, including notation, reducible aliases, structures, typeclasses, bundled
predicates, and coercions. Audit its body or bind it to an already audited
version. A meaning-carrying definition change is a declaration change even if
pretty-printed theorem text is unchanged.

Use transient, reproducibly generated Lean checks—never tracked candidate
files:

- for a theorem, an example at the independently reconstructed exact type whose
  body is exact Frozen.export;
- for a literal definition, checks of its elaborated type and defining
  equations;
- for a characterized definition, exact applications of its full
  characterization and uniqueness theorem; and
- at each conditional application, a term-level composition witness supplying
  every source premise from actual dependencies.

Delete temporary files after recording commands and output. Name reachability,
imports, graph edges, and file existence do not demonstrate term-level
consumption.

## Seal and axiom checks

For a sealed theorem, verify that the only frozen-file change from its approved
DRAFT_SORRY baseline is the proof body, now a short assembly such as
by exact Provider.result. Compile the frozen export and inspect #print axioms.
Unauthorized sorryAx, project axiom, or constant is fatal. Apply any explicitly
approved trust boundary exactly as local rules specify.

For definitions and their characterization theorems, require sorry-free axiom
closure before they are admitted as a semantic unit.

## Fail-fast procedure

1. Pin manifest identity, source, exact declaration bytes, state, and rulings.
2. Reconstruct the source mathematics independently.
3. Verify the frozen path/export/kind/bytes before inspecting helpers.
4. If a theorem is DRAFT_SORRY, verify its one allowed proof hole, record
   FROZEN_UNPROVED, and stop proof promotion.
5. For a theorem, emit the five-bin table; fail immediately on EXCESS.
6. For a definition, run the body/carrier/characterization audit; fail on any
   fallback, deferred semantics, missing proved well-definedness, or
   raw-codomain substitution.
7. Compile transient exact-type/characterization checks.
8. Verify source carriers, normalizations, scopes, and project watch items.
9. For sealed results, verify proof-body-only sealing and axiom cleanliness.
10. Compile producer-to-consumer composition for every closure claim.

For a draft anchor, emit these separate verdicts before stopping:

```text
DECLARATION_FIDELITY: PASS|FAIL
DRAFT_ALLOWLIST: PASS|FAIL
PROOF_STATUS: FROZEN_UNPROVED
```

A draft may pass declaration fidelity. It never passes theorem closure or
axiom closure.

A root cannot pass with inhabit=N/A, consume=N/A, “conditional assembly,” or
“characterization later.”

## Honest statuses and durable regressions

- FROZEN_UNPROVED: exact DRAFT theorem; unavailable.
- PROVED: exact sealed declaration, passing source/semantic and axiom audits.
- approved relative/trust status: exact declaration passes, with the named
  authorized input reported visibly.
- CONDITIONAL: internal helper with extra produced premises.
- SHELL: internal helper with unproduced premises.
- CLAIMED/PARTIAL: evidence is incomplete.

Only the exact frozen export can make its source node PROVED. Keep negative
regression fixtures that must fail:

1. a theorem with the right conclusion and 65 extra explicit hypotheses;
2. the same 65 obligations hidden in a project-owned bundle or Prop alias;
3. a definition returning the right codomain via a zero/default fallback; and
4. a definition whose audit admits that its source characterization will be
   proved later.

An audit process that passes any fixture cannot certify a project.
