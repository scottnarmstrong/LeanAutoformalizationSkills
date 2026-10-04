#!/usr/bin/env python3
"""Module-system checks and optional registry intake checks for a Lean 4 repository.

Run this checker only when the project's pinned toolchain and policy adopt the
module profile described in `references/module-system.md`. Registry-specific
checks activate when a `comparator.json` is present.

Every regular `.lean` file (tracked by git, so stage new files first; outside
a git checkout, every file outside `.git` and `.lake`) must:

- be a module: `module` is the first token after ordinary comments and blank
  lines (`lakefile.lean` is exempt);
- have at most 10,000 physical lines;
- not be a symbolic link.

Every `comparator.json` must name existing Challenge and Solution modules that
declare each of its `theorem_names`. Its `permitted_axioms` may only name the
standard three, and `enable_nanoda` must be true. The Challenge file has at
most 1,000 lines and 100 KiB; above 300 lines or 32 KiB is reported for review.

The helpers `has_module_header`, `code_mask`, `IMPORT`, `is_import_only` and
`declarations` are module-aware building blocks for a project's own checkers
(see `references/module-system.md`).

Usage: python3 check_lean_modules.py [--root DIR] [--files FILE ...] [--max-lines N]
Exit status: 0 PASS, 1 FAIL.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

MAX_LINES = 10_000
CHALLENGE_MAX_LINES, CHALLENGE_MAX_BYTES = 1_000, 100 * 1024
CHALLENGE_REVIEW_LINES, CHALLENGE_REVIEW_BYTES = 300, 32 * 1024
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}

# `import`, `public import`, `meta import`, `public meta import`, each optionally `all`.
IMPORT = re.compile(r"(?m)^[ \t]*(?:public[ \t]+)?(?:meta[ \t]+)?import[ \t]+(?:all[ \t]+)?(\S+)[ \t]*$")
MODULE_KEYWORD = re.compile(r"module(?![\w'.!?])")
CHAR_LITERAL = re.compile(r"'(?:\\.|[^\\'\n])'")
# Lines an import-only aggregator may contain besides imports.
SCAFFOLD_LINE = re.compile(
    r"[ \t]*(?:module|(?:public[ \t]+)?(?:meta[ \t]+)?import[ \t]+(?:all[ \t]+)?\S+|"
    r"namespace[ \t]+\S+|end(?:[ \t]+\S+)?|"
    r"(?:@\[[^\]\n]*\][ \t]*)*(?:(?:public|private|noncomputable)[ \t]+)*section(?:[ \t]+\S+)?|"
    r"open[ \t].*|set_option[ \t].*)?[ \t]*")
IDENT = r"(?:[A-Za-z_][A-Za-z0-9_'!?]*|«[^»\n]+»)"
NAME = rf"{IDENT}(?:\.{IDENT})*"
NAMESPACE = re.compile(rf"^[ \t]*namespace[ \t]+({NAME})")
SECTION = re.compile(
    rf"^[ \t]*(?:@\[[^\]\n]*\][ \t]*)*((?:(?:public|private|noncomputable)[ \t]+)*)section(?:[ \t]+{NAME})?[ \t]*$")
END = re.compile(rf"^[ \t]*end(?:[ \t]+{NAME})?[ \t]*$")
DECL = re.compile(
    r"^[ \t]*(?:(?:open|set_option)\b[^\n]*?\bin[ \t]+)*(?:@\[[^\]\n]*\][ \t]*)*"
    r"((?:(?:private|protected|public|meta|noncomputable|unsafe|partial|nonrec|scoped|local)[ \t]+)*)"
    r"(theorem|lemma|def|abbrev|opaque|structure|class|inductive|instance|axiom)\b"
    rf"(?:[ \t]+({NAME}))?")


def header_token_offset(text: str) -> int:
    """Offset of the first token after ordinary comments and whitespace.

    `--` line comments and (nested) `/- -/` block comments are skipped. A doc
    comment `/-- -/` or module doc `/-! -/` is a command and ends the scan: it
    cannot precede `module`.
    """
    index, size = 0, len(text)
    while index < size:
        if text[index].isspace() or text[index] == "﻿":
            index += 1
        elif text.startswith("--", index):
            newline = text.find("\n", index)
            index = size if newline < 0 else newline + 1
        elif text.startswith("/-", index) and not text.startswith(("/--", "/-!"), index):
            depth, index = 1, index + 2
            while index < size and depth:
                if text.startswith("/-", index):
                    depth, index = depth + 1, index + 2
                elif text.startswith("-/", index):
                    depth, index = depth - 1, index + 2
                else:
                    index += 1
        else:
            return index
    return size


def has_module_header(text: str) -> bool:
    return MODULE_KEYWORD.match(text, header_token_offset(text)) is not None


def code_mask(text: str) -> str:
    """Blank comments (including doc comments) and string literals, keeping offsets and newlines."""
    out = list(text)
    index, size = 0, len(text)

    def blank(start: int, end: int) -> None:
        for position in range(start, end):
            if out[position] != "\n":
                out[position] = " "

    while index < size:
        if text.startswith("--", index):
            end = text.find("\n", index)
            end = size if end < 0 else end
            blank(index, end)
            index = end
        elif text.startswith("/-", index):
            start, depth, index = index, 1, index + 2
            while index < size and depth:
                if text.startswith("/-", index):
                    depth, index = depth + 1, index + 2
                elif text.startswith("-/", index):
                    depth, index = depth - 1, index + 2
                else:
                    index += 1
            blank(start, index)
        elif (text[index] == "'" and CHAR_LITERAL.match(text, index)
              and not (index and (text[index - 1].isalnum() or text[index - 1] in "_'!?"))):
            index = CHAR_LITERAL.match(text, index).end()
        elif text[index] == '"':
            start, index = index, index + 1
            while index < size and text[index] != '"':
                index += 2 if text[index] == "\\" else 1
            index = min(index + 1, size)
            blank(start, index)
        else:
            index += 1
    return "".join(out)


def is_import_only(text: str) -> bool:
    """True for an aggregator: code is only the module header, imports and scope scaffolding."""
    lines = [line for line in code_mask(text).splitlines() if line.strip()]
    return (bool(lines) and all(SCAFFOLD_LINE.fullmatch(line) for line in lines)
            and any(IMPORT.match(line) for line in lines))


def qualified_name(namespaces: list[str], name: str) -> str:
    """The full name of `name` declared under `namespaces`; `_root_.X` names X."""
    if name.startswith("_root_."):
        return name[len("_root_."):]
    return ".".join([*namespaces, name])


def declarations(text: str) -> list[tuple[str, str, bool]]:
    """(kind, full name, exported) for each named top-level declaration, lexically.

    In a module a declaration is exported when it is marked `public`, or lies in
    a `public section` and is not `private`. In a non-module file every
    non-`private` declaration is exported.
    """
    module = has_module_header(text)
    namespaces: list[str] = []
    scopes: list[tuple[int, str | None]] = []  # (namespace parts, section visibility)
    found: list[tuple[str, str, bool]] = []
    for line in code_mask(text).splitlines():
        if match := NAMESPACE.match(line):
            parts = match.group(1).split(".")
            namespaces.extend(parts)
            scopes.append((len(parts), None))
        elif match := SECTION.match(line):
            words = match.group(1).split()
            scopes.append((0, "public" if "public" in words else "private" if "private" in words else None))
        elif END.match(line):
            if scopes:
                count, _visibility = scopes.pop()
                if count:
                    del namespaces[-count:]
        elif match := DECL.match(line):
            modifiers, kind, name = match.group(1).split(), match.group(2), match.group(3)
            if name is None:
                continue
            default = next((v for _c, v in reversed(scopes) if v is not None),
                           "private" if module else "public")
            exported = "private" not in modifiers and ("public" in modifiers or default == "public")
            found.append((kind, qualified_name(namespaces, name), exported))
    return found


def lean_files(root: Path) -> list[Path]:
    try:
        listed = subprocess.run(["git", "ls-files", "-z", "--", "*.lean"], cwd=root,
                                capture_output=True, check=True).stdout.decode().split("\0")
        return [root / name for name in listed if name]
    except (OSError, subprocess.CalledProcessError):
        found: list[Path] = []
        for directory, subdirs, names in os.walk(root):
            subdirs[:] = [d for d in subdirs if d not in {".git", ".lake"}]
            found.extend(Path(directory) / n for n in names if n.endswith(".lean"))
        return sorted(found)


def comparator_configs(root: Path) -> list[Path]:
    try:
        listed = subprocess.run(["git", "ls-files", "-z", "--", "*comparator.json"], cwd=root,
                                capture_output=True, check=True).stdout.decode().split("\0")
        return [root / name for name in listed if name and Path(name).name == "comparator.json"]
    except (OSError, subprocess.CalledProcessError):
        found: list[Path] = []
        for directory, subdirs, names in os.walk(root):
            subdirs[:] = [d for d in subdirs if d not in {".git", ".lake"}]
            found.extend(Path(directory) / n for n in names if n == "comparator.json")
        return sorted(found)


def check_file(root: Path, path: Path, max_lines: int, errors: list[str]) -> None:
    rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
    if path.is_symlink():
        errors.append(f"{rel}: symlinked .lean file")
        return
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"{rel}: unreadable: {exc}")
        return
    if path.name != "lakefile.lean" and not has_module_header(text):
        errors.append(f"{rel}: not a module (the first token after comments must be `module`)")
    lines = len(text.splitlines())
    if lines > max_lines:
        errors.append(f"{rel}: {lines} lines exceeds {max_lines}")


def check_comparator(root: Path, config: Path, errors: list[str], warnings: list[str]) -> None:
    rel = config.relative_to(root).as_posix()
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{rel}: unreadable: {exc}")
        return
    if not isinstance(data, dict):
        errors.append(f"{rel}: expected a JSON object")
        return
    names = data.get("theorem_names")
    if not isinstance(names, list) or not names or not all(isinstance(n, str) for n in names):
        errors.append(f"{rel}: theorem_names must be a nonempty list of names")
        names = []
    axioms = data.get("permitted_axioms")
    if not isinstance(axioms, list) or not set(axioms) <= STANDARD_AXIOMS:
        errors.append(f"{rel}: permitted_axioms must name only {sorted(STANDARD_AXIOMS)}")
    if data.get("enable_nanoda") is not True:
        errors.append(f"{rel}: enable_nanoda must be true")
    for key in ("challenge_module", "solution_module"):
        module = data.get(key)
        if not isinstance(module, str) or not module:
            errors.append(f"{rel}: {key} missing")
            continue
        path = root / (module.replace(".", "/") + ".lean")
        if not path.is_file():
            errors.append(f"{rel}: {key} {module} has no file {path.relative_to(root).as_posix()}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{rel}: {key} {module} unreadable: {exc}")
            continue
        declared = {name for kind, name, exported in declarations(text)
                    if exported and kind in {"theorem", "lemma"}}
        for name in names:
            if name not in declared:
                errors.append(f"{rel}: {key} {module} does not declare public theorem {name}")
        if key == "challenge_module":
            lines, size = len(text.splitlines()), len(text.encode("utf-8"))
            if lines > CHALLENGE_MAX_LINES or size > CHALLENGE_MAX_BYTES:
                errors.append(f"{rel}: Challenge has {lines} lines and {size} bytes "
                              f"(limit {CHALLENGE_MAX_LINES} lines, {CHALLENGE_MAX_BYTES} bytes)")
            elif lines > CHALLENGE_REVIEW_LINES or size > CHALLENGE_REVIEW_BYTES:
                warnings.append(f"{rel}: Challenge has {lines} lines and {size} bytes "
                                f"(review threshold {CHALLENGE_REVIEW_LINES} lines, {CHALLENGE_REVIEW_BYTES} bytes)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--files", nargs="+", type=Path, help="check only these .lean files (no comparator checks)")
    parser.add_argument("--max-lines", type=int, default=MAX_LINES)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    files = ([Path(os.path.abspath(root / f)) for f in args.files] if args.files else lean_files(root))
    errors: list[str] = []
    warnings: list[str] = []
    for path in files:
        check_file(root, path, args.max_lines, errors)
    configs = [] if args.files else comparator_configs(root)
    for config in configs:
        check_comparator(root, config, errors, warnings)
    for warning in warnings:
        print(f"warning: {warning}")
    summary = f"{len(files)} Lean files, {len(configs)} comparator configurations"
    if errors:
        print(f"check_lean_modules: FAIL ({summary})")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"check_lean_modules: PASS ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
