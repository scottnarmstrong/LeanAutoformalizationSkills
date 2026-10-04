---
name: lean-workflow
description: Route Lean 4 work through a repository's Mathlib/Lake conventions. Use when editing Lean files, checking source fidelity or axioms, searching dependencies, validating focused targets, or protecting dependency build artifacts.
---

# Lean workflow

Use this as the general router for a Lean 4 repository built with Lake and Mathlib. Read the repository's own instructions first; they override generic commands and thresholds here. Select a more focused sibling skill when it applies:

- `lean-project-architecture` for public declarations, abstractions, module boundaries, or imports;
- `lean-search-discovery` before attempting a new proof;
- `lean-proof-patterns` while translating or repairing a proof;
- `lean-naming-style` for declarations, files, namespaces, and docstrings;
- `lean-elaboration` for measured performance diagnosis or repair;
- `lean-elaboration-test` for a repository-wide performance snapshot;
- `lean-statement-audit` for exact source-to-declaration correspondence;
- `lean-orchestrator` for an explicitly authorized multi-agent formalization effort.

Use `build-proof-dependency-graph` for a source-level proof dependency database. It records source topology; it does not determine Lean proof status.

## Build and dependency hygiene

- Treat pinned dependencies and their compiled artifacts as read-only during routine project work.
- Never delete dependency `.olean`, `.ilean`, trace, hash, IR, or object files as an invalidation shortcut.
- Follow repository-provided build wrappers and cache guards. Otherwise validate the narrowest project target that covers the edit, for example `lake build Project.Foo.Bar`.
- Do not run `lake clean`, update the toolchain or dependency pins, or trigger a full dependency rebuild without explicit authorization.
- Before a destructive project-artifact invalidation, resolve the exact project-owned path and confirm that no dependency tree can match it.
- Distinguish project compilation from dependency compilation in build and performance reports.

## Workflow

1. Read `AGENTS.md` or `CLAUDE.md`, the Lake configuration, toolchain file, target module, and nearby imports.
2. Identify the authoritative mathematical source when a declaration represents an external claim. Preserve its binders, carriers, quantifiers, hypotheses, constants, and endpoint conditions.
3. Search Mathlib and the project before adding a declaration or inventing a proof route.
4. Do not move proof obligations into hypotheses, introduce custom axioms, or disguise unfinished proofs. Keep any explicitly authorized draft theorem quarantined and visibly marked under the repository's draft policy.
5. Make the smallest coherent edit and validate it with the repository's guarded command or the narrowest appropriate Lake/Lean command.
6. Audit affected public declarations for `sorry`, custom axioms, hidden stronger hypotheses, quantifier drift, and constant-dependence drift. Run `#print axioms` from an untracked probe or other repository-approved audit path, not from a compiled source file.
7. Report exact commands and targets, skipped validation, remaining placeholders, and source mismatches.

If work is delegated, obey the repository's agent policy and give each worker a bounded, disjoint task. Do not infer a model requirement, concurrency policy, or permission to spawn agents from this skill.
