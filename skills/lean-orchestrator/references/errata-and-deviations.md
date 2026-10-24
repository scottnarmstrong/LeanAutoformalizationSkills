# Errata and deviations record

Every formalization of published mathematics ships a reader-facing record,
`docs/ERRATA-AND-DEVIATIONS.md`, of where the Lean statements and proofs
differ from the printed sources and why. A reader comparing a Lean theorem
with the paper should find every intentional difference explained there.

Collect findings during the campaign, write the record near release, and
publish nothing until an independent verifier has checked each erratum against
the pinned source.

## What counts

- **Erratum:** a defect in the pinned source itself. Kinds: *typo* (misprint
  with clear intended meaning), *wrong constant/sign*, *missing hypothesis*
  (false without an extra condition), *false as stated*, and *gap* (the
  printed argument does not prove the printed step).
- **Deviation:** a deliberate difference that is not a source error: scope,
  conventions (including Lean's total functions such as `x / 0 = 0`),
  interpretation of an ambiguous phrase, strengthened, specialized or
  reformulated statements, explicit parameter windows in place of "small
  enough", proof supplements, and different proof routes.
- **Neither:** repairs of the project's own intermediate statements, versioned
  successors, retired routes, design mistakes, and open proof obligations.
  These are not errata. Mention them, if at all, as route deviations in
  reader-facing language.

Fix one policy for gaps and state it in the introduction. A conservative
default is to call a gap an erratum only when a printed assertion is false, and
to list a supplied missing argument for a true step as a deviation.

A published erratum is a public claim that named authors made an error. When
in doubt, classify the item as a deviation or leave it out.

## During the campaign: keep a findings ledger

Open the ledger when the sources are pinned. Each entry records:

- the source, its pinned version, and the exact location (page, theorem,
  equation, or LaTeX label);
- the printed text, quoted;
- the claimed defect and its kind;
- the evidence: a counterexample, an inconsistency proof, or the corrected
  statement;
- its status (`CANDIDATE`, `CONFIRMED`, `CONVENTION`, `DROPPED`) and who
  checked it.

Feed it from statement transcription and audits, source-gap nodes of the
dependency graph, worker stop reports, reviewer findings, and author rulings.
A confirmed erratum that changes a frozen statement goes through the normal
author-ruling and freezing procedure; the ledger records why the statement
departs from the print.

Certify an erratum in Lean where practical: a theorem that refutes the printed
claim (an impossibility or inconsistency theorem) and the theorem that proves
the corrected statement. These files are release evidence. Keep them through
dead-code removal, convert them to modules, and give them reader-facing names.

## At release: write the record

Draft after the main statements are sealed. Finalize after the last rename and
comment-scrub pass, since renames break links.

**File.** `docs/ERRATA-AND-DEVIATIONS.md`, titled "Errata and deviations".

**Introduction.** One paragraph saying how errata are separated from
deviations; the pinned version of each source (arXiv version or journal pages);
how locations are given (when printed numbers differ between versions, cite
the pinned version or the source's LaTeX labels); and the counting convention
(entries, not occurrences; whether editorial misprints count; a grouped entry
may cover repeated occurrences). If no erratum affects the main results, say so
here, naming the main theorems and their axioms.

**Count table.** `Source | Errata | Deviations`, one row per source, with a
total row when there are several sources.

**One section per source**, with `### Errata` then `### Deviations`, both
numbered. Each entry:

1. opens with the bold location, e.g. **p. 91, Proposition 6.12, (6.10)–(6.12).**;
2. states the kind and what is printed;
3. gives the correction; for a statement claimed false, an explicit
   counterexample;
4. states the effect: "No effect on the stated theorems", or exactly what
   changes in which formal statement;
5. links the certifying Lean file with a relative path and names the
   declaration, e.g. "see `not_printed_bound` in" followed by a Markdown link
   whose target is `../Project/Inconsistency.lean`.
   If a counterexample is only explained in a docstring, say it is not a Lean
   theorem.

A deviation states the choice actually made, never a menu of options, and its
effect on the formal statement. For a long list, put a summary table
(`# | Location | Kind | Lean statement`) before the details. Write "None"
under a heading that has no entries.

**Final sections.** How the formal proof route differs from the primary
source's proof; what is outside scope; and pinned sources used only as
references.

**README.** Add an "Errata and deviations" section: link to the record, counts
per source, and two to four headline items in one or two sentences each.
Update the counts whenever the record changes.

## Verification before publication

1. **Writer check.** The writer checks every erratum against the pinned PDF:
   location, quoted text, and that it really is wrong. Look first for a
   standing assumption, earlier convention, remark, or definition that already
   supplies the missing hypothesis; many apparent errata disappear there.
   Never fabricate a location. List every dropped finding, with its reason, in
   the handoff, not in the record.
2. **Independent verifier.** A fresh reviewer who did not write the record,
   preferably a strong model from a different family, takes a refute-first
   brief and does not edit the record. Per erratum: locate and quote the
   pinned text, search for conventions that supply the hypothesis, recheck the
   counterexample mathematically, read the cited Lean declaration, and return
   `CONFIRMED`, `CONVENTION-ISSUE` (move to deviations or drop), `WRONG`
   (drop) or `UNVERIFIABLE` (drop). Per deviation: is it accurate, a real
   difference, and the actual choice? Also check the proof-route section, run
   the language lint, and resolve every link. It returns a table (entry,
   verdict, quoted evidence, required change) and the exact edits.
3. **Apply and recount.** The writer applies the edits, recounts, and updates
   the README.
4. **Re-check links** after every later rename or scrub wave.

Treat a record that comes back much faster than the source reading could take
as unchecked.

## Language

The record is reader-facing. No agent or model names, work-item or gate names,
seal/ruling vocabulary, internal versions, dates, or private paths; only
relative links to shipped Lean files. Use the project's final declaration and
module names. Run the release's forbidden-language lint on the file.

## Briefs

Writer:

```text
Task: write docs/ERRATA-AND-DEVIATIONS.md (+ README section) in <worktree>.
Models: <paths to one or two earlier records>; read them fully first.
Sources: <short name, title, pinned version, PDF path> for each.
Mine: findings ledger, graph source-gap nodes, audits and reviews, author
  rulings, certifying regression tests (say what each refutes or repairs),
  git log for erratum/typo/gap/counterexample/inconsistent.
Rules: verify every erratum in the pinned PDF; drop what fails; never
  fabricate; our own statement repairs are not errata; reader-facing
  language; final Lean names, relative links; docs only, no Lean edits.
Handoff: commit, counts, every link, every dropped finding with its reason.
```

Verifier:

```text
Independent verifier; a wrong public erratum harms named authors, so be
conservative. Do not edit the record.
Record: <path>; writer notes: <path>; pinned PDFs: <paths>.
Per erratum: locate and quote; look for conventions supplying the hypothesis;
  recheck any counterexample; read the cited Lean declaration; verdict
  CONFIRMED / CONVENTION-ISSUE / WRONG / UNVERIFIABLE.
Per deviation and the proof-route section: accurate? real difference? actual
  choice stated?
Also: language lint, link resolution.
Output: <path> with verdict table (id, verdict, quoted evidence, change) and
  exact edits; summary of verdicts in the final message.
```
