# Tool Index

This file collects the tools and services mentioned elsewhere in the repository.  It is intentionally duplicative.  It does not try to list every primitive tactic in Lean, focusing instead on search, automation, project tooling, and external resources.

## Search and Discovery

Search should start before proof writing.  Some tools inspect the current goal, while others search Mathlib by text, type, or natural language.  [Search and Discovery](search-and-discovery.md) gives the complete workflow.

### Goal-state search tactics

| Tool | Use | Notes | Primary reference |
|------|-----|-------|-------------------|
| `exact?` | Find a lemma that closes the current goal | Discovery only.  Replace it in finished proofs. | [Search and Discovery](search-and-discovery.md), [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| `apply?` | Find a lemma whose conclusion matches the goal head | Discovery only.  It may leave subgoals. | [Search and Discovery](search-and-discovery.md), [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| `rw?` | Find candidate rewrite lemmas | Useful when the goal is close to the right normal form. | [Search and Discovery](search-and-discovery.md), [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| `simp?` | Report which lemmas `simp` used | Main way to turn `simp` into `simp only [...]`. | [Search and Discovery](search-and-discovery.md), [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| `hint` | Try several tactics and report successes | Useful when the next step is unclear. | [Search and Discovery](search-and-discovery.md) |
| `#check`, `#print` | Verify that a discovered name has the right statement | Use after any search hit. | [Search and Discovery](search-and-discovery.md) |

### External search services and local inspection

| Tool | Use | Notes | Primary reference |
|------|-----|-------|-------------------|
| `rg`, `rg --files`, `ls` | Search `.lake/packages/mathlib` by file name or text | Start with local text and filename searches. | [Search and Discovery](search-and-discovery.md) |
| Editor or Read tool | Inspect lines around a search hit | Use after a text search narrows the file. | [Search and Discovery](search-and-discovery.md) |
| [Loogle](https://loogle.lean-lang.org/) | Search Mathlib by type pattern | Best when the theorem shape is clearer than the name. | [Search and Discovery](search-and-discovery.md), [Sources and References](../../../SOURCES.md) |
| [LeanSearch](https://leansearch.net/) | Search Mathlib by natural language | Best for plain-English theorem descriptions. | [Search and Discovery](search-and-discovery.md), [Sources and References](../../../SOURCES.md) |
| [Moogle](https://www.moogle.ai/) | Search semantically across Lean code | Alternative search service listed in the sources. | [Sources and References](../../../SOURCES.md) |
| [Mathlib API docs](https://leanprover-community.github.io/mathlib4_docs/) | Browse declarations, imports, and module docs | Useful after search narrows the namespace or file. | [Sources and References](../../../SOURCES.md) |
| [Lean Zulip](https://leanprover.zulipchat.com/) | Search prior discussions and ask blockers | Use when local and public search fail. | [Search and Discovery](search-and-discovery.md), [Sources and References](../../../SOURCES.md) |

## Proof Automation and Specialized Tactics

These tools discharge common goal shapes or automate routine steps.  They are effective when the goal shape matches the tactic's domain.  [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) is the main reference, with domain docs adding specialized cases.

| Tool | Best for | Notes | Primary reference |
|------|----------|-------|-------------------|
| `ring` | Commutative semiring and ring equalities | Also appears in algebra, combinatorics, and linear algebra guidance. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md), Algebra and number theory |
| `field_simp` | Clearing denominators in field expressions | Often followed by `ring`. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md), Algebra and number theory |
| `omega` | Linear arithmetic over `Nat` and `Int` | Called out for cardinality and range arguments in combinatorics. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md), Combinatorics |
| `linarith` | Linear arithmetic over ordered fields | Used broadly, including dimension arguments. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md), Linear algebra |
| `nlinarith` | Nonlinear arithmetic with key side inequalities | Heuristic.  Supply useful intermediate facts. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| `norm_num` | Numerical normalization and concrete arithmetic | Also useful for matrix and field computations. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md), Linear algebra |
| `positivity` | Prove nonnegativity or positivity goals | Common companion to `linarith`. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| `norm_cast`, `push_cast` | Normalize coercions and cast-heavy goals | Use before arithmetic tactics when casts obscure the goal. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| `aesop` | General automation | Useful, but the repo treats it as secondary to explicit proofs. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| `grind` | Congruence closure and E-matching | General-purpose automation in Lean 4. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md), [Sources and References](../../../SOURCES.md) |
| `fun_prop` | Continuity, measurability, and differentiability of composed functions | Treated as the first choice in analysis and topology. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md), Measure theory and analysis, Topology |
| `measurability` | Measurability goals | First attempt for pure measurability proofs. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md), Measure theory and analysis |
| `continuity` | Continuity goals | Older than `fun_prop`, but still useful. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md), Topology |
| `gcongr` | Inequality transport through monotone contexts | Especially useful inside `calc` blocks. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md), [Math-to-Lean Phrasebook](../../lean-proof-patterns/references/math-to-lean.md) |
| `mono` | Monotonicity lemmas | Listed as a domain-specific automation tool. | [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| `aesop_cat` | Category-theory automation | Standard tactic for functoriality, naturality, and diagram lemmas. | Category theory, [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| `slice_lhs`, `slice_rhs`, `reassoc` | Category-theory rewriting inside composition chains | Useful for diagram chasing that `aesop_cat` does not close directly. | Category theory |

Basic structural tactics such as `intro`, `constructor`, `rcases`, `ext`, `conv`, and `calc` remain important.  They are documented in [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) and [Math-to-Lean Phrasebook](../../lean-proof-patterns/references/math-to-lean.md).  This file keeps the focus on the tactics the repo treats as tools for discovery, automation, or workflow.

## Project and Environment Tooling

Proof search is only part of the workflow.  Build settings, profiling, and project structure determine how quickly a large formalization moves.  [Project Architecture](../../lean-project-architecture/references/project-architecture.md) is the main reference here.

| Tool | Use | Notes | Primary reference |
|------|-----|-------|-------------------|
| [leanblueprint](https://github.com/leanprover-community/leanblueprint) | Plan theorem dependencies and connect prose to declarations | Recommended for projects with many interdependent lemmas. | [Project Architecture](../../lean-project-architecture/references/project-architecture.md), [Sources and References](../../../SOURCES.md) |
| `set_option profiler true in` | Profile slow declarations | Use locally and scope it tightly. | [Project Architecture](../../lean-project-architecture/references/project-architecture.md), [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| Scoped heartbeat options | Diagnose whether a timeout is budget-related | Follow repository policy; profile and refactor before accepting a budget increase. | [Project Architecture](../../lean-project-architecture/references/project-architecture.md), [Tactics and Automation](../../lean-proof-patterns/references/tactics-and-automation.md) |
| `autoImplicit false` | Prevent accidental free variables at the project level | Set in the lakefile. | [Project Architecture](../../lean-project-architecture/references/project-architecture.md) |
| `#lint` | Check style and API hygiene before a PR | Also tied to naming and documentation rules. | [Project Architecture](../../lean-project-architecture/references/project-architecture.md), [Naming and Style](../../lean-naming-style/references/naming-and-style.md) |
| `lake exe cache get` | Fetch cached artifacts for the pinned dependency version | Follow the repository setup policy; change dependency pins only when authorized. | [Sources and References](../../../SOURCES.md) |

## External Workflow Packs and Community Resources

Some useful tools live outside Mathlib itself.  They help with compilation repair, PR workflow, and operational questions that the local docs leave to upstream references.  These resources complement the local material rather than replacing it.

| Resource | Use | Notes | Primary reference |
|----------|-----|-------|-------------------|
| [cameronfreer/lean4-skills](https://github.com/cameronfreer/lean4-skills) | Operational Lean workflow for agents | Covers prove-review-golf loops, compilation debugging, and deeper tactic references. | [Lean skill index](../../../INDEX.md), [Sources and References](../../../SOURCES.md) |
| [leanprover/skills](https://github.com/leanprover/skills) | Official Lean-team workflow skills | Covers `mathlib-pr`, `mathlib-review`, `mathlib-build`, and related workflows. | [Lean skill index](../../../INDEX.md), [Sources and References](../../../SOURCES.md) |
| [Lean Zulip](https://leanprover.zulipchat.com/) | Community discussion and current practice | Useful when the docs lag behind current Mathlib behavior. | [Search and Discovery](search-and-discovery.md), [Sources and References](../../../SOURCES.md) |
