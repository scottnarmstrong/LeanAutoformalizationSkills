#!/usr/bin/env python3
"""Fail-closed local checker for an author-approved frozen-anchor manifest.

This tool verifies supplied baselines only.  It deliberately has no update,
accept, or rebaseline command: an author-approved successor is external work.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

HEX = re.compile(r"^[0-9a-f]{64}$")
FQ = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+$")
MARKERS = ("FROZEN_ANCHOR_PREFIX_BEGIN", "FROZEN_ANCHOR_PROOF_BEGIN",
           "FROZEN_ANCHOR_PROOF_END", "FROZEN_ANCHOR_SUFFIX_BEGIN",
           "FROZEN_ANCHOR_SUFFIX_END")
# Module-system imports: `public`, `meta` and `all` qualifiers are accepted.
IMPORT = re.compile(r"(?m)^\s*(?:public\s+)?(?:meta\s+)?import\s+(?:all\s+)?([A-Za-z_][A-Za-z0-9_.]*)\s*$")
DECL = re.compile(
    r"(?m)^[ \t]*(?:@\[[^\]\n]*\][ \t]*)*"
    r"((?:(?:private|protected|public|noncomputable|unsafe|partial|nonrec|meta)\s+)*)"
    r"(theorem|lemma|def|abbrev|opaque|structure|class|inductive|axiom|constant|instance|example)\b"
    r"(?:\s+([A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*))?"
)
NAMESPACE = re.compile(r"^[ \t]*namespace\s+([A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)\b")
SECTION = re.compile(
    r"^[ \t]*(?:@\[[^\]\n]*\][ \t]*)*((?:(?:public|private|noncomputable)\s+)*)"
    r"section(?:\s+[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)?[ \t]*$")
END = re.compile(r"^[ \t]*end(?:\s+[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)?[ \t]*$")
PLACEHOLDER = re.compile(r"\b(?:sorry|admit)\b")
MODULE_KEYWORD = re.compile(r"module(?![\w'.!?])")


def has_module_header(text: str) -> bool:
    """True when `module` is the first token after `--` and (nested) `/- -/` comments.

    A doc comment `/-- -/` or module doc `/-! -/` is a command: it cannot
    precede `module`.
    """
    index, size = 0, len(text)
    while index < size:
        if text[index].isspace() or text[index] == "\ufeff":
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
            return MODULE_KEYWORD.match(text, index) is not None
    return False


class Guard:
    def __init__(self, root: Path, allow_non_module: bool = False) -> None:
        self.root = root.resolve()
        self.allow_non_module = allow_non_module
        self.errors: list[str] = []
        self.allowed_sorry: dict[Path, set[tuple[int, int]]] = {}

    def fail(self, message: str) -> None:
        self.errors.append(message)

    @staticmethod
    def digest(data: str | bytes) -> str:
        raw = data.encode("utf-8") if isinstance(data, str) else data
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def read_utf8(path: Path) -> str:
        """Decode UTF-8 without universal-newline normalization."""
        return path.read_bytes().decode("utf-8")

    @staticmethod
    def code_mask(text: str) -> str:
        """Blank comments and strings while retaining offsets/newlines.

        This is deliberately a lexer-sized defense, not a Lean parser.  It
        handles nested block comments, line comments, ordinary/triple strings,
        escapes, and ordinary character literals well enough for quarantine
        token checks without treating prose as executable Lean.
        """
        out = list(text)

        def blank(start: int, end: int) -> None:
            for index in range(start, end):
                if out[index] != "\n":
                    out[index] = " "

        index, size = 0, len(text)
        while index < size:
            if text.startswith("--", index):
                end = text.find("\n", index)
                end = size if end == -1 else end
                blank(index, end)
                index = end
            elif text.startswith("/-", index):
                start, depth = index, 1
                index += 2
                while index < size and depth:
                    if text.startswith("/-", index):
                        depth, index = depth + 1, index + 2
                    elif text.startswith("-/", index):
                        depth, index = depth - 1, index + 2
                    else:
                        index += 1
                blank(start, index)
            elif text.startswith('"""', index):
                start = index
                end = text.find('"""', index + 3)
                index = size if end == -1 else end + 3
                blank(start, index)
            elif text[index] == '"':
                start, index = index, index + 1
                while index < size:
                    if text[index] == "\\":
                        index += 2
                    elif text[index] == '"':
                        index += 1
                        break
                    else:
                        index += 1
                blank(start, min(index, size))
            elif text[index] == "'" and (index == 0 or not (text[index - 1].isalnum() or text[index - 1] in "_'")):
                start, index = index, index + 1
                while index < size:
                    if text[index] == "\\":
                        index += 2
                    elif text[index] == "'":
                        index += 1
                        break
                    else:
                        index += 1
                blank(start, min(index, size))
            else:
                index += 1
        return "".join(out)

    def project_files(self) -> list[Path]:
        return [path for path in self.root.rglob("*.lean")
                if ".lake" not in path.parts and ".git" not in path.parts]

    def declarations(self, text: str) -> list[tuple[str | None, str, str | None, str | None]]:
        """Lexically resolve common declaration commands under simple namespaces.

        In a module a declaration is private unless it is marked `public` or
        lies in a `public section`; such a declaration is reported as
        `private`. `_root_.X` names X.
        """
        module = has_module_header(text)
        namespaces: list[str] = []
        blocks: list[tuple[str, int, str | None]] = []
        found: list[tuple[str | None, str, str | None, str | None]] = []
        for line in self.code_mask(text).splitlines():
            namespace = NAMESPACE.match(line)
            if namespace:
                parts = namespace.group(1).split(".")
                namespaces.extend(parts)
                blocks.append(("namespace", len(parts), None))
                continue
            section = SECTION.match(line)
            if section:
                words = section.group(1).split()
                visibility = "public" if "public" in words else "private" if "private" in words else None
                blocks.append(("section", 0, visibility))
                continue
            if END.match(line):
                if blocks:
                    block, count, _visibility = blocks.pop()
                    if block == "namespace" and count:
                        del namespaces[-count:]
                continue
            for declaration in DECL.finditer(line):
                modifiers, kind, name = declaration.groups()
                words = modifiers.split()
                default = next((visibility for _block, _count, visibility in reversed(blocks)
                                if visibility is not None), "private" if module else "public")
                private = "private" in words or ("public" not in words and default == "private")
                modifier = "private" if private else "protected" if "protected" in words else None
                if name is None:
                    fq_name = None
                elif name.startswith("_root_."):
                    fq_name = name[len("_root_."):]
                else:
                    fq_name = ".".join([*namespaces, *name.split(".")])
                found.append((modifier, kind, name, fq_name))
        return found

    def path(self, value: Any, label: str) -> Path | None:
        if not isinstance(value, str) or not value.endswith(".lean"):
            self.fail(f"{label}: must be a relative .lean path")
            return None
        candidate = (self.root / value).resolve()
        if self.root not in candidate.parents or candidate == self.root:
            self.fail(f"{label}: path escapes --root")
            return None
        if not candidate.is_file():
            self.fail(f"{label}: missing file {value}")
            return None
        return candidate

    def hash(self, value: Any, label: str) -> bool:
        if not isinstance(value, str) or not HEX.fullmatch(value):
            self.fail(f"{label}: expected 64 lowercase hexadecimal characters")
            return False
        return True

    def check(self, data: Any) -> None:
        if not isinstance(data, dict):
            self.fail("manifest: expected JSON object")
            return
        if set(data) != {"schema_version", "manifest_state", "seal_limits", "anchors"}:
            self.fail("manifest: schema has missing or unauthorized top-level fields")
        if data.get("schema_version") != 1:
            self.fail("manifest: unsupported or missing schema_version (only 1 is authorized)")
        if data.get("manifest_state") != "AUTHOR_APPROVED":
            self.fail("manifest: state must be AUTHOR_APPROVED")
        limits = data.get("seal_limits")
        if (not isinstance(limits, dict) or set(limits) != {"max_body_lines", "max_body_bytes"}
                or not isinstance(limits.get("max_body_lines"), int)
                or not isinstance(limits.get("max_body_bytes"), int)
                or limits["max_body_lines"] < 1 or limits["max_body_bytes"] < 1):
            self.fail("manifest: seal_limits must have positive max_body_lines and max_body_bytes")
            limits = {"max_body_lines": 1, "max_body_bytes": 1}
        anchors = data.get("anchors")
        if not isinstance(anchors, list) or not anchors:
            self.fail("manifest: anchors must be a nonempty array")
            return
        paths: set[str] = set()
        exports: set[str] = set()
        ids: set[str] = set()
        modules: dict[str, Path] = {}
        parsed: list[tuple[dict[str, Any], Path, Path | None]] = []
        for number, item in enumerate(anchors):
            if not isinstance(item, dict):
                self.fail(f"anchor[{number}]: expected object")
                continue
            path = self.check_entry(item, number, paths, exports, ids, limits)
            if path is None:
                continue
            modules[self.module_name(path)] = path
            implementation = None
            if item.get("kind") == "theorem":
                implementation = self.implementation_path(item, number)
                if implementation is not None:
                    modules[item["implementation"]["module"]] = implementation
            parsed.append((item, path, implementation))
        self.check_split_groups(anchors)
        self.check_import_graph(modules, parsed)
        self.check_draft_quarantine(parsed)
        self.check_all_sorries()
        self.check_forbidden_axioms_constants()

    def check_entry(self, anchor: dict[str, Any], number: int, paths: set[str],
                    exports: set[str], ids: set[str], limits: dict[str, int]) -> Path | None:
        label, kind, state = f"anchor[{number}]", anchor.get("kind"), anchor.get("state")
        if not isinstance(anchor.get("id"), str) or not anchor["id"]:
            self.fail(f"{label}.id: required nonempty string")
        elif anchor["id"] in ids:
            self.fail(f"{label}.id: duplicate anchor ID {anchor['id']}")
        else:
            ids.add(anchor["id"])
        if kind not in ("theorem", "definition"):
            self.fail(f"{label}.kind: must be theorem or definition")
        if state not in ("DRAFT_SORRY", "SEALED"):
            self.fail(f"{label}.state: must be DRAFT_SORRY or SEALED")
        common = {"id", "kind", "author_approval", "source", "contract", "path", "export",
                  "abi_sha256", "definition_closure", "state", "split_policy"}
        expected = (common | {"implementation", "prefix_sha256", "suffix_sha256", "draft_allowlist"}
                    if kind == "theorem" else common | {"full_file_sha256"})
        if set(anchor) != expected:
            self.fail(f"{label}: schema has missing or unauthorized fields")
        if kind == "definition" and state != "SEALED":
            self.fail(f"{label}: definition anchors must be SEALED whole-file anchors")
        for group, keys in (("author_approval", ("approved_by", "approved_at", "approval_ref", "approval_version")),
                            ("source", ("revision", "range")), ("contract", ("id", "version"))):
            value = anchor.get(group)
            if (not isinstance(value, dict) or set(value) != set(keys)
                    or any(not isinstance(value.get(key), str) or not value[key] for key in keys)):
                self.fail(f"{label}.{group}: missing or unauthorized approval/provenance fields")
        path_value, export = anchor.get("path"), anchor.get("export")
        if isinstance(path_value, str) and path_value in paths:
            self.fail(f"{label}.path: duplicate {path_value}")
        elif isinstance(path_value, str):
            paths.add(path_value)
        if not isinstance(export, str) or not FQ.fullmatch(export):
            self.fail(f"{label}.export: expected fully-qualified export")
        elif export in exports:
            self.fail(f"{label}.export: duplicate {export}")
        else:
            exports.add(export)
        self.hash(anchor.get("abi_sha256"), f"{label}.abi_sha256")
        self.check_split_policy(anchor.get("split_policy"), f"{label}.split_policy")
        self.check_definition_closure(anchor, label)
        path = self.path(path_value, f"{label}.path")
        if path is None:
            return None
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        if not self.allow_non_module and not has_module_header(text):
            self.fail(f"{label}: frozen file is not a module (the first token after comments must be `module`)")
        if kind == "definition":
            self.hash(anchor.get("full_file_sha256"), f"{label}.full_file_sha256")
            if self.digest(raw) != anchor.get("full_file_sha256"):
                self.fail(f"{label}: whole-file definition anchor hash drift")
            self.check_declaration(anchor, label, text, "definition")
            return path
        self.check_allowlist(anchor, label)
        bounds = self.check_theorem_region(anchor, label, text, limits)
        self.check_declaration(anchor, label, text, "theorem")
        implementation = anchor.get("implementation")
        if bounds is not None and isinstance(implementation, dict) and isinstance(implementation.get("module"), str):
            prefix = text[:bounds[0]]
            if implementation["module"] not in self.imports_text(prefix):
                self.fail(f"{label}: frozen prefix does not import declared implementation.module")
        return path

    def check_split_policy(self, policy: Any, label: str) -> None:
        keys = {"source_group", "mode", "ruling_ref"}
        if not isinstance(policy, dict) or set(policy) != keys:
            self.fail(f"{label}: require exactly source_group, mode, and ruling_ref")
            return
        if not isinstance(policy.get("source_group"), str) or not policy["source_group"]:
            self.fail(f"{label}.source_group: required nonempty string")
        if policy.get("mode") not in {"NOT_SPLIT", "INDEPENDENT_BY_AUTHOR"}:
            self.fail(f"{label}.mode: must be NOT_SPLIT or INDEPENDENT_BY_AUTHOR")
        if not isinstance(policy.get("ruling_ref"), str) or not policy["ruling_ref"]:
            self.fail(f"{label}.ruling_ref: required nonempty author ruling reference")

    def check_split_groups(self, anchors: list[Any]) -> None:
        groups: dict[str, list[dict[str, Any]]] = {}
        for anchor in anchors:
            if not isinstance(anchor, dict) or not isinstance(anchor.get("split_policy"), dict):
                continue
            policy = anchor["split_policy"]
            group = policy.get("source_group")
            if isinstance(group, str) and group:
                groups.setdefault(group, []).append(policy)
        for group, policies in groups.items():
            mode_values = [policy.get("mode") for policy in policies]
            ruling_values = [policy.get("ruling_ref") for policy in policies]
            if not all(isinstance(mode, str) for mode in mode_values):
                self.fail(f"split_policy source_group {group}: every mode must be a string")
                continue
            if not all(isinstance(ruling, str) and ruling for ruling in ruling_values):
                self.fail(f"split_policy source_group {group}: all entries must cite the same nonempty ruling_ref")
                continue
            modes, rulings = set(mode_values), set(ruling_values)
            if len(modes) != 1:
                self.fail(f"split_policy source_group {group}: all entries must use the same mode")
                continue
            if len(rulings) != 1:
                self.fail(f"split_policy source_group {group}: all entries must cite the same nonempty ruling_ref")
            mode = next(iter(modes))
            if mode == "INDEPENDENT_BY_AUTHOR" and len(policies) < 2:
                self.fail(f"split_policy source_group {group}: INDEPENDENT_BY_AUTHOR requires at least two entries")
            if mode == "NOT_SPLIT" and len(policies) != 1:
                self.fail(f"split_policy source_group {group}: NOT_SPLIT requires one joint constitutional anchor")

    def check_definition_closure(self, anchor: dict[str, Any], label: str) -> None:
        closure = anchor.get("definition_closure")
        if not isinstance(closure, list):
            self.fail(f"{label}.definition_closure: expected array")
            return
        paths: set[str] = set()
        for index, entry in enumerate(closure):
            entry_label = f"{label}.definition_closure[{index}]"
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"} or not isinstance(entry.get("path"), str):
                self.fail(f"{entry_label}: expected exactly path and sha256")
                continue
            if entry["path"] in paths:
                self.fail(f"{entry_label}: duplicate path")
            paths.add(entry["path"])
            path = self.path(entry["path"], f"{entry_label}.path")
            if self.hash(entry.get("sha256"), f"{entry_label}.sha256") and path:
                if self.digest(path.read_bytes()) != entry["sha256"]:
                    self.fail(f"{entry_label}: semantic definition hash drift")

    def check_allowlist(self, anchor: dict[str, Any], label: str) -> None:
        allow = anchor.get("draft_allowlist")
        if not isinstance(allow, dict) or set(allow) != {"frozen_paths", "audit_paths"}:
            self.fail(f"{label}.draft_allowlist: require exactly frozen_paths and audit_paths")
            return
        for field, marker in (("frozen_paths", "Frozen"), ("audit_paths", "Audit")):
            values = allow[field]
            if (not isinstance(values, list) or not all(isinstance(value, str) for value in values)
                    or len(values) != len(set(values))):
                self.fail(f"{label}.draft_allowlist.{field}: expected unique path array")
                continue
            for value in values:
                path = self.path(value, f"{label}.draft_allowlist.{field}")
                if path and marker not in path.parts:
                    self.fail(f"{label}.draft_allowlist.{field}: {value} is not an explicit {marker} location")

    def check_theorem_region(self, anchor: dict[str, Any], label: str, text: str,
                             limits: dict[str, int]) -> tuple[int, int] | None:
        positions = []
        for marker in MARKERS:
            found = [match.start() for match in re.finditer(re.escape(marker), text)]
            if len(found) != 1:
                self.fail(f"{label}: marker {marker} must occur exactly once")
                return None
            positions.append(found[0])
        if positions != sorted(positions):
            self.fail(f"{label}: proof-region markers are out of order")
            return None
        body_start = text.index("\n", positions[1]) + 1
        body_end = text.rfind("\n", 0, positions[2]) + 1
        # These two regions cover every byte except the mutable proof body.
        prefix, suffix, body = text[:body_start], text[body_end:], text[body_start:body_end]
        if self.hash(anchor.get("prefix_sha256"), f"{label}.prefix_sha256") and self.digest(prefix) != anchor["prefix_sha256"]:
            self.fail(f"{label}: frozen prefix hash drift (all bytes before proof body changed)")
        if self.hash(anchor.get("suffix_sha256"), f"{label}.suffix_sha256") and self.digest(suffix) != anchor["suffix_sha256"]:
            self.fail(f"{label}: frozen suffix hash drift (all bytes after proof body changed)")
        if anchor.get("state") == "DRAFT_SORRY":
            match = re.fullmatch(r"\s*by\s+(?P<sorry>sorry)\s*", body)
            if match is None:
                self.fail(f"{label}: DRAFT_SORRY body must be exactly the single authorized `by sorry`")
            else:
                path_value = anchor.get("path")
                if isinstance(path_value, str):
                    self.allowed_sorry.setdefault((self.root / path_value).resolve(), set()).add(
                        (body_start + match.start("sorry"), body_start + match.end("sorry")))
        else:
            implementation = anchor.get("implementation")
            export = implementation.get("export") if isinstance(implementation, dict) else None
            escaped = re.escape(export) if isinstance(export, str) else r"(?!)"
            if not re.fullmatch(r"\s*by\s+(?:exact\s+|simpa\s+using\s+)" + escaped + r"\s*", body):
                self.fail(f"{label}: SEALED body must be trivial assembly of exactly implementation.export")
            lines = 0 if not body.strip() else body.strip().count("\n") + 1
            if lines > limits["max_body_lines"] or len(body.encode("utf-8")) > limits["max_body_bytes"]:
                self.fail(f"{label}: SEALED body exceeds configured short assembly limits")
        return body_start, body_end

    def check_declaration(self, anchor: dict[str, Any], label: str, text: str, kind: str) -> None:
        declarations = self.declarations(text)
        expected_export = anchor.get("export", "")
        expected_kind = "def" if kind == "definition" else None
        if len(declarations) != 1:
            self.fail(f"{label}: frozen file must contain exactly one top-level declaration total")
            return
        modifier, actual_kind, actual_name, actual_export = declarations[0]
        if modifier == "private":
            self.fail(f"{label}: frozen declaration cannot be private "
                      "(in a module, declare it in a `public section` or mark it `public`)")
        if actual_name is None:
            self.fail(f"{label}: frozen declaration must have a named export")
            return
        if actual_export != expected_export:
            self.fail(f"{label}: lexically resolved declaration name does not match fully qualified export")
        if expected_kind and actual_kind != expected_kind:
            self.fail(f"{label}: definition anchor must use literal `def`")
        if kind == "theorem" and actual_kind not in {"theorem", "lemma"}:
            self.fail(f"{label}: theorem anchor must declare theorem or lemma")

    def implementation_path(self, anchor: dict[str, Any], number: int) -> Path | None:
        label, value = f"anchor[{number}].implementation", anchor.get("implementation")
        if not isinstance(value, dict) or set(value) != {"module", "export"}:
            self.fail(f"{label}: require exactly module and export")
            return None
        module, export = value["module"], value["export"]
        if not isinstance(module, str) or not FQ.fullmatch(module):
            self.fail(f"{label}.module: expected fully-qualified module")
            return None
        if not isinstance(export, str) or not FQ.fullmatch(export):
            self.fail(f"{label}.export: expected fully-qualified export")
        path = self.path(module.replace(".", "/") + ".lean", f"{label}.module")
        if path is not None and anchor.get("state") == "SEALED" and isinstance(export, str):
            declarations = self.declarations(self.read_utf8(path))
            matches = [declaration for declaration in declarations
                       if declaration[0] != "private" and declaration[3] == export]
            if len(matches) != 1:
                self.fail(f"{label}.export: SEALED implementation export is not declared exactly once in implementation.module")
        return path

    def module_name(self, path: Path) -> str:
        return ".".join(path.relative_to(self.root).with_suffix("").parts)

    def imports_text(self, text: str) -> set[str]:
        return set(IMPORT.findall(self.code_mask(text)))

    def imports(self, path: Path) -> set[str]:
        return self.imports_text(self.read_utf8(path))

    def project_module_graph(self) -> tuple[dict[str, Path], dict[str, set[str]]]:
        modules = {self.module_name(path): path for path in self.project_files()}
        return modules, {module: {imp for imp in self.imports(path) if imp in modules}
                         for module, path in modules.items()}

    def check_import_graph(self, modules: dict[str, Path], parsed: list[tuple[dict[str, Any], Path, Path | None]]) -> None:
        project_modules, graph = self.project_module_graph()
        modules = {**project_modules, **modules}
        definition_paths = {str(path.relative_to(self.root)) for anchor, path, _ in parsed
                            if anchor.get("kind") == "definition"}
        for anchor, frozen, implementation in parsed:
            if anchor.get("kind") == "theorem" and implementation is not None:
                target, start = self.module_name(frozen), anchor["implementation"]["module"]
                todo, seen = [start], set()
                while todo:
                    current = todo.pop()
                    if current in seen:
                        continue
                    seen.add(current)
                    if current == target:
                        self.fail(f"{anchor['id']}: implementation module reverse-imports frozen anchor")
                        break
                    todo.extend(graph.get(current, ()))
            for entry in anchor.get("definition_closure", []):
                if isinstance(entry, dict) and entry.get("path") not in definition_paths:
                    self.fail(f"{anchor['id']}: definition_closure path is not a manifest definition anchor")

    def check_draft_quarantine(self, parsed: list[tuple[dict[str, Any], Path, Path | None]]) -> None:
        files = self.project_files()
        modules, graph = self.project_module_graph()
        for anchor, frozen, implementation in parsed:
            if anchor.get("kind") != "theorem" or anchor.get("state") != "DRAFT_SORRY":
                continue
            allow, approved = anchor.get("draft_allowlist", {}), {frozen.resolve()}
            if isinstance(allow, dict):
                for values in allow.values():
                    if isinstance(values, list):
                        approved.update((self.root / value).resolve() for value in values if isinstance(value, str))
            module, export = self.module_name(frozen), anchor.get("export", "")
            token = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(export) + r"(?![A-Za-z0-9_.])")
            implementation_data = anchor.get("implementation", {})
            provider_module = implementation_data.get("module", "")
            provider_export = implementation_data.get("export", "")
            provider_token = re.compile(
                r"(?<![A-Za-z0-9_.])" + re.escape(provider_export) + r"(?![A-Za-z0-9_.])")
            provider_approved = {frozen.resolve()}
            if implementation is not None:
                provider_approved.add(implementation.resolve())
            for path in files:
                resolved = path.resolve()
                code = self.code_mask(self.read_utf8(path))
                reachable: set[str] = set()
                todo = [self.module_name(path)]
                while todo:
                    current = todo.pop()
                    if current in reachable:
                        continue
                    reachable.add(current)
                    todo.extend(graph.get(current, ()))
                if resolved not in approved:
                    if module in reachable:
                        self.fail(f"{anchor['id']}: DRAFT_SORRY imported directly or transitively outside explicit frozen/audit allowlist: {path.relative_to(self.root)}")
                    if token.search(code):
                        self.fail(f"{anchor['id']}: DRAFT_SORRY used outside explicit frozen/audit allowlist: {path.relative_to(self.root)}")
                if resolved not in provider_approved:
                    if provider_module in reachable:
                        self.fail(f"{anchor['id']}: DRAFT provider imported directly or transitively outside its provider and frozen anchor: {path.relative_to(self.root)}")
                    if provider_token.search(code):
                        self.fail(f"{anchor['id']}: DRAFT provider export used outside its provider and frozen anchor: {path.relative_to(self.root)}")

    def check_all_sorries(self) -> None:
        for path in self.project_files():
            code = self.code_mask(self.read_utf8(path))
            allowed = self.allowed_sorry.get(path.resolve(), set())
            for match in PLACEHOLDER.finditer(code):
                authorized = match.group() == "sorry" and (match.start(), match.end()) in allowed
                if not authorized:
                    self.fail(f"unauthorized `{match.group()}` outside manifest-listed DRAFT proof region: {path.relative_to(self.root)}")

    def check_forbidden_axioms_constants(self) -> None:
        for path in self.project_files():
            for _modifier, kind, name, _export in self.declarations(self.read_utf8(path)):
                if kind in {"axiom", "constant"}:
                    label = name or "<anonymous>"
                    self.fail(f"project-owned `{kind}` command is forbidden: {path.relative_to(self.root)}:{label}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--allow-non-module", action="store_true",
                        help="accept non-module frozen files; only for a legacy repository awaiting its module port")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FROZEN-ANCHOR GUARD FAILED: cannot read manifest: {exc}", file=sys.stderr)
        return 2
    guard = Guard(args.root, allow_non_module=args.allow_non_module)
    guard.check(data)
    if guard.errors:
        print("FROZEN-ANCHOR GUARD FAILED:", file=sys.stderr)
        for error in guard.errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("FROZEN-ANCHOR GUARD OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
