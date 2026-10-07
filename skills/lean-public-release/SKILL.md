---
name: lean-public-release
description: Prepare and verify a private Lean repository for public release. Use for source scrubbing, selective syncs, clean history, proof-status and license review, fresh-checkout builds, optional registry or comparator intake, independent review, and an explicit publication gate.
---

# Lean public release

Prepare a reader-facing public repository without exposing private paths,
internal history, credentials, campaign records, or unpublished source
material. Read the repository's instructions and release destination rules
before choosing a workflow. Preparing a release does not itself authorize a
commit, push, visibility change, registry submission, or publication.

## Freeze the release contract

Record before editing:

- the exact source revision and release target;
- which library modules, verification tools, documentation, metadata, and
  license files will ship;
- the intended proof-status policy, including any authorized drafts;
- third-party code, data, text, and licenses that require attribution;
- whether the public repository is a one-time export or a maintained mirror;
- optional destination requirements such as a registry, archive, or challenge
  format.

Preserve source-to-statement fidelity throughout. Scrubbing must not change
binders, carriers, quantifiers, hypotheses, conclusions, constants, endpoint
conditions, or unique-characterization semantics. Never convert a proof step
into an assumption or replace a definition with hypotheses about an abstract
object. Keep draft theorems quarantined and honestly labeled.

## Selective sync

- Use an allowlist of files and directories that may ship. Treat everything
  else as excluded until reviewed.
- Run a forbidden-reference lint on the trial tree. Check private repository
  names, usernames, absolute paths, scratch locations, internal issue or packet
  labels, credentials, unpublished-source paths, and excluded tooling.
- Keep a no-commit preview mode. Sync first to a disposable checkout and
  inspect the complete resulting tree and diff.
- If a fresh public history is desired, create it only after approval. A
  one-commit history is an option, not a universal requirement.
- Define how later public changes are synchronized. Do not assume rewriting
  published history is acceptable.

## Source and documentation scrub

Replace internal generation suffixes, work-item names, unstable line-number
citations, and private file references with stable public declaration names,
paper theorem numbers, labels, or public URLs. Verify every renamed declaration
and cross-reference mechanically where possible.

Do not erase provenance or required attribution. Preserve copyright notices,
third-party licenses, paper citations, and authorship information. Separate
release-facing explanations from private process history, but retain audit
artifacts that the release contract says are part of the public verification
story.

## Lean integrity gates

Run checks against the exact proposed public tree:

1. Search for unauthorized `sorry`, `admit`, custom axioms, placeholder
   definitions, theorem-shaped proposition packages, and disabled checks.
2. Run the repository's axiom audit from probes or a dedicated audit target.
   Do not leave expensive `#print axioms` commands in ordinary source files.
3. Confirm imports resolve only through declared dependencies at pinned
   revisions. Remove private path dependencies, source symlinks, copied build
   trees, and hidden search paths.
4. Build in a fresh checkout with empty project artifacts and the documented
   dependency setup. This is the isolation test; a build in the development
   checkout is insufficient.
5. Run every shipped checker exactly as documented for readers.
6. Compare public theorem statements with their authoritative sources after
   every rename or module move.

Respect local cache rules. A first-time fresh-checkout build may need to create
dependency artifacts; a guard designed for an already-populated development
checkout must account for that setup explicitly.

## Optional registry and challenge requirements

Apply this section only when the chosen destination requires it. Read the
current registry policy at release time; size limits, module rules, metadata,
and schemas can change.

If every Lean file must be a module, port project modules and shipped checkers
before release. Publish and pin project-owned dependencies in dependency order.
Validate module headers, imports, visibility modifiers, root names, and
aggregator files in the synced tree.

If comparator-style challenges are required:

- give each main result a challenge with the destination's required deliberate
  proof hole and a solution proving the byte-identical statement;
- match the allowed dependency closure and avoid private declarations whose
  generated names differ by module;
- define every source-defined notion needed by the statement inside the
  permitted challenge surface;
- for an object defined by unique characterization, include its actual
  construction or audited defining interface and verify existence and
  uniqueness without extra assumptions;
- use concise definitions to meet size limits; do not hide definitions in
  hypotheses or move them outside the reviewed closure;
- invalidate only the exact challenge artifacts before verification.

Registry-specific helper scripts from companion skills may be used only when
they exist in the installed skill set and match the destination's current
rules.

## Hosted CI

If the release ships continuous integration:

- Use two workflows, each with a README badge under the title: one builds the
  project and runs the axiom audit for every advertised theorem plus the module
  and metadata checks; the other runs the comparator checks with the independent
  kernel replay. Keep them manual-dispatch drafts until release, then trigger on
  pushes and pull requests to the default branch. Give each workflow its own
  build-cache key; restores may fall back to the other's prefix.
- Free disk space first in every workflow that builds the project or runs
  comparators. A hosted runner starts with roughly 14 GB free, and replaying an
  exported solution over the full Mathlib closure in an independent kernel
  exhausts it. The typical signature is that both builds and both exports
  succeed, then the kernel replay dies with `no space left on device`. That is an
  environment failure, not a verification failure, but it still fails the badge.
  Put a step like this right after checkout:

  ```yaml
      - name: Free runner disk space
        run: |
          set -Eeuo pipefail
          # Only remove preinstalled, unused SDKs on disposable hosted runners.
          if [[ "${RUNNER_ENVIRONMENT:-}" == github-hosted ]]; then
            sudo rm -rf /usr/share/dotnet /usr/local/lib/android /opt/ghc /opt/hostedtoolcache/CodeQL
            sudo docker image prune --all --force > /dev/null || true
          fi
          df -h .
          available_kib="$(df -Pk . | awk 'NR==2 {print $4}')"
          test "$available_kib" -ge 20971520
  ```

- Read the failing step's log before diagnosing. A failing comparator job after
  green local runs is usually a runner resource limit, not a statement mismatch.
- Let every workflow finish green on the exact pushed commit before the
  repository becomes public; badges show no status until a run completes.

## Reader-facing files

The README should tell a new reader:

- what is formalized and which source results correspond to it;
- the exact Lean toolchain and pinned dependencies;
- how to obtain caches or build dependencies, build the project, run audits,
  and reproduce optional challenges;
- which results belong to upstream dependencies;
- the honest status of drafts, gaps, axioms, and excluded material;
- the license and citation requirements.

GitHub renders README math after HTML sanitizing. Inside math, write `\lt` and
`\gt` instead of `<` or `>` directly before a letter or backslash
(`\sum_{i<j}` breaks the formula). Escape literal `$` outside code in generated
Markdown such as logs or transcripts. Check the rendered page on GitHub; local
renderers do not reproduce either failure.

Check `LICENSE`, citation metadata, repository metadata, and dependency
licenses together. A code license does not automatically cover manuscript text,
figures, datasets, or vendored third-party material.

## Independent review and release gate

Have a reviewer who did not perform the scrub inspect the exact proposed tree:

- statement and definition fidelity against pinned sources;
- proof status, axiom output, draft quarantine, and absence of proof smuggling;
- dependency isolation and fresh-checkout reproducibility;
- forbidden references, secrets, and private artifacts;
- README accuracy, licenses, attribution, and optional registry compliance.

Resolve each finding or record a justified disposition. Present the complete
release tree, README, verification results, unresolved limitations, and planned
external actions for approval. Only then perform the separately authorized
commit, push, visibility change, archive upload, or registry submission.

## Suggested sequence

1. Freeze scope, source revision, proof-status policy, licenses, and destination
   rules.
2. Scrub names and references in the private source while preserving statement
   meaning.
3. Prepare public documentation, metadata, licenses, and CI in draft form.
4. Build an allowlisted no-commit sync and burn forbidden-reference findings
   down to zero.
5. Verify the trial tree in a fresh checkout and run all shipped checks.
6. Obtain independent review and resolve findings.
7. Obtain explicit approval for the README and proposed external actions.
8. Commit or publish only within that approval.
