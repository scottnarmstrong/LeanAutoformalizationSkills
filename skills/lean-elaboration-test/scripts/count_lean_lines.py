#!/usr/bin/env python3
"""Size snapshot for a Lean 4 repo elaboration test.

Counts .lean files and lines at a git ref (stable snapshot — never the working
tree), excluding files that are entirely comments/whitespace. A line counts
as code if it contains at least one non-whitespace character outside comments
and string literals. Files that are not Lean modules (no `module` header;
`lakefile.lean` exempt) are counted and listed: every file must be a module.

Usage:  python3 count_lean_lines.py [REF] [PATH_PREFIX ...]
        REF defaults to HEAD. Optional prefixes restrict to e.g. 'Project'.

Run from the repo root.
"""
import re
import subprocess
import sys

MODULE_KEYWORD = re.compile(r"module(?![\w'.!?])")


def has_module_header(text):
    """True when `module` is the first token after `--` and (nested) `/- -/`
    comments; a `/--` doc comment or `/-!` module doc cannot precede it."""
    i, n = 0, len(text)
    while i < n:
        if text[i].isspace() or text[i] == "\ufeff":
            i += 1
        elif text.startswith("--", i):
            j = text.find("\n", i)
            i = n if j < 0 else j + 1
        elif text.startswith("/-", i) and not text.startswith(("/--", "/-!"), i):
            depth, i = 1, i + 2
            while i < n and depth:
                if text.startswith("/-", i):
                    depth, i = depth + 1, i + 2
                elif text.startswith("-/", i):
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
        else:
            return MODULE_KEYWORD.match(text, i) is not None
    return False


def code_line_flags(text):
    """Return per-line booleans: line has non-comment, non-string-aware code.

    Lexical scan tracking Lean line comments (--), nested block comments
    (/- -/ including doc comments), and string literals (so that '--' inside
    a string still counts the line as code, and comment openers inside
    strings are ignored).
    """
    lines = text.split("\n")
    flags = [False] * len(lines)
    ln = 0
    i = 0
    n = len(text)
    block_depth = 0
    in_line_comment = False
    in_string = False
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if c == "\n":
            ln += 1
            in_line_comment = False
            i += 1
            continue
        if in_line_comment:
            i += 1
            continue
        if block_depth:
            if two == "-/":
                block_depth -= 1
                i += 2
                continue
            if two == "/-":
                block_depth += 1
                i += 2
                continue
            i += 1
            continue
        if in_string:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_string = False
            flags[ln] = True
            i += 1
            continue
        # ordinary code context
        if two == "--":
            in_line_comment = True
            i += 2
            continue
        if two == "/-":
            block_depth += 1
            i += 2
            continue
        if text.startswith(("'\"'", "'\\\"'"), i):  # the character literal '"' or '\"'
            flags[ln] = True
            i += 3 if text[i + 1] == '"' else 4
            continue
        if c == '"':
            in_string = True
            flags[ln] = True
            i += 1
            continue
        if not c.isspace():
            flags[ln] = True
        i += 1
    return lines, flags


def main():
    ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    prefixes = tuple(sys.argv[2:])
    names = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    files = [f for f in names
             if f.endswith(".lean") and not f.startswith(".lake")
             and (not prefixes or f.startswith(prefixes))]

    total_lines = 0
    code_lines = 0
    counted = 0
    comment_only = []
    non_module = []
    for f in files:
        text = subprocess.run(
            ["git", "show", f"{ref}:{f}"],
            capture_output=True, text=True, check=True,
        ).stdout
        if f.rsplit("/", 1)[-1] != "lakefile.lean" and not has_module_header(text):
            non_module.append(f)
        lines, flags = code_line_flags(text)
        n_code = sum(flags)
        if n_code == 0:
            comment_only.append(f)
            continue
        counted += 1
        # split("\n") yields a trailing empty element for newline-terminated
        # files; count physical lines the way wc -l does
        total_lines += len(text.splitlines())
        code_lines += n_code

    print(f"ref:                            {ref}")
    if prefixes:
        print(f"prefixes:                       {' '.join(prefixes)}")
    print(f".lean files in tree:            {len(files)}")
    print(f"comment-only files (excluded):  {len(comment_only)}")
    print(f"counted files:                  {counted}")
    print(f"total lines (counted files):    {total_lines}")
    print(f"non-comment code lines:         {code_lines}")
    print(f"non-module files:               {len(non_module)}")
    if comment_only:
        print("\ncomment-only files:")
        for f in comment_only:
            print(f"  {f}")
    if non_module:
        print("\nnon-module files (must be ported):")
        for f in non_module:
            print(f"  {f}")


if __name__ == "__main__":
    main()
