# Provenance and adaptation

This collection is a Lean-focused export of a private instruction collection.
Its original Git history and private project records are not distributed.

The export retains Lean workflows and their supporting scripts, tests, assets,
and references, plus the source-level proof dependency graph workflow. It
omits manuscript-writing and website skills. The project-specific workflow
router was renamed to `lean-workflow` and rewritten for general Mathlib/Lake
projects.

Personal references, private project names, workstation paths, internal
incident histories, and project-specific profiling numbers were removed.
Detailed transferable proof patterns were retained or rewritten into neutral
examples. Carrier choices, build policies, module-system adoption, agent
configuration, and registry requirements are conditional on the target project.
Source-to-statement audits, frozen declarations, draft quarantine, unique
characterization, provider sealing, axiom checks, and independent review remain
part of the formalization workflows.

The repository verifier was adapted to the standalone layout. The installer
and its tests were added for reproducible local setup. Existing graph,
frozen-anchor, module-layout, and line-counting helpers were retained with
portable metadata and descriptions.

Independent review also exposed two gaps in the frozen-anchor checker. The
export now enforces draft-provider quarantine and uses raw-byte hashes for
frozen files and definition closure, with dedicated regression tests for
provider bypasses and line-ending changes. Repository scrub patterns can be
supplied from an external file without embedding private names in the export.

Public-source attributions are in [SOURCES.md](SOURCES.md). Adapted MIT
material is identified inline and in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
References to the Apache-2.0 Lean-team workflow collection remain attributed;
its license is included in [LICENSES/Apache-2.0.txt](LICENSES/Apache-2.0.txt).
The original portions of this collection are licensed under CC BY 4.0 (see
[LICENSE](LICENSE)); third-party portions retain their own notices and license
terms.
