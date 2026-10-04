#!/usr/bin/env python3
"""Install the complete skill folders without replacing any existing installation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def install(source: Path, destination: Path, *, dry_run: bool = False) -> int:
    skills = sorted(p.parent for p in source.glob("*/SKILL.md"))
    if not skills:
        raise ValueError(f"no skill folders found in {source}")
    conflicts = []
    for skill in skills:
        target = destination / skill.name
        if target.is_symlink() and target.resolve() == skill.resolve():
            continue
        if target.exists() or target.is_symlink():
            conflicts.append(target)
    if conflicts:
        raise ValueError("existing skills would be replaced; no files changed:\n" +
                         "\n".join(str(p) for p in conflicts))
    if not dry_run:
        destination.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for skill in skills:
            target = destination / skill.name
            if target.is_symlink() and target.resolve() == skill.resolve():
                continue
            if dry_run:
                print(f"would link {target} -> {skill.resolve()}")
            else:
                target.symlink_to(skill.resolve(), target_is_directory=True)
                created.append(target)
    except OSError:
        for target in created:
            target.unlink()
        raise
    return len(skills)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True, choices=("codex", "claude"))
    location = parser.add_mutually_exclusive_group()
    location.add_argument("--project", type=Path, help="install for this Lean project")
    location.add_argument("--dest", type=Path, help="explicit skill directory, for compatibility or isolated tests")
    parser.add_argument("--dry-run", action="store_true", help="show links without writing anything")
    args = parser.parse_args(argv)
    platform = ".agents" if args.agent == "codex" else ".claude"
    destination = args.dest or ((args.project or Path.home()) / platform / "skills")
    source = Path(__file__).resolve().parent.parent / "skills"
    try:
        count = install(source, destination.expanduser().absolute(), dry_run=args.dry_run)
    except (ValueError, OSError) as error:
        print(f"installation failed: {error}", file=sys.stderr)
        return 1
    print(f"{'Checked' if args.dry_run else 'Installed'} {count} skills for {args.agent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
