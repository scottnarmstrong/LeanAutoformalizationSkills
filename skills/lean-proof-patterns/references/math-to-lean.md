# Math-to-Lean Phrasebook

> **Sources:** Adapted from cameronfreer/lean4-skills
> [lean-phrasebook.md](https://github.com/cameronfreer/lean4-skills/blob/main/plugins/lean4/skills/lean4/references/lean-phrasebook.md), which is
> itself inspired by [Terence Tao's Lean Phrasebook](https://docs.google.com/spreadsheets/d/1Gsn5al4hlpNc_xKoXdU6XGmMyLiX4q-LFesFVsMlANo/).
> For the full version with more examples, see cameronfreer's original.
> See [Sources and References](../../../SOURCES.md) for full citations.

This reference translates mathematical proof language into Lean 4 tactic proofs.
Organized by the kind of reasoning step you want to express.

---

## Forward Reasoning (building from what you know)

| Math phrase | Lean |
|------------|------|
| "Observe that A holds because r" | `have h : A := by r` |
| "We claim A. [proof]" | `have h : A := by ...` |
| "X equals Y by definition" | `have : X = Y := rfl` |
| "From h, applying f gives B" | `have hB : B := f h` |
| "The claim follows from h" | `exact h` or `assumption` |
| "This follows by definition" | `rfl` |
| "Replace h with its consequence" | `replace h := f h` |
| "h is no longer needed" | `clear h` |

## Backward Reasoning (working from the goal)

| Math phrase | Lean |
|------------|------|
| "By lemma A, it suffices to show..." | `apply A` |
| "It suffices to show B" | `suffices h : B by ...` then prove B |
| "Later we'll prove A; assume it now" | `suffices h : A from ...` then prove A |
| "We need to show A'" | `show A'` |
| "By definition, the goal is A'" | `change A'` |
| "We reduce to a close variant" | `convert my_lemma using n` |

### Do Not Turn Proof Sections Into Assumptions

Use `suffices` and helper lemmas for local proof decomposition only.  When
formalizing a paper theorem, do not replace a major analytic section by adding
that section's conclusion as a hypothesis to the public theorem.

If the paper proves:

```text
A -> Step 1 -> Step 2 -> B
```

then the Lean development must contain theorems proving `Step 1` and `Step 2`
from the approved concrete inputs before the final theorem proves `B`.

The public theorem

```lean
theorem final (hA : A) (hStep1 : Step1) (hStep2 : Step2) : B
```

is not a formalization of `A -> B`; it is only a conditional scaffold.  Treat
auditor phrases such as "certified under the abstract interface" or
"conditional certification" as failures when the user asked for the implication
itself.

## Case Analysis

| Math phrase | Lean |
|------------|------|
| "h says A or B; split into cases" | `rcases h with hA \| hB` |
| "Either P or ¬P" | `by_cases h : P` |
| "We split into cases n = 0 and n = k+1" | `cases n with \| zero => ... \| succ k => ...` |
| "We induct on n" | `induction n with \| zero => ... \| succ n ih => ...` |

## Quantifiers

| Math phrase | Lean |
|------------|------|
| "Assume A holds" / "Let x ∈ X" | `intro hA` / `intro x hx` |
| "Take x = a [to prove ∃ x, P x]" | `use a` |
| "By h, ∃ x with P(x); call it x₀" | `obtain ⟨x₀, hx₀⟩ := h` |
| "Since h : ∀ x ∈ X, P x, apply to a" | `have := h a ha` or `specialize h a ha` |
| "Select a canonical element" | `let x := h.some` |

## Conjunction, Disjunction, Iff

| Math phrase | Lean |
|------------|------|
| "To prove A ∧ B, prove each" | `constructor` or `exact ⟨proof_A, proof_B⟩` |
| "From h : A ∧ B, extract both" | `obtain ⟨hA, hB⟩ := h` or `h.1`, `h.2` |
| "To prove A ∨ B, we show A" | `left` (or `right` for B) |
| "To prove A ↔ B, prove both directions" | `constructor` |
| "By h : A ↔ B, convert A to B" | `rw [h]` or `h.mp hA` |

## Contradiction and Contrapositive

| Math phrase | Lean |
|------------|------|
| "We seek a contradiction" | `exfalso` |
| "But h and ¬h contradict" | `contradiction` or `absurd h nh` |
| "Suppose for contradiction ¬A" | `by_contra nh` |
| "Taking contrapositives" | `contrapose!` |
| "Push negation inward" | `push_neg` or `push_neg at h` |

## Equational and Inequality Reasoning

| Math phrase | Lean |
|------------|------|
| "Rewrite using h : X = Y" | `rw [h]` (left→right) or `rw [← h]` (right→left) |
| "Rewrite h in a hypothesis" | `rw [h] at hyp` |
| "Rewrite under binders (∀, ∃, ∫)" | `simp_rw [h]` (NOT `rw`) |
| "Chain of equalities/inequalities" | `calc x = y := by ... ; _ ≤ z := by ...` |
| "Both sides differ by monotone f" | `gcongr` |
| "Transitivity: X ≤ Y from X ≤ Z, Z ≤ Y" | `exact h₁.trans h₂` or `calc` |
| "X = Y by ≤ and ≥" | `apply le_antisymm` |

## Set Theory

| Math phrase | Lean |
|------------|------|
| "x ∈ S ∩ T means x ∈ S and x ∈ T" | `rcases hx with ⟨hxS, hxT⟩` |
| "To show x ∈ S ∪ T, show x ∈ S" | `left; exact hxS` |
| "S ⊆ T means ∀ x ∈ S, x ∈ T" | `intro x hx` |
| "To show S = T, show mutual inclusion" | `ext x; constructor <;> intro h ...` |
| "The preimage of S under f" | `f ⁻¹' S` |
| "The image of S under f" | `f '' S` |

## Extensionality

| Math phrase | Lean |
|------------|------|
| "Two functions equal iff equal pointwise" | `ext x` |
| "Two sets equal iff same membership" | `ext x` |
| "Two linear maps equal iff equal on all inputs" | `ext x` |
| "Two morphisms equal iff ..." | `ext` (works for most bundled types) |

## Algebraic Reasoning

| Math phrase | Lean |
|------------|------|
| "By ring arithmetic" | `ring` |
| "Clear denominators, then ring" | `field_simp; ring` |
| "By group calculation" | `group` (multiplicative) or `abel` (additive) |
| "By linear arithmetic" | `linarith` or `omega` (for ℕ/ℤ) |
| "Obviously nonneg/positive" | `positivity` |
| "By numerical computation" | `norm_num` |

## Almost-Everywhere Reasoning (Measure Theory)

| Math phrase | Lean |
|------------|------|
| "P holds for all x" → "P holds a.e." | `ae_of_all μ h` |
| "Combine a.e. hypotheses pointwise" | `filter_upwards [h₁, h₂] with x hx₁ hx₂` |
| "a.e. equal functions have equal integrals" | `integral_congr_ae h` |
| "P holds a.e., so Q holds a.e." | `filter_upwards [hP] with x hx; exact ...` |

## Goal Management

| Math phrase | Lean |
|------------|------|
| "The other goal first" | `swap` |
| "Apply same tactic to all goals" | `all_goals ...` or `<;> ...` |
| "This goal is trivial" | `trivial` or `simp` |
| "Skip this for now" | `sorry` (development only — never in finished code) |
| "Show what simp would do" | `simp?` → replace with `simp only [...]` |
| "What lemma closes this?" | `exact?` (development only) |
