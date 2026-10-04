# Mathlib Search and Discovery

> **Sources:** cameronfreer/lean4-skills
> [mathlib-guide.md](https://github.com/cameronfreer/lean4-skills/blob/main/plugins/lean4/skills/lean4/references/mathlib-guide.md);
> Mathlib naming conventions
> (leanprover-community.github.io/contribute/naming.html); Terence Tao's Lean 4 proof
> tours. See [Sources and References](../../../SOURCES.md) for full citations.

## Table of Contents

1. [Philosophy](#philosophy)
2. [In-Proof Search Tactics](#in-proof-search-tactics)
3. [Command-Line Search](#command-line-search)
4. [Naming Convention Search](#naming-convention-search)
5. [File Organization Search](#file-organization-search)
6. [Type-Signature Search (Loogle)](#type-signature-search-loogle)
7. [Natural Language Search (LeanSearch)](#natural-language-search-leansearch)
8. [Verification After Discovery](#verification-after-discovery)
9. [When Mathlib Does Not Have It](#when-mathlib-does-not-have-it)

---

## Philosophy

**Search before you prove.** Mathlib contains a large library of reusable declarations. Reproving an existing lemma wastes time and introduces maintenance
burden. The expected workflow is:

```
1. Understand what you need mathematically
2. Identify keywords, type signature, and likely name
3. Search using multiple complementary strategies
4. Verify with #check / #print
5. Import and use
6. If not found after exhaustive search, prove it yourself
```

Use **at least two** different search strategies before concluding that something is
missing from Mathlib.

---

## In-Proof Search Tactics

These are the fastest way to find lemmas when you already have a goal state:

### `exact?`
Searches for a single lemma that closes the current goal exactly.
```lean
example (a b : ℕ) (h : a ≤ b) : a ≤ b + 1 := by
  exact?  -- Try this: exact Nat.le_succ_of_le h
```

### `apply?`
Searches for a lemma whose conclusion unifies with the goal, possibly leaving subgoals.
```lean
example (f : ℝ → ℝ) (hf : Continuous f) (s : Set ℝ) (hs : IsCompact s) :
    IsCompact (f '' s) := by
  apply?  -- Try this: exact IsCompact.image hs hf
```

### `rw?`
Searches for rewrite lemmas applicable to the goal.
```lean
example (a b : ℝ) : a + b = b + a := by
  rw?  -- Try this: rw [add_comm]
```

### `simp?`
Runs `simp` and reports which lemmas were used. Essential for converting a bare
`simp` to `simp only [...]`.
```lean
example (a : ℝ) : a + 0 = a := by
  simp?  -- Try this: simp only [add_zero]
```

### `hint`
Tries multiple tactics and reports which ones work.

**Performance note:** These search tactics are expensive. Use them for discovery during
development, but replace them with explicit tactic calls in finished proofs.

---

## Command-Line Search

For AI assistants and power users working from a terminal:

### Find relevant files by pattern
```bash
# Find files containing both "continuous" and "compact"
find .lake/packages/mathlib -name "*.lean" \
  -exec grep -l "continuous.*compact\|compact.*continuous" {} \; | head -10

# Find files in a specific subdirectory
ls .lake/packages/mathlib/Mathlib/Topology/
```

### Search within files
```bash
# Search with line numbers (for targeted reading)
grep -n "lemma.*compact.*preimage" .lake/packages/mathlib/Mathlib/Topology/Compactness/*.lean

# Case-insensitive search
grep -in "harnack" .lake/packages/mathlib/Mathlib/Analysis/**/*.lean

# Search for theorem/lemma definitions matching a keyword
grep -rn "theorem\|lemma" .lake/packages/mathlib/Mathlib/MeasureTheory/ | grep "condExp"

# Use OR patterns for alternative phrasings
grep -rn "measure_union\|union_measure" .lake/packages/mathlib/Mathlib/MeasureTheory/
```

### Combine strategies
```bash
# Step 1: Find the right file
ls .lake/packages/mathlib/Mathlib/MeasureTheory/Function/

# Step 2: Search within it
grep -n "condExp.*add\|add.*condExp" \
  .lake/packages/mathlib/Mathlib/MeasureTheory/Function/ConditionalExpectation/*.lean

# Step 3: Read relevant section
# (use your editor or Read tool to examine lines around the match)
```

**Always limit output:** Append `| head -10` or `| head -20` to avoid being
overwhelmed.

---

## Naming Convention Search

Mathlib's naming is highly systematic. If you know the conventions, you can often
guess the lemma name directly.

### Core patterns

| Pattern | Meaning | Example |
|---------|---------|---------|
| `conclusion_of_hypothesis` | Implication | `continuous_of_isOpen_preimage` |
| `property_iff_characterization` | Equivalence | `compact_iff_finite_subcover` |
| `Structure.property` | Dot notation | `IsCompact.image` |
| `operation_structure` | Operation on structure | `integral_add`, `measure_union` |
| `property_operation` | Property of operation | `add_comm`, `mul_assoc` |

### Abbreviations used in names

| Abbreviation | Meaning |
|-------------|---------|
| `pos` | `0 < x` |
| `neg` | `x < 0` |
| `nonneg` | `0 ≤ x` |
| `nonpos` | `x ≤ 0` |
| `ne` | `≠` |
| `inj` | injective (bidirectional, `f x = f y ↔ x = y`) |
| `injective` | `Function.Injective f` |
| `mono` | `a ≤ b → f a ≤ f b` |
| `anti` | `a ≤ b → f b ≤ f a` |
| `monotone` | `Monotone f` |
| `strictMono` | `StrictMono f` |
| `ext` | extensionality |
| `ae` | almost everywhere (measure theory) |

### Searching by convention
```bash
# Looking for "conditional expectation of sum = sum of conditional expectations"
# Convention predicts: condExp_add
grep -rn "condExp_add\|add_condExp" .lake/packages/mathlib/Mathlib/MeasureTheory/

# Looking for "measure of union is at most sum"
# Convention predicts: measure_union_le
grep -rn "measure_union_le" .lake/packages/mathlib/Mathlib/MeasureTheory/
```

### Symbol name dictionary

When translating symbols to name components:

| Symbol | Name component |
|--------|---------------|
| `∨` | `or` |
| `∧` | `and` |
| `→` | `of` (hypotheses) / `imp` |
| `↔` | `iff` |
| `¬` | `not` |
| `∈` | `mem` |
| `∪` | `union` |
| `∩` | `inter` |
| `⊔` | `sup` |
| `⊓` | `inf` |
| `⊥` | `bot` |
| `⊤` | `top` |
| `∣` | `dvd` |
| `∑` | `sum` |
| `∏` | `prod` |
| `•` | `smul` |
| `⁻¹` | `inv` |
| `ᶜ` | `compl` |
| `\` (set difference) | `sdiff` |

---

## File Organization Search

Mathlib's file hierarchy mirrors mathematical taxonomy. Knowing where to look is
often faster than grep.

```
Mathlib/
├── Algebra/           -- Algebraic structures
│   ├── Group/         -- Groups, subgroups, quotients
│   ├── Ring/          -- Rings, ideals
│   ├── Field/         -- Fields
│   ├── Order/         -- Ordered algebraic structures
│   └── Homology/      -- Homological algebra
├── Analysis/          -- Real and functional analysis
│   ├── Calculus/      -- Derivatives, integrals
│   ├── InnerProductSpace/
│   ├── NormedSpace/
│   ├── SpecialFunctions/  -- exp, log, trig, etc.
│   └── Fourier/
├── CategoryTheory/    -- Categories, functors, limits
├── Combinatorics/     -- Combinatorial structures
├── Data/              -- Concrete data types
│   ├── List/, Finset/, Multiset/
│   ├── Nat/, Int/, Rat/, Real/, Complex/
│   └── Polynomial/
├── Geometry/          -- Euclidean, manifolds
├── LinearAlgebra/     -- Vector spaces, matrices, tensors
├── MeasureTheory/     -- Measures, integration
│   ├── Measure/       -- Measure spaces, constructions
│   ├── Integral/      -- Lebesgue, Bochner integration
│   ├── Function/      -- Measurable functions, conditional expectation
│   └── Covering/      -- Covering lemmas (Vitali, Besicovitch)
├── NumberTheory/      -- Arithmetic, L-functions
├── Order/             -- Lattices, well-orders
├── Probability/       -- Independence, distributions
├── RingTheory/        -- Ideals, localization, Dedekind domains
├── SetTheory/         -- Cardinals, ordinals
├── Tactic/            -- Tactic implementations
└── Topology/          -- Topological spaces, metric spaces
    ├── Algebra/       -- Topological groups/rings
    ├── MetricSpace/
    └── UniformSpace/
```

### Navigation workflow
```bash
# Step 1: Identify the mathematical domain
# "I need something about Lebesgue integration"
ls .lake/packages/mathlib/Mathlib/MeasureTheory/Integral/

# Step 2: Read the file header / module docstring
head -30 .lake/packages/mathlib/Mathlib/MeasureTheory/Integral/Lebesgue.lean

# Step 3: Search for your specific concept
grep -n "lemma\|theorem" .lake/packages/mathlib/Mathlib/MeasureTheory/Integral/Lebesgue.lean | grep "integral_add"

# Step 4: Check neighboring files for related results
ls .lake/packages/mathlib/Mathlib/MeasureTheory/Integral/
```

---

## Type-Signature Search (Loogle)

Loogle (https://loogle.lean-lang.org/) searches Mathlib by **type pattern**. This is
extremely powerful when you know what types go in and come out, but don't know the name.

### Syntax
- `?a`, `?b`, `?c` — type variables (match any type)
- `_` — wildcard for any term
- `->` — function arrow
- `|-` — turnstile (for conclusions)

### Examples that work well
```
-- Find: (α → β) → List α → List β
(?a -> ?b) -> List ?a -> List ?b
-- Returns: List.map ✓

-- Find: composition of measurable functions
Measurable ?f -> Measurable ?g -> Measurable (?g ∘ ?f)
-- Returns: Measurable.comp ✓

-- Find: pushing forward a probability measure
IsProbabilityMeasure ?μ -> IsProbabilityMeasure (Measure.map ?f ?μ)
-- Returns: relevant pushforward lemmas ✓
```

### Combine type and name discovery
Use type patterns when the theorem's shape is clearer than its name. Check the
service's current query syntax; combine its results with local name searches.
Verify every result in the project's pinned Mathlib before using it.

---

## Natural Language Search (LeanSearch)

LeanSearch (https://leansearch.net/) accepts natural language queries and returns
Mathlib results. Good for when you know the concept but not the Lean phrasing.

### Example queries
- "continuous function preserves compact sets"
- "integral of sum equals sum of integrals"
- "Cauchy-Schwarz inequality"
- "preimage of open set under continuous map is open"

---

## Verification After Discovery

Always verify a candidate lemma before using it:

```lean
-- Check the type signature
#check IsCompact.image
-- IsCompact.image : IsCompact s → Continuous f → IsCompact (f '' s)

-- Check with all implicit arguments visible
#check @IsCompact.image
-- Shows every argument you might need to provide

-- Quick test in isolation
example (f : ℝ → ℝ) (hf : Continuous f) (s : Set ℝ) (hs : IsCompact s) :
    IsCompact (f '' s) :=
  hs.image hf
```

---

## When Mathlib Does Not Have It

Before giving up, try:

1. **Alternative phrasings:** "continuous image compact" ↔ "compact image
   continuous"; "integral sum" ↔ "sum integral".

2. **More general versions:** Mathlib may have the result for `ContinuousOn` instead
   of `Continuous`, or for `MeasurableSet` in a more general measure space. Check
   class hierarchy: `Continuous` vs `ContinuousOn` vs `ContinuousAt`.

3. **Building blocks:** Mathlib might not have `condExp_indicator` directly, but might
   have `condExp_const` + `condExp_mul` which combine to give it.

4. **Check Mathlib PRs:** The result might be in a pending pull request. Search
   https://github.com/leanprover-community/mathlib4/pulls.

5. **Ask on Zulip:** The Lean Zulip (https://leanprover.zulipchat.com/) channel
   `#mathlib` is the canonical place to ask "Is there a lemma for X?"

If truly missing, write it yourself and mark it clearly:
```lean
/-- TODO: this should be in Mathlib. See [Zulip thread / PR link]. -/
lemma my_missing_lemma : ... := by
  ...
```
