---
name: build-proof-dependency-graph
description: Build an independently reviewed, source-level dependency database anchored to exact author-frozen Lean declarations. Use after source-first approval of one-declaration anchor files, when an orchestrator must trace roots through LaTeX, Markdown, or other line-addressable proof sources, expose substantive proof steps and external inputs, and produce a structurally checked graph for later Lean orchestration. Do not use this skill to inspect implementation Lean code or decide whether any theorem is proved.
---

# Build a Proof Dependency Graph

Construct the mathematical topology from the supplied proof text, after the
author has approved a small set of exact one-declaration Lean anchor files.
Produce a database that a later Lean orchestrator can use immediately, while
making no claim that an anchor's proof has been completed.

## Keep the boundary sharp

- Read the source corpus and its cited mathematical inputs. Among Lean files,
  read only the designated frozen declaration files and frozen-anchor manifest
  needed to identify the author-approved anchors. Never read implementation
  modules, proof-status ledgers, or arbitrary Lean declarations.
- Do not interpret proof bodies, `sorry`, axioms, imports, or Lean status.
  A manifest may allowlist draft `sorry` bodies, but that is later
  orchestration policy, not evidence this skill can use.
- Initialize Lean planning fields only:
  `LEAN_STATUS: NOT_STARTED`, `LEAN_REF: -`, and `LEAN_NOTE: -` for ordinary
  nodes; use `ASSUMED` for explicit standing-assumption nodes and `EXTERNAL`
  for cited external results.
- Treat the bundled linter as a database and topology checker. It never
  interprets Lean proof status and cannot decide whether the extracted
  mathematics is correct or complete.
- Treat `FROZEN_ANCHORS` as immutable Lean ABI nodes. Each anchor has one
  manifest ID, declaration file, declaration export, source-record ID/version, and
  author-controlled elaborated ABI hash. With `--source-root`, the linter
  hashes the manifest file named in the graph header, parses its identity
  schema, and requires an exact unique match for every frozen graph node. It
  never reads Lean proof bodies or interprets manifest state, `sorry`, or proof
  metadata. A source-statement correction creates a new versioned anchor and
  invalidates old audits; neither graph edges nor amendments can change an
  anchor ABI.
- Record source-only statement fields for every node. For an anchor, they are a
  review aid alongside its frozen Lean statement, not permission to edit it.
- The schema names `CONTRACT_ID` and `CONTRACT_VERSION` identify a
  source-statement record only. That record is not a theorem statement,
  candidate declaration, approval surface, or substitute for the actual frozen
  Lean export.
- Stop after delivering the reviewed graph, coverage manifest, generated
  dashboard, and unresolved source questions. Do not begin formalization.

## Use the bundled resources

Before delegating, read [references/agent-packets.md](references/agent-packets.md)
for the extraction and review packet specifications.

Copy these assets into the target project and replace their placeholders:

- [assets/DEPGRAPH.template.md](assets/DEPGRAPH.template.md) as the graph
  database;
- [assets/DEPGRAPH_COVERAGE.template.md](assets/DEPGRAPH_COVERAGE.template.md)
  as the exhaustive source inventory.

Run `scripts/proof_depgraph.py --help` for linter options. Keep the script in
the skill or copy it into the target project if the graph will be maintained
there.

## Phase 0: author-freeze anchors before graph extraction

Work source-first. Select one or a few declaration-sized definitions/theorems
per subsection that carry its mathematical interface. Only their actual exact
Lean declarations may become anchors. Markdown descriptions, candidates,
tracked probes, placeholder types/bodies, fallback definitions, and promised
future characterizations have no anchor status. A transient untracked file may
elaborate the exact final command and must then be deleted.

The author approves the complete exact Lean command before dependency
extraction. Place each in its own declaration-only `.lean` file. Freeze each
approved keystone proposition or theorem with the exact body `by sorry` and
manifest state `DRAFT_SORRY`; do not wait for its proof before anchoring the
graph. The durable manifest must record and allowlist that exact body, provider,
declaration/ABI hash, and quarantine. The theorem statement is already final
but remains `FROZEN_UNPROVED`. Definitions neither contain nor depend on a
draft placeholder.

If the source defines an object by a characteristic property, prove and audit
its exact well-definedness theorem first. Only afterward materialize the
definition and its separately named, sorry-free full characterization; treat
them as one versioned semantic unit. Downstream graph nodes depend on the
characterization theorem, not merely on the definition's codomain. The
well-definedness theorem may itself be an exact frozen theorem root before the
definition exists.

The well-definedness theorem must not assume any existence, integrability,
linearity, quadraticity, symmetry, representability, or other proof step unless
the source states it as a premise. Model those results as dependencies. After a
genuine ∃! result is proved, unique choice is legitimate; a fallback or
non-unique selection is not.

Create the manifest before the graph using the frozen-anchor manifest schema.
For every anchor record its node ID, project-relative file, exact export,
source-record ID/version, elaborated ABI SHA-256, source locator, author/version,
and draft-body policy. The ABI hash is supplied and controlled by the authoring
process; this skill records it but does not compute or certify it from Lean.
With `--source-root`, the graph linter verifies the header's exact manifest
file SHA-256 and binds graph fields to the JSON entry; it never opens Lean
proof bodies.

Only then create the graph header: `FROZEN_ANCHORS` names these node IDs and
`FROZEN_MANIFEST` records its durable relative path and hash. Every graph root
must be an anchor. Non-anchor nodes must use `-` for all `FROZEN_*` fields.
No anchor may be a route, step, application, assumption, or external node.

When the author splits one source theorem or lemma into multiple anchors,
record the split ruling and its constant/witness policy in every affected
source-statement record: shared means shared across exports; independent means each export may
choose its own witness. A shared witness requires a joint frozen anchor; graph
edges between separate existential exports do not make their witnesses equal.
Do not derive either policy from graph topology.

## Phase 1: freeze the extraction specification

Record before reading proofs:

1. the already author-approved root anchor or anchors;
2. every in-scope source file and a revision, hash, or dated snapshot;
3. the exact IDs and scopes of standing assumptions, recorded in
   `STANDING_ASSUMPTIONS`, and the policy for cited external results;
4. stable notation, carrier, normalization, quantifier, and convention choices
   that a global reviewer must track;
5. the threshold for a substantive proof-step node;
6. exclusions, such as background exposition outside the root closure;
7. the central writer's stable agent/session identity.

Prefer source labels as node IDs. For unlabeled Markdown results, derive IDs
from stable heading anchors and semantic slugs. Use `parent#slug` for an
unlabeled proof step. Never make a line number part of an ID; retain line
numbers only as revisable locators.

Check every designated root anchor against its source statement before
extracting its proof. Record all source-visible premises and the outer-to-inner
quantifier order, especially dependency restrictions such as `C` depending
only on `d`. The graph's source fields may not mention an intermediate estimate
merely because the proof uses it, and they may never change the anchor file.

## Phase 2: inventory before interpreting

Build the coverage manifest mechanically and then inspect it manually. Include:

- theorem-like environments and named claims;
- definitions used by proofs;
- labeled or reused displayed formulas;
- Markdown theorem/proof headings;
- explicit citations and cross-references;
- proof paragraphs likely to contain unnamed substantive steps.

Give every inventory item exactly one disposition: one or more graph nodes, or
`EXCLUDED` with a concrete reason. An inventory is a checklist, not proof that
coverage is complete; fresh reviewers must compare it with the raw corpus.

## Phase 3: extract in parallel

Partition ownership into non-overlapping, line-addressable slices aligned to
complete statement/proof units whenever possible. Read-only context may
overlap across slice boundaries, but node ownership may not. Assign one
worker per slice and keep one distinct orchestrator as the single writer and
adjudicator. Choose models and reasoning effort appropriate to the mathematics
and the repository's resource policy; give every worker a bounded brief.

Require workers to return packets only. Each proposed node must include:

- exact statement and proof locators;
- a stable source-family `CONTRACT_ID` and its `CONTRACT_VERSION`, which
  together form the versioned source identity;
- normalized `SOURCE_HYPOTHESES`, `SOURCE_QUANTIFIERS`, `SOURCE_CONCLUSION`,
  and `CONSTANT_SCOPE` fields read from the statement rather than its proof;
- a stable ID and kind;
- direct prerequisites with source evidence for every edge;
- explicit standing-assumption and external-input nodes;
- substantive child steps;
- alternative proof routes;
- ambiguities and cross-slice references.

Do not ask extraction workers to set Lean status or edit the database. Give
them the approved anchor IDs and source statement locators, but do not give
them implementation modules or proof-status material. Reuse a worker for
follow-ups within its slice, but use fresh agents for independent review.

## Phase 4: model the proof faithfully

Use only direct dependency edges. Do not add a prerequisite merely because it
appears earlier in the paper. An edge can still be direct even when another
path makes it transitively redundant: retain it when the target's own proof
explicitly invokes or logically consumes that prerequisite.

Create a step node when omitting the step would hide a plausible Lean lemma or
an independently failing obligation. Typical examples are a nontrivial
estimate, construction, case split, parameter or witness choice, theorem
application, quantifier closure, carrier change, or reused intermediate claim.
Do not create nodes for routine algebra or purely syntactic rewrites unless
they change hypotheses, constants, carriers, or quantifier strength.

If the source asserts or needs a substantive bridge without actually proving
it, keep that bridge as a `step` or `application` node and mark `NOTE` with a
clear `SOURCE_GAP:` explanation. Its `STATEMENT_SOURCE` may point to the target
statement and its `PROOF_SOURCE` to the prose where the bridge is invoked.
`TOPOLOGY_STATUS` judges whether this modeling is accurate, not whether the
source proves the mathematics, so an independently confirmed gap can be
`REVIEWED`. Do not silently fill an omitted bridge merely because a reviewer
can reconstruct a proof; apply the substantive-step threshold to what the
source actually supplies. Never invent a proof-status-like topology value.

Interpret `DEPS` conjunctively. If the source offers alternative derivations,
create one `KIND: route` node for each derivation and list them in `ROUTES` on
the target. One available route will later suffice. Never put alternatives in
one comma-separated `DEPS` list. `ROUTE_FOR` is exclusively the ownership field
for these route nodes; do not use it as a parent pointer for ordinary proof
steps or displays.

Represent standing assumptions and external results as explicit leaf nodes.
Do not hide them in notes or magic dependency tokens. Only IDs frozen in the
header may use `KIND: assumption`; the linter rejects undeclared assumption
nodes.

Do not turn every bound variable or theorem-local premise into a node. Keep a
premise inside its statement unless it is a genuine standing assumption or a
substantive obligation established elsewhere. A named local hypothesis package
may map to the enclosing theorem node in the coverage manifest; naming alone
does not make it a globally `ASSUMED` leaf. A conditional lemma may therefore
be a node without separate nodes for all of its premises. At each later
application, create direct dependencies for the source steps that discharge
those premises, splitting out a substantive application node when necessary.

Keep source-statement fields and proof topology separate. `DEPS` names results the
source proof consumes; it never enlarges `SOURCE_HYPOTHESES`. If result `B` is
used to prove `A`, represent `B` as a dependency of `A`, not as an allowed
hypothesis of `A`. A genuinely conditional source lemma records its displayed
premises in `SOURCE_HYPOTHESES`; a helper with additional premises is not the
same source node. Never use an edge to launder proof content into a statement.

## Phase 5: merge through one writer

Have the orchestrator merge packets, normalize IDs, record its identity in
`WRITER`, and resolve only local, well-supported conflicts. Preserve
uncertainty as `TOPOLOGY_STATUS: DISPUTED` rather than guessing.

For every dependency or route edge, add one `EDGE:` record naming the target,
the target proof's locator where the prerequisite is consumed, and a short
direct-use rationale. Do not cite only the prerequisite's own proof site.

Run the linter after each merge wave. Resolve duplicate IDs, dangling edges,
route-ownership errors, cycles, uncovered inventory items, and source-path
errors before beginning review.

## Phase 6: run independent topology audits

Give fresh reviewers the raw source slice, coverage entries, and merged node
blocks, but not the extractor's private rationale. Ask them to try to refute
the graph by finding:

- omitted statements, displays, definitions, or implicit bridge steps;
- dependencies that are missing, reversed, merely transitive, or unnecessary;
- hidden assumptions or external inputs;
- alternatives incorrectly modeled as conjunctions;
- definition/projection cycles;
- source ranges or statement boundaries that do not match the text;
- source-statement records that omit, add, reorder, or rescope hypotheses,
  quantifiers, conclusions, or constants;
- conditional theorem premises that a downstream application never supplies;
- `EDGE` locators that cite the prerequisite instead of its use by the target;
- cross-slice edges that neither local extractor owned.

Require a distinct reviewer for every accepted node. Set
`TOPOLOGY_STATUS: REVIEWED` only after that review; otherwise retain
`PROPOSED` or `DISPUTED`.

Delegate at least one fresh adversarial pass over the complete root closure to
an agent distinct from the writer and the relevant extractors. Use one or two
fresh reviewers with sufficient mathematical capability and
have the distinct orchestrator adjudicate their findings. Check root identity,
statement strength, carriers, normalizations,
  quantifier order, constant scope, exact source-statement fields,
conditional-premise discharge at consumers, edge use sites,
global conventions, cross-section edges, and the AND/OR route structure.
Record the independent reviewer and durable report in `GLOBAL_REVIEWER` and
`GLOBAL_REVIEW_REF`; the linter rejects a global reviewer who is the writer or
already served as a node extractor. The orchestrator must enforce the stronger
procedural rule that this agent did not perform an earlier slice review.

## Phase 7: validate and publish

Run, at minimum:

```bash
python3 scripts/proof_depgraph.py \
  --db DEPGRAPH.md \
  --manifest DEPGRAPH_COVERAGE.md \
  --source-root . \
  --require-reviewed \
  --require-complete-coverage \
  --require-initial-lean-status \
  --require-all-reachable \
  --write-dashboard

python3 scripts/proof_depgraph.py \
  --db DEPGRAPH.md \
  --manifest DEPGRAPH_COVERAGE.md \
  --source-root . \
  --require-reviewed \
  --require-complete-coverage \
  --require-initial-lean-status \
  --require-all-reachable \
  --check
```

Do not call the graph ready until:

- every root exists and its full dependency closure is represented;
- every graph node feeds at least one declared root;
- every coverage item is mapped or explicitly excluded;
- every in-closure node is independently reviewed;
- every node has reviewed, complete source-statement fields;
- every edge has source evidence;
- the global reviewer is independent of the central writer;
- no topology dispute, dangling reference, ownership error, or cycle remains;
- the generated dashboard is current;
- all ordinary Lean fields remain initialized rather than inferred.

Report the node and edge counts, roots and root-closure size, dependency leaves,
external and assumption boundaries, alternative-route count, topology-review
queue, explicit `SOURCE_GAP` nodes, excluded inventory items, and any unresolved
questions. Do not compute or report a Lean proof frontier in this skill.

Hand the published graph and frozen-anchor manifest to the later Lean
orchestrator only after this gate passes. That workflow develops implementation
lemmas beneath the anchors and must compile an exact-type probe before
marking an anchor certified; this source-only skill neither creates nor
evaluates that probe. The required order is always **author-frozen anchors →
anchored source graph → Lean orchestration**, never the reverse.

## Maintain structural history

During initial one-writer drafting, edit proposed records normally. After the
graph is published, correct structural facts with append-only `AMEND` records
and an independent reviewer. Never silently rewrite historical dependency or
source claims in a shared campaign.
Corrections to source-statement fields on ordinary graph nodes are structural changes:
use reviewed `SET_CONTRACT_ID`, `SET_CONTRACT_VERSION`,
`SET_SOURCE_HYPOTHESES`, `SET_SOURCE_QUANTIFIERS`, `SET_SOURCE_CONCLUSION`, or
`SET_CONSTANT_SCOPE` amendments. A frozen anchor is different: never amend its
statement/proof source locators or source identity. Create a new versioned declaration file and manifest entry, update
the author-approved anchor list, and invalidate every audit tied to the old
ABI. `DEPS` may be amended as proof topology evolves, but it never alters an
anchor ABI.
