# Maintaining LeanAutoformalizationSkills

This repository contains portable Lean 4 formalization skills for Codex and Claude Code.
The shared instructions live in `skills/<name>/SKILL.md`; supporting scripts,
references, assets, and tests travel with each skill.

- Keep one editable source for each skill. Keep metadata and cross-links consistent.
- Preserve exact source-to-statement fidelity, independent audits, draft quarantine,
  and the distinction between source topology and Lean proof status.
- Make project conventions conditional. Do not embed personal names, private project
  names, absolute workstation paths, or internal campaign histories in examples.
- Preserve public-source attribution and third-party license notices.
- Give delegated work disjoint write sets; have a fresh reviewer check substantial edits.
- Read a skill and its relevant resources before changing it. Run its bundled tests
  when changing a script; validate metadata and links after structural changes.
- Do not modify existing skill installations as a side effect of editing this repository.
- Repository visibility, commits, and pushes follow the user's current authorization.
