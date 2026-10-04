# Proof-source coverage manifest — <project>

CORPUS: <same paths and revision as DEPGRAPH.md>

Every theorem-like source unit, definition, reused display, citation, and
candidate substantive proof paragraph receives exactly one disposition.

## Record schema

```text
ITEM: <stable inventory ID>
KIND: theorem|proposition|lemma|corollary|claim|definition|display|assumption|external|heading|citation|proof-region
SOURCE: <path#stable-anchor@Lx-Ly | external:bib-key#result>
DISPOSITION: NODE <comma-separated node IDs> | EXCLUDED
REASON: <why split into these nodes or why excluded>
COVERAGE_STATUS: PROPOSED|REVIEWED|DISPUTED
EXTRACTOR: <agent/session tag>
REVIEWER: <different agent/session tag | ->
```

## Inventory

ITEM: <inventory-id>
KIND: theorem
SOURCE: <source locator>
DISPOSITION: NODE <node-id>
REASON: represented by the corresponding statement and proof-step closure
COVERAGE_STATUS: PROPOSED
EXTRACTOR: <agent tag>
REVIEWER: -
