#!/usr/bin/env python3
"""Check structure and optional forbidden patterns; semantic review remains separate."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re
import sys
from urllib.parse import unquote

SKILL_NAMES = (
    "build-proof-dependency-graph", "lean-elaboration", "lean-elaboration-test",
    "lean-learnings", "lean-naming-style", "lean-orchestrator",
    "lean-project-architecture", "lean-proof-patterns", "lean-public-release",
    "lean-search-discovery", "lean-statement-audit", "lean-workflow",
)
REQUIRED_FILES = (
    "AGENTS.md", "CLAUDE.md", "INDEX.md", "README.md", "PROVENANCE.md",
    "SOURCES.md", "THIRD_PARTY_NOTICES.md", "LICENSE", "LICENSES/Apache-2.0.txt",
    "scripts/install_skills.py",
)
REQUIRED_PYTHON = (
    "skills/build-proof-dependency-graph/scripts/proof_depgraph.py",
    "skills/build-proof-dependency-graph/scripts/test_proof_depgraph.py",
    "skills/lean-orchestrator/scripts/check_frozen_anchors.py",
    "skills/lean-orchestrator/tests/test_check_frozen_anchors.py",
    "skills/lean-project-architecture/scripts/check_lean_modules.py",
    "skills/lean-project-architecture/tests/test_check_lean_modules.py",
    "skills/lean-elaboration-test/scripts/count_lean_lines.py",
)
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")


def validate(root: Path, forbidden_patterns: tuple[re.Pattern[str], ...] = ()) -> list[str]:
    failures = []
    for rel in REQUIRED_FILES + REQUIRED_PYTHON:
        if not (root / rel).is_file():
            failures.append(f"missing required file: {rel}")
    found = {p.parent.name for p in (root / "skills").glob("*/SKILL.md")}
    if found != set(SKILL_NAMES):
        failures.append(f"skill registry differs: missing={sorted(set(SKILL_NAMES)-found)}, extra={sorted(found-set(SKILL_NAMES))}")
    index = (root / "INDEX.md").read_text() if (root / "INDEX.md").is_file() else ""
    for name in SKILL_NAMES:
        skill = root / "skills" / name
        entry = skill / "SKILL.md"
        if not entry.is_file():
            continue
        text = entry.read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        body = frontmatter.group(1) if frontmatter else ""
        if not re.search(rf"^name:\s*{re.escape(name)}\s*$", body, re.M):
            failures.append(f"frontmatter name mismatch: {name}")
        if not re.search(r"^description:\s*\S", body, re.M):
            failures.append(f"missing description: {name}")
        if f"skills/{name}/SKILL.md" not in index:
            failures.append(f"index omits skill: {name}")
        metadata = skill / "agents/openai.yaml"
        if not metadata.is_file():
            failures.append(f"missing UI metadata: {name}")
        else:
            yaml = metadata.read_text()
            if f"${name}" not in yaml:
                failures.append(f"UI prompt omits skill invocation: {name}")
            short = re.search(r'^\s*short_description:\s*"([^"]+)"\s*$', yaml, re.M)
            if not short or not 25 <= len(short.group(1)) <= 64:
                failures.append(f"UI description must have 25–64 characters: {name}")
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if ".git" in rel.parts or "__pycache__" in rel.parts:
            continue
        if path.is_symlink():
            failures.append(f"export contains a symlink rather than an independent file: {rel}")
            continue
        for pattern in forbidden_patterns:
            if pattern.search(rel.as_posix()):
                failures.append(f"forbidden pattern in path: {rel}")
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # Binary artifacts require separate review; paths were checked above.
        if re.search(r"/(?:home|Users)/[A-Za-z0-9_.-]+/", text):
            failures.append(f"workstation path in export: {rel}")
        for pattern in forbidden_patterns:
            for line_number, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    failures.append(f"forbidden pattern in content: {rel}:{line_number}")
        if path.suffix == ".py":
            try:
                ast.parse(text, filename=str(path))
            except SyntaxError as error:
                failures.append(f"invalid Python: {rel}: {error}")
        if path.suffix == ".md":
            for match in LINK.finditer(text):
                target = match.group(1).strip().strip("<>")
                if "://" in target or target.startswith(("#", "mailto:")):
                    continue
                local = unquote(target.split("#", 1)[0])
                if local and not (path.parent / local).exists():
                    failures.append(f"broken local link: {rel} -> {target}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--forbidden-patterns", type=Path,
                        help="external file of case-insensitive regexes, one per line; blank lines and # comments ignored")
    args = parser.parse_args()
    patterns = ()
    if args.forbidden_patterns:
        try:
            patterns = tuple(re.compile(line.strip(), re.I)
                             for line in args.forbidden_patterns.read_text().splitlines()
                             if line.strip() and not line.lstrip().startswith("#"))
        except (OSError, re.error) as error:
            print(f"FAIL: cannot load forbidden patterns: {error}")
            return 1
    failures = validate(args.root.resolve(), patterns)
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        return 1
    print(f"OK: {len(SKILL_NAMES)} skills; metadata, Python resources, and local links verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
