# Mathlib Naming Conventions and Code Style

> **Sources:** Mathlib naming conventions (leanprover-community.github.io/contribute/naming.html);
> Lean 4 naming conventions (lean4/doc/std/naming.md); Library style guidelines
> (leanprover-community.github.io/contribute/style.html); Mathlib style linters documentation.
> See [Sources and References](../../../SOURCES.md) for full citations.

## Table of Contents

1. [Capitalization Rules](#capitalization-rules)
2. [Theorem Naming Patterns](#theorem-naming-patterns)
3. [Symbol-to-Name Dictionary](#symbol-to-name-dictionary)
4. [Variable Conventions](#variable-conventions)
5. [Prop-Valued Classes and Is-Prefix](#prop-valued-classes)
6. [Structural Lemma Patterns](#structural-lemma-patterns)
7. [Code Formatting](#code-formatting)
8. [File Organization](#file-organization)
9. [Documentation](#documentation)
10. [Linting](#linting)

---

## Capitalization Rules

Lean 4 Mathlib uses a mixed-case convention (unlike Lean 3 which was all `snake_case`):

| Kind of declaration | Case | Examples |
|----|------|---------|
| Terms of `Prop` (proofs, theorem names) | `snake_case` | `add_comm`, `mul_assoc` |
| `Prop`s, `Type`s, `Sort`s (structures, classes, inductive types) | `UpperCamelCase` | `CommRing`, `IsCompact`, `Continuous` |
| Functions (named by return type) | Same as return type | A function returning `Prop` → `snake_case`; returning `Type` → `UpperCamelCase` |
| Other terms of `Type` | `lowerCamelCase` | `toFun`, `instRing` |
| Acronyms (≤ 3 letters) | All same case | `LE` (type), `le` (theorem); `IO` (type) |
| `UpperCamelCase` names inside `snake_case` names | `lowerCamelCase` | `isCompact_preimage` (not `IsCompact_preimage`) |

### File names
Files use `UpperCamelCase.lean`. Rare exceptions (e.g., `lp.lean` for ℓ_p) must be
discussed on Zulip.

---

## Theorem Naming Patterns

### Descriptive names (most common)

The name describes the conclusion. Hypotheses are added with `_of_`:

```
succ_ne_zero         -- succ n ≠ 0
mul_zero             -- a * 0 = 0
sub_add_eq_add_sub   -- a - b + c = a + (c - b)
le_iff_lt_or_eq      -- a ≤ b ↔ a < b ∨ a = b
```

Hypotheses are listed in order (not reversed):
```
lt_of_succ_le           -- succ m ≤ n → m < n   (A_of_B)
lt_of_le_of_ne          -- a ≤ b → a ≠ b → a < b  (A_of_B_of_C)
add_lt_add_of_lt_of_le  -- a < b → c ≤ d → a + c < b + d
```

### Axiomatic names

Some names describe the property rather than the statement:
```
add_comm          -- commutativity of addition
mul_assoc         -- associativity of multiplication
neg_neg           -- double negation
pred_succ         -- predecessor of successor
```

### Namespace / dot notation

Use the most specific namespace in the hypotheses to enable dot notation:
```
-- Good: enables hs.image syntax
IsCompact.image : IsCompact s → Continuous f → IsCompact (f '' s)

-- The namespace is IsCompact because the first hypothesis is IsCompact s
```

### Infix operations

Name follows the written order of the expression:
```
neg_mul_neg     -- (-a) * (-b) = a * b  (not mul_neg_neg)
```

### Left / right

"Left" and "right" refer to which argument varies:
```
add_le_add_left   -- c + a ≤ c + b (left argument c is fixed)
add_le_add_right  -- a + c ≤ b + c (right argument c is fixed)
mul_left_monotone -- Monotone (· * a) (left slot varies, right is a)
```

For `cancel`/`inj`: the side that "changes" is named:
```
sub_right_inj     -- a - b = a - c ↔ b = c  (right argument changes)
```

### Abbreviations

| Short form | Means | Instead of |
|-----------|-------|-----------|
| `pos` | `0 < x` | `zero_lt` |
| `neg` | `x < 0` | `lt_zero` |
| `nonneg` | `0 ≤ x` | `zero_le` |
| `nonpos` | `x ≤ 0` | `le_zero` |

---

## Symbol-to-Name Dictionary

### Logic
`∨` → `or`, `∧` → `and`, `→` → `of`/`imp`, `↔` → `iff`, `¬` → `not`,
`∃` → `exists`, `∀` → `forall`, `=` → `eq` (often omitted), `≠` → `ne`

### Sets
`∈` → `mem`, `∪` → `union`, `∩` → `inter`, `⋃` → `iUnion`/`biUnion`,
`⋂` → `iInter`/`biInter`, `⋃₀` → `sUnion`, `⋂₀` → `sInter`,
`\` → `sdiff`, `ᶜ` → `compl`, `{x | p x}` → `setOf`

### Algebra
`0` → `zero`, `+` → `add`, `-` → `neg`/`sub`, `1` → `one`, `*` → `mul`,
`^` → `pow`, `/` → `div`, `⁻¹` → `inv`, `∣` → `dvd`, `∑` → `sum`,
`∏` → `prod`, `•` → `smul`

### Order/lattice
`<` → `lt`/`gt`, `≤` → `le`/`ge`, `⊔` → `sup`, `⊓` → `inf`,
`⨆` → `iSup`/`ciSup`, `⨅` → `iInf`/`ciInf`, `⊥` → `bot`, `⊤` → `top`

### Using `le`/`lt` vs `ge`/`gt`
Mathlib almost always writes `≤` and `<` rather than `≥` and `>`. Use `ge`/`gt` only:
- When arguments appear in swapped order vs. first `≤`/`<` in the name
- To match argument order of `=` or `≠`
- To describe the relation with swapped arguments

---

## Variable Conventions

| Variable | Conventional use |
|----------|-----------------|
| `u`, `v`, `w` | Universes |
| `α`, `β`, `γ` | Generic types |
| `a`, `b`, `c` | Propositions |
| `x`, `y`, `z` | Elements of a generic type |
| `h`, `h₁`, `h₂` | Hypotheses / assumptions |
| `p`, `q`, `r` | Predicates and relations |
| `s`, `t` | Sets / lists |
| `m`, `n`, `k` | Natural numbers |
| `i`, `j` | Integers / indices |
| `G` | Group |
| `R` | Ring |
| `K`, `𝕜` | Field |
| `E` | Vector space |
| `f`, `g` | Functions |
| `μ`, `ν` | Measures |

---

## Prop-Valued Classes

### `Is`-prefix convention

- **Noun-based classes** → prefix with `Is`: `IsTopologicalRing`, `IsNoetherian`
- **Adjective-based classes** → no prefix needed: `Normal` (subgroup), `Finite`

Test: "assume the ring R is ___". If the blank is a noun phrase, use `Is`.
"Is topological" sounds odd → use `IsTopologicalRing`.
"Is normal" sounds fine → `Normal` is OK.

---

## Structural Lemma Patterns

### Extensionality
```lean
-- Standard form: tagged @[ext]
@[ext]
theorem MyType.ext (h : ∀ x, f x = g x) : f = g := ...

-- Iff form
theorem MyType.ext_iff : f = g ↔ ∀ x, f x = g x := ...
```

### Injectivity
```lean
-- Primary form: Function.Injective conclusion
theorem f_injective : Function.Injective f := ...

-- Bidirectional (often @[simp])
@[simp]
theorem f_inj : f x = f y ↔ x = y := ...
```

### Induction/recursion naming

| Motive eliminates into | Value first | Constructions first |
|------------------------|-------------|-------------------|
| `Prop` | `T.induction_on` | `T.induction` |
| `Sort u` / `Type u` | `T.recOn` | `T.rec` |

### Expanded vs unexpanded function forms

`f * g` (unexpanded) vs `fun x ↦ f x * g x` (expanded):
```lean
-- Unexpanded form
theorem Continuous.mul (hf : Continuous f) (hg : Continuous g) :
    Continuous (f * g) := ...

-- Expanded form: prefix with fun_
theorem Continuous.fun_mul (hf : Continuous f) (hg : Continuous g) :
    Continuous fun x ↦ f x * g x := ...
```

---

## Code Formatting

### Line length
Maximum **100 characters** per line. URLs may exceed this.

### Indentation
2 spaces. No tabs.

### Tactic blocks
```lean
-- One tactic per line in general
theorem foo : P := by
  intro h
  rw [bar] at h
  exact h.symm

-- Short closers can be inline
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Nat.succ_eq_add_one]
    linarith
```

### Operators
- Use `<|` not `$` for pipe operator
- Use `fun` not `λ` for anonymous functions
- Use `·` (Unicode middle dot) not `.` for focusing dots

### Parentheses
Don't orphan parentheses. Keep them with their arguments:
```lean
-- ✓ Good
theorem foo (h₁ : P)
    (h₂ : Q) : R := by
  ...

-- ✗ Bad
theorem foo
  (h₁ : P
  )
  (h₂ : Q
  ) : R := by
  ...
```

### Term-mode proofs
Indent continuation arguments:
```lean
theorem foo : R :=
  bar baz
    (qux quux)
    corge
```

---

## File Organization

### File header
```lean
/-
Copyright (c) 2026 Author Name. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Author Name, Coauthor Name
-/
module

public import Mathlib.Foo.Bar
public import Mathlib.Baz.Qux

/-!
# Title of the file

This file defines `MyDefinition` and proves basic properties.

## Main definitions
- `MyDefinition`: brief description

## Main results
- `myDefinition_property`: brief description of the theorem

## Implementation notes
Any non-obvious design choices.

## References
- [Author, *Title*][bibkey]
-/

public section
```

In projects using the module system, only ordinary comments may precede `module`. Use
`public import` for what the public interface needs and plain `import` for
proof-only dependencies (see the `lean-project-architecture` skill's
`references/module-system.md`).

### Import ordering
1. Mathlib imports first
2. Project imports second
3. No blank lines between imports

### Sections and namespaces
- Close all sections/namespaces before end of file (the `missingEnd` linter checks this).
- Exception: the outermost `public section` (or `noncomputable section`) may be left open.

### File size
Keep files focused; roughly 1000 lines is a useful point to consider splitting.
Follow the pinned Mathlib linters and any stricter project or publication limits.

---

## Documentation

### Module docstrings
Every file needs a `/-! ... -/` module docstring after the imports, describing:
- What the file defines / proves
- Main definitions (bulleted)
- Main results (bulleted)
- Implementation notes (if any)
- References (if any)

### Declaration docstrings
Use `/-- ... -/` before definitions and significant theorems:
```lean
/-- The Hölder exponent conjugate to `p`. Returns `0` when `p = 1`. -/
def conjExponent (p : ℝ≥0∞) : ℝ≥0∞ := ...
```

### Language
Documentation uses American English spelling. (Code identifiers also use American English:
`factorization` not `factorisation`, `FiberBundle` not `FibreBundle`.)

---

## Linting

Run `#lint` at the end of every file before submission. Key linters:

| Linter | What it checks |
|--------|---------------|
| `longFile` | File exceeds line limit |
| `longLine` | Line exceeds 100 characters |
| `unusedArguments` | Theorem has unnecessary hypotheses |
| `docBlame` | Public declaration missing docstring |
| `simpNF` | `@[simp]` lemma is not in normal form |
| `dupNamespace` | Redundant namespace repetition |
| `setOption` | Disallowed `set_option` commands |
| `lambdaSyntax` | Uses `λ` instead of `fun` |
| `dollarSyntax` | Uses `$` instead of `<|` |
| `cdotLinter` | Uses wrong character for `·` |

### `@[simp]` rules
A simp lemma `A = B` must have B "simpler" than A. The simplifier only rewrites left
to right. Bad simp lemmas cause loops. The `simpNF` linter catches common mistakes.

Normal forms to know:
- `0 < n` (not `n ≠ 0` or `n > 0` for `Nat`)
- `s.Nonempty` (not `s ≠ ∅`)
- `≤` preferred over `≥`
