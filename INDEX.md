# Skill index

All editable skill sources live under `skills/`. Each directory is a complete
shared skill for Codex and Claude Code; `agents/openai.yaml` supplies Codex UI
metadata. Supporting Python files, tests, references, and assets are retained.

| Skill | Entry point |
| --- | --- |
| `lean-workflow` | [Workflow router](skills/lean-workflow/SKILL.md) |
| `lean-project-architecture` | [Project architecture](skills/lean-project-architecture/SKILL.md) |
| `build-proof-dependency-graph` | [Source dependency graph](skills/build-proof-dependency-graph/SKILL.md) |
| `lean-orchestrator` | [Proof orchestration](skills/lean-orchestrator/SKILL.md) |
| `lean-statement-audit` | [Statement and proof audit](skills/lean-statement-audit/SKILL.md) |
| `lean-search-discovery` | [Mathlib discovery](skills/lean-search-discovery/SKILL.md) |
| `lean-proof-patterns` | [Proof patterns](skills/lean-proof-patterns/SKILL.md) |
| `lean-naming-style` | [Naming and style](skills/lean-naming-style/SKILL.md) |
| `lean-learnings` | [Analysis and elaboration lessons](skills/lean-learnings/SKILL.md) |
| `lean-elaboration` | [Elaboration repair](skills/lean-elaboration/SKILL.md) |
| `lean-elaboration-test` | [Performance reporting](skills/lean-elaboration-test/SKILL.md) |
| `lean-public-release` | [Formalization release](skills/lean-public-release/SKILL.md) |

Begin with `lean-workflow` when you need routing. Use narrow proof/search/style
skills directly for local tasks. The graph and audit workflow is appropriate
for source-facing formalizations that need exact mathematical correspondence.

See [README.md](README.md) for installation and examples, and
[SOURCES.md](SOURCES.md) for public-source attribution.
