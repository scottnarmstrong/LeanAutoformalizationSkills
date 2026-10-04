# Agent packet specifications

Use these specifications to keep worker context bounded and returns mergeable. Give
workers raw source excerpts or exact line-addressable ranges. Do not give fresh
reviewers the extractor's hidden reasoning or expected verdict.

Before any packet, the author—not an extraction worker—selects and approves
the exact one-declaration frozen Lean anchors. The graph packet may name and
read only those designated declarations and their manifest identity fields. It
must never inspect implementation modules, imports, proof bodies, `sorry`,
axioms, or proof-status material. The graph uses the manifest's anchor ID,
path, export, contract ID/version, and ABI hash as immutable identity metadata;
it is not proof evidence.

The legacy schema words `CONTRACT_ID` and `CONTRACT_VERSION` name
source-statement metadata only. They are not Lean declarations, candidate
statements, or approval artifacts. Every root is the actual exact frozen Lean
export. A source-characterized definition is eligible only after its
well-definedness theorem is proved and its sorry-free full characterization is
frozen; graph consumers depend on that characterization theorem.

## Contents

1. Extraction packet
2. Slice topology review
3. Global root-closure review
4. Orchestrator merge checklist

## 1. Extraction packet

Assign one non-overlapping source slice. Include the frozen-anchor manifest
(IDs, file paths, declaration exports, contract IDs/versions, and ABI hashes
only), nearby
statement inventory, convention watch list, and any already-canonical
cross-slice node IDs. Do not supply implementation Lean files.

Use a prompt of this form:

```text
Read only <source files/ranges> and, if necessary, the designated frozen-anchor
manifest/declaration headers. Build proposed source-level dependency records
for every in-scope mathematical statement and substantive proof step. Do not
inspect implementation Lean, proof bodies, `sorry`, axioms, Lean status, or
edit the central database.

For each node return:
- a block using exactly the database field names and allowed `KIND` values;
- stable `NODE` ID and `KIND`;
- TITLE;
- exact STATEMENT_SOURCE and PROOF_SOURCE;
- a stable source-family CONTRACT_ID and source-only CONTRACT_VERSION, which
  together form the versioned source identity, plus
  SOURCE_HYPOTHESES, SOURCE_QUANTIFIERS, SOURCE_CONCLUSION, and CONSTANT_SCOPE;
- `FROZEN_FILE`, `FROZEN_DECL`, `FROZEN_ANCHOR_ID`, and `FROZEN_ABI_SHA256`
  copied exactly from the manifest only if the node ID is in `FROZEN_ANCHORS`;
  the versioned manifest anchor ID may differ from the stable source NODE ID;
  otherwise use `-`;
- direct DEPS only, in the direction `NODE -> prerequisite` (never point a
  prerequisite at its consumer);
- alternative ROUTES, each as a separate route node;
- one EDGE record per dependency/route, citing where the target proof uses it
  rather than where the prerequisite itself was proved;
- explicit assumption and external nodes, with `KIND: assumption` restricted
  to IDs in the frozen `STANDING_ASSUMPTIONS` header;
- EXTRACTOR tag, TOPOLOGY_STATUS: PROPOSED;
- initialized Lean fields only;
- ambiguity/cross-slice notes.

Also return coverage-manifest dispositions for every assigned inventory item,
with `COVERAGE_STATUS: PROPOSED`, the extractor tag, and no reviewer yet.
Create a step node when omission would hide a plausible independent Lean lemma,
nontrivial estimate/application, construction, case split, witness/parameter
choice, quantifier closure, carrier change, or reused intermediate claim.
`ROUTE_FOR` is reserved exclusively for `KIND: route`; it is not a generic
parent pointer for steps or displays. Do not atomize bound variables or
theorem-local premises. A named local premise belongs to the enclosing
conditional statement unless the source separately establishes it; model its
later discharge at the consumer, and never initialize it as globally assumed.
Do not copy a premise from the proof into SOURCE_HYPOTHESES. A proof dependency
belongs in DEPS; only a premise stated by the source belongs in the
source-statement fields.
Return node blocks and a short uncertainty list; make no file changes.
```

Require the worker report to state:

- source ranges actually read;
- node and edge counts;
- coverage items mapped/excluded;
- unresolved IDs or cross-slice edges;
- alternate routes found;
- confirmation that no Lean evidence was sought and no files were changed.
- confirmation that no anchor ABI was edited or inferred from a proof body.

## 2. Slice topology review

Use a different agent from the extractor. Supply raw source, the frozen-anchor
manifest and declaration headers, coverage entries, and merged node blocks. Do
not supply implementation Lean or the extractor's private rationale beyond the
records themselves.

Use a prompt of this form:

```text
Adversarially review this proposed proof-topology slice against the raw source.
Try to refute completeness and edge correctness. You may identify the
designated frozen anchor declarations against their manifest, but do not inspect
implementation Lean, proof bodies, `sorry`, axioms, Lean status, or edit files.

Check every inventory disposition, node boundary, substantive proof step,
direct edge and EDGE locator, assumption, external input, route alternative,
and cross-slice reference. Look for missing bridge steps, wrong edge direction,
transitive shortcuts, accidental AND where the proof says OR, and circularity
between definitions and consequences.

Reconstruct each node's source-statement fields independently from the raw
statement. Fail any record that adds a proof ingredient as a hypothesis, drops a source
premise, changes quantifier order, weakens the conclusion, or permits a
constant to depend on data outside its source scope.

Topology status is not proof status. If the source omits a needed mathematical
bridge, require an ordinary step/application node with `SOURCE_GAP:` in its
NOTE; that node may pass topology review once it faithfully exposes the gap.
Use only the schema's topology values. Do not supply an omitted substantive
argument from your own mathematical knowledge merely to make the source close.

Return PASS or FAIL per node and per coverage item. For every failure, give a
replacement node/edge/manifest fragment. A PASS must name the source spans
re-read. Do not approve your own extraction work.
```

Only the orchestrator changes a node to `TOPOLOGY_STATUS: REVIEWED` or an item
to `COVERAGE_STATUS: REVIEWED` and records the reviewer identity.

## 3. Global root-closure review

Reserve one fresh agent with sufficient mathematical capability after local
reviews, using the repository's model and resource policy. Give it the full
source corpus, conventions, manifest, and effective graph.

Use a prompt of this form:

```text
Trace every designated frozen root backward through the complete proposed graph
and compare the closure with the source. Try to find a global modeling error.

Audit root identity, statement strength, quantifier order, carriers,
normalizations, convention changes, induction hypotheses, cross-section edges,
external-input boundaries, AND/OR routes, and nodes outside the root closure.
Reconstruct every root's source-statement fields directly from the source and
compare all four fields before reviewing topology.
At every application of a conditional result, check where each premise is
supplied. Check that EDGE evidence points to the consumer's use site. Check
that every proof paragraph contributing a substantive obligation appears in
the graph or has an explicit exclusion, and that plausible but unstated
arguments remain SOURCE_GAP nodes.

Return a root-by-root verdict, proposed correction fragments, unreachable-node
findings, and the final unresolved-question list. Verify every root is an
author-frozen anchor and every non-anchor has `FROZEN_*: -`. Do not inspect
implementation Lean, proof bodies, `sorry`, axioms, Lean status, or edit files.
```

The global reviewer must be fresh and distinct from the central writer. Do not
publish the graph while this review reports a source-topology failure.

## 4. Orchestrator merge checklist

Keep one writer. Before each merge wave:

1. Re-read the frozen-anchor manifest, declaration identities, frozen source
   locators, source-statement fields, and convention watch list; reject any
   mismatch rather than repairing a frozen anchor in the graph. A correction
   requires a new versioned declaration and manifest entry.
2. Record the central writer identity and verify slice ownership.
3. Normalize IDs without erasing source labels.
4. Reject records without exact source locators, complete source-statement fields,
   or direct-edge evidence.
5. Convert alternatives into owned route nodes.
6. Preserve disputes explicitly; do not guess to make lint pass.
7. Run structural lint and inspect root closure after merging.
8. Apply fresh-review findings, record reviewer identities, and rerun lint.
9. Compare the final node/edge counts with worker reports and the manifest.
10. Publish only after the completion gate in SKILL.md passes. Never add a
    graph root before its frozen declaration and manifest entry exist.

For a large corpus, rotate workers by slice rather than giving every agent the
whole paper. Use shared durable packets or concise returns so the orchestrator
spends context on conflicts, cross-slice topology, and final adjudication.
