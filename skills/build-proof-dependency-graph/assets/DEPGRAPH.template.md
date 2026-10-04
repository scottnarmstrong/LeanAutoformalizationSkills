# Proof dependency database — <project or root>

GRAPH_VERSION: 4
ROOTS: <comma-separated root node IDs>
CORPUS: <source paths and immutable revision/hash/date>
CONVENTIONS: <notation, carrier, normalization, and quantifier watch items>
STANDING_ASSUMPTIONS: <comma-separated assumption node IDs | ->
EXTERNAL_POLICY: <how cited results are represented>
FROZEN_ANCHORS: <comma-separated NODE IDs whose exact Lean statements are author-frozen>
FROZEN_MANIFEST: <project-relative frozen-anchor manifest path | sha256:<64 lowercase hex>>
WRITER: <central orchestrator/session tag>
GLOBAL_REVIEWER: <high-judgment reviewer tag | ->
GLOBAL_REVIEW_REF: <durable report or session reference | ->

The dependency direction is `NODE -> prerequisite`. `DEPS` is conjunctive.
`ROUTES` lists alternative `KIND: route` nodes; one route is sufficient.
Lean fields are initialized planning metadata and are not evaluated here.
This source-extraction skill writes only `NOT_STARTED`, `EXTERNAL`, or
`ASSUMED`. A later Lean workflow owns every subsequent status and its meaning.
`CONTRACT_ID` and `CONTRACT_VERSION` together form the versioned contract
identity and are extracted only from the source statement.
`DEPS` may never add a premise to them: proof ingredients belong in the graph,
not in the theorem's hypothesis list.

`FROZEN_ANCHORS` is the graph's ABI boundary. Each named node corresponds to
one author-approved Lean declaration file and exact declaration name. With
`--source-root`, the linter hashes the JSON manifest file named in the header,
then binds every frozen node to its unique manifest entry by anchor ID, path,
export, contract ID/version, and elaborated ABI hash. It deliberately neither
reads Lean bodies nor interprets a manifest entry's proof/status fields. A
changed contract requires a new versioned declaration, anchor, and manifest
hash; prior audit evidence does not transfer. The graph may add or correct
`DEPS`, but can never alter an anchor's declaration, statement, or ABI.

## Node schema

```text
NODE: <stable source label or semantic ID>
KIND: theorem|proposition|lemma|corollary|claim|definition|display|step|application|route|external|assumption
TITLE: <short semantic title>
STATEMENT_SOURCE: <path#stable-anchor@Lx-Ly | external:bib-key#result | ->
PROOF_SOURCE: <path#stable-anchor@Lx-Ly | external:bib-key#proof | ->
CONTRACT_ID: <stable contract-family ID, e.g. S4.l.main>
CONTRACT_VERSION: <contract version within that family, e.g. 1>
SOURCE_HYPOTHESES: <semicolon-separated normalized source premises | none>
SOURCE_QUANTIFIERS: <outer-to-inner ordered binders and scopes | none>
SOURCE_CONCLUSION: <normalized source conclusion; never a proof obligation>
CONSTANT_SCOPE: <dependency scope, e.g. C depends only on d and precedes model data | none>
FROZEN_FILE: <project-relative one-declaration .lean file for a FROZEN_ANCHORS ID | ->
FROZEN_DECL: <exact Lean declaration name for a FROZEN_ANCHORS ID | ->
FROZEN_ANCHOR_ID: <manifest anchor ID for a FROZEN_ANCHORS ID; may differ from stable NODE ID | ->
FROZEN_ABI_SHA256: <64 lowercase hexadecimal manifest abi_sha256 for a FROZEN_ANCHORS ID | ->
DEPS: <comma-separated direct prerequisite IDs | ->
ROUTES: <comma-separated alternative route-node IDs | ->
ROUTE_FOR: <owner node ID for a route node | ->
EDGE: <dependency-or-route ID> | <source locator> | <direct-use rationale>
TOPOLOGY_STATUS: PROPOSED|REVIEWED|DISPUTED
EXTRACTOR: <agent/session tag>
REVIEWER: <different agent/session tag | ->
LEAN_STATUS: <later-workflow status; initially NOT_STARTED|EXTERNAL|ASSUMED>
LEAN_REF: <Lean declaration/file reference | ->
LEAN_NOTE: <later Lean-orchestration note | ->
NOTE: <source-topology decision; use SOURCE_GAP: for an unproved bridge | ->
```

For a dependency-free node, omit `EDGE:` lines. For every ID in `DEPS` or
`ROUTES`, include exactly one matching `EDGE:` line.

Every `ROOTS` ID must also appear in `FROZEN_ANCHORS`. Frozen anchors may have
only `KIND: theorem|proposition|lemma|corollary|claim|definition|display`;
they may not be route, step, application, assumption, or external nodes. Each
frozen file and declaration is unique. Ordinary nodes use `-` in all four
`FROZEN_*` fields.

## Nodes

NODE: <root-id>
KIND: theorem
TITLE: <root title>
STATEMENT_SOURCE: <source locator>
PROOF_SOURCE: <source locator>
CONTRACT_ID: <root-contract-id>
CONTRACT_VERSION: 1
SOURCE_HYPOTHESES: <exact normalized hypotheses stated by the source | none>
SOURCE_QUANTIFIERS: <outer-to-inner quantifier order | none>
SOURCE_CONCLUSION: <exact normalized conclusion>
CONSTANT_SCOPE: <all constant-dependence restrictions | none>
FROZEN_FILE: Frozen/<root-id>.lean
FROZEN_DECL: <Namespace.rootDeclaration>
FROZEN_ANCHOR_ID: <versioned manifest anchor ID>
FROZEN_ABI_SHA256: <64 lowercase hexadecimal manifest ABI hash>
DEPS: <direct prerequisite IDs | ->
ROUTES: -
ROUTE_FOR: -
TOPOLOGY_STATUS: PROPOSED
EXTRACTOR: <agent tag>
REVIEWER: -
LEAN_STATUS: NOT_STARTED
LEAN_REF: -
LEAN_NOTE: -
NOTE: source extraction pending independent review

## Append-only structural amendments

```text
AMEND: <unique amendment ID>
TARGET: <existing node ID>
AUTHOR: <agent/session tag>
REVIEWER: <different agent/session tag>
ADD_DEPS: <IDs | ->
DROP_DEPS: <IDs | ->
ADD_ROUTES: <route IDs | ->
DROP_ROUTES: <route IDs | ->
SET_TITLE: <new title | ->
SET_STATEMENT_SOURCE: <new locator | ->
SET_PROOF_SOURCE: <new locator | ->
SET_CONTRACT_ID: <new contract-family ID | ->
SET_CONTRACT_VERSION: <new contract version | ->
SET_SOURCE_HYPOTHESES: <new normalized source premises | ->
SET_SOURCE_QUANTIFIERS: <new ordered binders/scopes | ->
SET_SOURCE_CONCLUSION: <new normalized conclusion | ->
SET_CONSTANT_SCOPE: <new dependency scope | ->
SET_ROUTE_FOR: <new owner | ->
EDGE: <new dependency-or-route ID> | <source locator> | <rationale>
NOTE: <reason for the reviewed correction>
```

An amendment may correct proof topology around a frozen anchor, but may not
use `SET_STATEMENT_SOURCE`, `SET_PROOF_SOURCE`, `SET_CONTRACT_ID`,
`SET_CONTRACT_VERSION`, or a `SET_SOURCE_*` field on it. Frozen source
locators and statement-contract fields require a new frozen declaration and
graph version; no amendment field exists for changing
`FROZEN_FILE`, `FROZEN_DECL`, `FROZEN_ANCHOR_ID`, or `FROZEN_ABI_SHA256`.

<!-- BEGIN PROOF DEPGRAPH GENERATED -->
Run `proof_depgraph.py --write-dashboard` to replace this body.
<!-- END PROOF DEPGRAPH GENERATED -->
