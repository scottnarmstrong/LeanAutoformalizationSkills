# Conditional repository-structure guidance

Repository layout should expose mathematical dependencies and keep common edit
and build paths cheap. It should follow the repository's established namespace,
build rules, and public API; no universal directory tree or line limit fits all
formalizations.

## Decide from dependencies

Organize by stable mathematical layers rather than the order of a manuscript or
the chronology of development. A common analysis project may have layers such
as ambient algebra, geometry, function spaces, deterministic estimates,
probability, and iteration. Use only the layers the project needs, and derive
their direction from actual imports.

Foundational modules should avoid importing downstream constructions. Leaf
theorem files may be heavier. Optional examples and applications can depend on
the core without sitting on its dependency spine.

## Split when there is a coherent API boundary

Consider splitting a file when it mixes definitions with a long proof, contains
several theorem families, creates avoidable imports, or blocks independent work.
Useful boundaries include:

- definitions and basic API versus major estimates;
- finite or exact results versus approximation and closure arguments;
- generic analytic tools versus application-specific assembly;
- scalar or entrywise lemmas versus bundled operator results.

Line counts are warning signals rather than laws. Prefer a focused file that a
reviewer can understand in one sitting. Before splitting, profile: a split that
repeats imports or a large variable context can increase total cost.

When an imported module path is already public, keep a thin umbrella module if
that preserves compatibility. Internal siblings should import the narrow
provider module rather than the umbrella.

## Imports and namespaces

- Use the existing project namespace. Choose a new namespace for longevity and
  collision avoidance, not for a temporary repository name.
- Import the narrowest stable provider of the declarations used.
- Avoid cycles by placing bridges in the lowest downstream module that can
  import both sides.
- Remember that `open` and `open scoped` commands do not propagate through
  imports.
- Add aggregator modules when they serve a real external API, not merely to
  mirror a directory.

## Definitions and theorem surfaces

Place a definition with its laws and elementary API. Put proof-heavy theorem
families in downstream modules. Keep representation changes near the module
that owns the representations. Expose final mathematical endpoints separately
from recovery data, transport plumbing, and implementation witnesses.

Temporary proof scaffolding must not harden into the public API. Do not encode
unproved steps as theorem hypotheses or theorem-shaped definitions. Track
source topology separately from Lean proof status.

## Before creating or moving a file

Ask:

1. What declarations does it consume and export?
2. Is there an existing narrow module with that responsibility?
3. Does the change reduce imports or merely move cost?
4. Does it preserve public module paths and namespace conventions?
5. Can it be reviewed and profiled independently?

After a structural change, check imports, metadata and cross-links, elaborate
each new child, and test representative downstream consumers.
