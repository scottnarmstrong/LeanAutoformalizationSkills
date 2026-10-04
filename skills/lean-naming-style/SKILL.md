---
name: lean-naming-style
description: Use when naming Lean declarations, organizing files, adding docstrings, or cleaning code so it matches Mathlib conventions and review expectations.
---

# Lean Naming Style

Use this skill when creating or renaming declarations, organizing modules, or cleaning Lean code for review. The goal is not just “pretty code”; it is a library-shaped API that feels native to Mathlib.

## Naming Rules

- Use `snake_case` for theorem names and terms of type `Prop`.
- Use `UpperCamelCase` for structures, classes, inductive types, and other declarations returning `Type` or `Sort`.
- Use `lowerCamelCase` for ordinary terms returning data.
- Prefer descriptive theorem names whose conclusion drives the name.
  - add hypotheses with `_of_...`
  - use systematic fragments like `nonneg`, `inj`, `ext`, `iff`
- Put the declaration in the most specific namespace that supports natural dot notation.

## File and API Rules

- Use `UpperCamelCase.lean` file names.
- In projects using the module system, follow this header order:
  - copyright comment;
  - `module`;
  - imports: `public import` only for what statements need, plain `import`
    otherwise;
  - `/-! module docstring -/`;
  - `public section`.

  See the `lean-project-architecture` skill's `references/module-system.md`.
- Keep one focused topic per file and follow the repository's file-size limit.
- Import as little as possible.
- After adding a public definition, add the obvious API immediately.
  - constructor or evaluation lemmas
  - `@[simp]` lemmas only when they genuinely improve simplification
  - extensionality lemmas where equality is structural
- Add module docstrings and public-definition docstrings where they help later readers.

## Style Rules

- Prefer readable proofs over clever ones.
- Keep checked-in proofs explicit and lint-clean.
- Do not commit unmanifested `sorry`, `exact?`, `apply?`, or exploratory
  `simp`. The sole `sorry` exception is the exact `by sorry` body of an
  author-approved, manifest-bound frozen keystone theorem in state
  `DRAFT_SORRY`; it is statement ABI, not finished code.
- In projects with a zero-warning policy, do not commit while linter warnings remain.

## Review Checklist

- Does the name match Mathlib conventions?
- Is the namespace the right one?
- Is the file the canonical home?
- Are imports minimal?
- Are there missing `simp`, `ext`, or accessor lemmas?
- Is the code docstring- and linter-clean?

## References

- Read [references/naming-and-style.md](references/naming-and-style.md) for naming patterns, symbol-to-name translations, structural lemma conventions, file organization, and lint/style expectations.
