# The Lean module system

Use this guidance when the selected Lean toolchain supports modules and the
project has adopted them, or when a target registry requires them. New files
in such a project should be modules; port an existing non-module dependency
tree bottom-up before modular consumers depend on it.

Two constraints matter in that setting:

- A registry submission policy may reject a submission if any regular `.lean`
  file in the repository is not a module. The verifier parses headers before it
  builds anything. Unused files, generated certificates, contained projects
  and local path dependencies all count; only `.git`, `.lake` and the
  `lakefile.lean` header are exempt.
- A module cannot import a non-module file. Lean reports
  ``cannot import non-`module` X from `module` ``. One unported file therefore
  blocks every module downstream of it, including dependencies in other
  repositories.

For supported versions, Mathlib's modular files provide useful examples.

## File shape

```lean
/-
Copyright (c) 2026 <author>. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: <author>
-/
module

public import Mathlib.Analysis.Calculus.FDeriv.Basic
import Mathlib.Tactic.Linarith

/-!
# Title

Module documentation.
-/

public section

namespace Project

-- declarations

end Project

end
```

- Ordinary comments, such as the copyright block, may precede `module`.
  Nothing else may.
- The module docstring comes after the imports.
- Open `public section`, or `@[expose] public section` (see below), right after
  the module docstring. Mathlib either closes it with a bare `end` at the end
  of the file or leaves it open; both are valid.

## Visibility

- **Declarations.** Under the module system a declaration is private to its
  module by default, unless it sits in a `public section` or is marked
  `public`. The file's API goes in the public section. `private` keeps its
  usual meaning. For registry Comparator Challenge or Solution files, avoid
  `private` when the current intake tooling matches names by dependency
  closure, because private names are mangled per module.
- **Theorem proofs are never exported.** The statement of a public theorem is
  exported; its proof is not.
- **Definition bodies are not exported by default.** Clients cannot unfold a
  public `def` definitionally unless it is `@[expose]`. This also applies to
  theorems in the **same file**, because an exported theorem may unfold only
  exposed definitions. It is verified for `rfl`; expect the same for `decide`
  and for definitional unfolding in client modules (`unfold` and `simp [f]` go
  through equation lemmas and may behave differently). Verified on Lean
  v4.35.0-rc2; recheck on the project's pinned toolchain:
  `theorem t : f = 3 :=
  rfl` for a non-exposed public `def f : ℕ := 3` fails with "Not a
  definitional equality … This theorem is exported from the current module.
  This requires that all definitions that need to be unfolded to prove this
  theorem must be exposed."
- **When to expose.** Expose a definition whose body is its meaning:
  - source-facing and frozen definitions, so a reader or auditor sees the
    object from the interface;
  - every definition in a Challenge file;
  - small definitions that are meant to reduce.

  For internal machinery, prefer stating and using unfolding lemmas (`f_def`,
  `f_apply`) over blanket exposure. A definition-heavy file may use
  `@[expose] public section`.
- **Imports.** Use `public import` when the public interface needs the import:
  statement types, exposed bodies, and instances appearing in statements. Use
  plain `import` when only proofs need it.
- **Code that runs at elaboration time.** Tactic or elaborator
  implementations and `#eval` of project code may need `meta` declarations or
  `meta import` (Mathlib uses `public meta import` in its tactic files).
  Follow the compiler's message and Lean's reference on modules and
  visibility.

## Dependencies

Port bottom-up. A project-owned path or Git dependency must be modular, and
pinned at a modular commit, before any consumer can be ported. At the start of
a campaign, check that every dependency is modular. A non-modular dependency
requires an explicit project decision: port it or pin a compatible version
before converting downstream files.

## Porting an existing repository

1. **Mechanical pass.** Insert `module` after the copyright comment. Rewrite
   each `import` as `public import`. Add `@[expose] public section` after the
   module docstring, with a closing `end`. Leave `private` declarations
   private.
2. **Rebuild and repair.** Expose definitions, or use unfolding lemmas, where
   `rfl` or definitional unfolding fails. Add `meta` where the compiler asks.
   Make a name public, or restructure, when a public statement mentions a
   private one.
3. **Tighten, if desired.** Demote proof-only imports to `import` and replace
   blanket exposure by targeted `@[expose]`. Measure before and after; see
   `lean-elaboration`.
4. **Verify.** Clean rebuild from a fresh checkout, the axiom audit, the
   Comparator configurations and the statement checks.
5. **Frozen statements.** Header and import edits change frozen bytes.
   Record each as a semantics-neutral hash move with its change-control note.
   The declaration, its ABI and its meaning must not change; rerun the
   frozen-statement checker. Port before freezing whenever the order is still
   open.

## Checker scripts

A project's own checkers (rule checks, duplicate-declaration checks, axiom
probes, frozen-statement guards, sync lints) parse Lean source lexically. The
module system breaks every non-module assumption in them, often silently.
Port them together with the Lean files, and port the published copies too:
a release often ships its own copies of the checkers.

- **Module header.** `module` must be the first token after `--` and
  `/- -/` comments. A `/--` doc comment or a `/-!` module doc is a command,
  not a comment, and may not come before it. A pattern such as `/-(?!-)`
  wrongly skips `/-!`.
- **Imports.** Accept `import`, `public import`, `meta import`,
  `public meta import` and `import all`. An "import-only aggregator"
  exemption must also accept the `module` line and
  `@[expose] public section` / bare `end`, or every aggregator file fails
  a "no public declaration" rule.
- **Declaration modifiers.** Declaration lexers and "next command" patterns
  must know `public` and `meta` (and `module` as a command).
- **Visibility.** In a module, a declaration is exported only if it is marked
  `public` or lies in a `public section` (nested sections inherit it), and is
  not `private`. A checker that asks "is this declaration public?" must track
  sections. Without `module`, every non-`private` declaration is public.
- **`_root_`.** `theorem _root_.X.y` inside `namespace N` declares `X.y`, not
  `N._root_.X.y`. Porting that moves code across namespaces creates these;
  an axiom probe that prints `N._root_.X.y` fails with "unknown constant".
- **Verify in a fresh checkout.** Run the full pipeline (build script, rule
  checks, axiom audit) in a fresh clone of the published tree. The published
  checkers fail there first, and the first public CI run would fail the same
  way.

[scripts/check_lean_modules.py](../scripts/check_lean_modules.py) enforces
the header rule and the intake checks below. For the other rules it provides
tested helpers to reuse in a project's checkers (`has_module_header`,
`code_mask`, `IMPORT`, `is_import_only`, `declarations`). The
[`check_frozen_anchors.py`](../../lean-orchestrator/scripts/check_frozen_anchors.py)
applies the same header,
visibility and `_root_` rules to frozen files.

## Registry-specific limits

Apply this section only when targeting a registry with these intake rules.
Confirm the current policy at submission time; registry limits can change.

- Every regular `.lean` file is a module. The `lakefile.lean` header is
  exempt.
- At most 10,000 physical lines per `.lean` file; comments and blank lines
  count. Split oversized files; never hide them in excluded paths.
- A Challenge file has at most 1,000 lines and 100 KiB, with a review warning
  above 300 lines or 32 KiB.
- `scripts/check_lean_modules.py` enforces the header, line-cap, symlink and
  Challenge-size rules and checks each `comparator.json`. Run it before every
  release or submission.
- One Comparator configuration is one submission and one registry entry.
- A violation needs a corrected submission revision.
