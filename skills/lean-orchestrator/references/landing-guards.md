# Landing guards that resist bypass

A landing guard lets the orchestrator merge agent-written Lean without
re-reading every line. Every layer has a blind spot. These rules come from an
independent adversarial audit of a guard branch, in which each blind spot
below had a working bypass: a build that succeeded, a full freeze check that
exited 0, and a false or isolation-breaking result in the tree.

## 1. An axiom report is not a kernel check

`#print axioms` and axiom sweeps report what a constant's value refers to.
They do not show that the kernel checked the constant. Under
`debug.skipKernelTC := true`, a declaration is added without kernel checking.
That can happen through `run_cmd`/`addDecl`, or inside a custom elaborator
that calls `mkAuxLemma` within `withOptions`. Such a declaration can "prove"
`(1 : Nat) = 2` and still report no axioms.

- Make a kernel replay a landing gate. Replay every constant of the changed
  modules with `Lean.Kernel.Environment.replay`, or run `leanchecker`, against
  an environment built from their imports.
- Run the full replay of every project module before any release or seal claim.

## 2. Lint metaprogramming anywhere, on masked code

A forbidden-construct lint must run on code with comments and strings masked,
and it must match **anywhere on a line**. A line-start pattern missed

```lean
open Lean Meta Elab Term in elab "fake" : term => ...
```

- Cover the elaborator commands: `elab`, `elab_rules`, `macro`, `macro_rules`
  and `syntax`.
- Cover the run commands: `run_cmd`, `run_elab`, `run_meta`, `run_tac` and
  `by_elab`, plus `addDecl` and `set_option debug.*`.
- Cover elaborator-registering attributes (`command_elab`, `term_elab`,
  `tactic`, `macro`), whether written as `@[…]` or as `attribute […]`.
- A `meta import` rule does not back up the `elab` rule. In a module file, an
  `elab` needs no `meta import`.
- After widening a pattern, re-lint the whole tree. Fix a false positive by
  narrowing the pattern, never by allow-listing a real elaborator.

## 3. Isolate libraries by allow-list over the transitive closure

Take a guard that keeps one library free of another project library, with a
deny-list of forbidden roots checked against **direct** imports. It held only
until a new `lean_lib` was added whose modules import the forbidden roots. A
library file that imports the new lib then depends on the forbidden code,
while every guard passes.

- Read the project's library roots from the lakefile, so a new lib is covered
  automatically.
- Allow only the permitted project roots plus external packages.
- Check the **transitive** import closure: `lean --deps`, or a header parser
  validated against it.
- Treat a new `lean_lib`, or a new import edge between project libraries, as a
  change to the guard's assumptions, and re-audit the guard.

## 4. Make a changed-only replay cover what changed

A quick replay of only the changed modules must:

- include untracked `.lean` files (`git ls-files --others --exclude-standard`),
  not only `git diff` against main;
- replay exactly the named module. `leanchecker M` treats `M` as a prefix, and
  for a root module that can be the whole library;
- report "0 changed modules" explicitly instead of passing silently.

Changed mode does not replay a module that was rebuilt only because one of its
imports changed. Yet an elaborator, macro or attribute from the changed module
can add constants to it. The full replay closes this gap.

## 5. Placeholders in Comparator Challenges

A Comparator Challenge states its theorems with `sorry` by design. A
whole-tree placeholder scan must neither reject every Challenge, which blocks
the comparator landing, nor skip the comparator directory, which lets
placeholders into Solutions.

- Authorize a bare `sorry` only in the file named by a `comparator.json`'s
  `challenge_module`. Resolve that file from the JSON, never by a glob.
- Never authorize `admit`, a `sorry` in the `solution_module`, or a Challenge
  equal to the Solution.
- Authorize it only while no project module imports the Challenge.

The bundled `scripts/check_frozen_anchors.py` implements exactly this. A
comparator branch runs the project's full landing guard before it claims to
be ready; Comparator's own check does not stand in for it.

## 6. Test the guards with mutations, and audit them independently

- Give every layer a recorded mutation it must catch, in a test script run on
  every guard change.
- Record **which** layer caught each mutation. A mutation caught only by the
  last layer means an earlier layer has a gap.
- Require exit status 0 **and** the success marker from every guard
  subprocess. A stale marker in the output must not pass a failed run.
- Before merging a guard change, an independent auditor adds new mutations.
  The change merges only when those are caught too. Each new bypass becomes a
  permanent mutation test.
