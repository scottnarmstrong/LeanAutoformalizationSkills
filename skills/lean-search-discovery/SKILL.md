---
name: lean-search-discovery
description: Use when searching Mathlib for existing declarations, likely theorem names, relevant files, or proof ingredients before attempting a new Lean proof.
---

# Lean Search Discovery

Use this skill when the next bottleneck is not proving a statement from scratch, but finding the right declaration, namespace, import, or existing theorem. The default posture is: search before you prove.

## Search Workflow

1. Decide what you are searching for.
   - a theorem name
   - a namespace or file
   - a rewrite lemma
   - a theorem with a recognizable type signature
2. Predict likely names from Mathlib conventions.
   - use conclusion-driven names such as `foo_of_bar`
   - translate symbols into name fragments like `mem`, `inter`, `union`, `nonneg`, `inj`
3. Search locally first.
   - inside Lean: `exact?`, `apply?`, `rw?`, `simp?`, `#check`, `#print`
   - in the terminal: `rg`, `find`, `ls`, targeted file inspection
4. Verify every hit before using it.
   - confirm the statement shape
   - confirm the namespace and import path
   - confirm the lemma is at the right level of generality
5. Only after two or more search strategies fail should you assume the theorem is missing and start proving it yourself.

## Local Search Rules

- Prefer `rg` in `.lake/packages/mathlib/Mathlib` for terminal search.
- Search both likely names and nearby concepts.
- Limit output aggressively so inspection stays local and readable.
- After a hit, read the surrounding file rather than trusting the name alone.

## In-Proof Search Rules

- `exact?` is for “this goal should be one lemma.”
- `apply?` is for “this looks like the head of a useful theorem.”
- `rw?` is for normal-form mismatches.
- `simp?` is for turning exploratory simplification into explicit `simp only [...]`.
- None of these should remain in finished code.

## Online Search

If online access is available, use Loogle or LeanSearch when local name search is not enough. Treat them as discovery tools, not proof authorities: always verify the result locally with `#check`, `#print`, or direct file inspection.

## References

- Read [references/search-and-discovery.md](references/search-and-discovery.md) for the full search workflow, theorem-name heuristics, and search-service guidance.
- Read [references/tools.md](references/tools.md) when choosing between search tactics, terminal search, API docs, and broader workflow tools.
