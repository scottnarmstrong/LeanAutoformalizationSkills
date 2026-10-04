#!/usr/bin/env python3
"""Validate and render a source-level mathematical proof dependency graph.

This intentionally checks records and topology only.  In particular, Lean
references are opaque planning metadata: this program never reads Lean files
and cannot establish mathematical truth or extraction completeness.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Iterable, Sequence


BEGIN = "<!-- BEGIN PROOF DEPGRAPH GENERATED -->"
END = "<!-- END PROOF DEPGRAPH GENERATED -->"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:#/-]*$")
LOCATOR_RE = re.compile(
    r"^(?P<path>[^#]+)#(?P<anchor>[^@\s]+)@L(?P<first>[1-9]\d*)-L(?P<last>[1-9]\d*)$"
)
EXTERNAL_LOCATOR_RE = re.compile(r"^external:[^#\s]+#[^\s]+$")
FIELD_RE = re.compile(r"^([A-Z][A-Z0-9_]*):[ \t]*(.*)$")

GRAPH_FIELDS = ("GRAPH_VERSION", "ROOTS", "CORPUS", "CONVENTIONS", "STANDING_ASSUMPTIONS", "EXTERNAL_POLICY", "FROZEN_ANCHORS", "FROZEN_MANIFEST", "WRITER", "GLOBAL_REVIEWER", "GLOBAL_REVIEW_REF")
NODE_FIELDS = (
    "KIND", "TITLE", "STATEMENT_SOURCE", "PROOF_SOURCE", "CONTRACT_ID",
    "CONTRACT_VERSION", "SOURCE_HYPOTHESES", "SOURCE_QUANTIFIERS",
    "SOURCE_CONCLUSION", "CONSTANT_SCOPE", "FROZEN_FILE", "FROZEN_DECL",
    "FROZEN_ANCHOR_ID", "FROZEN_ABI_SHA256",
    "DEPS", "ROUTES", "ROUTE_FOR", "TOPOLOGY_STATUS",
    "EXTRACTOR", "REVIEWER", "LEAN_STATUS", "LEAN_REF", "LEAN_NOTE", "NOTE",
)
AMEND_FIELDS = (
    "TARGET", "AUTHOR", "REVIEWER", "ADD_DEPS", "DROP_DEPS", "ADD_ROUTES",
    "DROP_ROUTES", "SET_TITLE", "SET_STATEMENT_SOURCE", "SET_PROOF_SOURCE",
    "SET_CONTRACT_ID", "SET_CONTRACT_VERSION", "SET_SOURCE_HYPOTHESES",
    "SET_SOURCE_QUANTIFIERS", "SET_SOURCE_CONCLUSION", "SET_CONSTANT_SCOPE",
    "SET_ROUTE_FOR", "NOTE",
)
MANIFEST_FIELDS = ("KIND", "SOURCE", "DISPOSITION", "REASON", "COVERAGE_STATUS", "EXTRACTOR", "REVIEWER")
KINDS = frozenset({"theorem", "proposition", "lemma", "corollary", "claim", "definition", "display", "step", "application", "route", "external", "assumption"})
FROZEN_ANCHOR_KINDS = KINDS.difference({"route", "step", "application", "assumption", "external"})
TOPOLOGY_STATUSES = frozenset({"PROPOSED", "REVIEWED", "DISPUTED"})
MANIFEST_KINDS = frozenset({"theorem", "proposition", "lemma", "corollary", "claim", "definition", "display", "assumption", "external", "heading", "citation", "proof-region"})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
LEAN_DECL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_'.]*$")
FROZEN_MANIFEST_RE = re.compile(r"^(?P<path>[^|\s][^|]*?)\s*\|\s*sha256:(?P<hash>[0-9a-f]{64})$")


@dataclass(frozen=True)
class Diagnostic:
    path: str
    line: int
    message: str

    def render(self) -> str:
        where = f"{self.path}:{self.line}" if self.line else self.path
        return f"{where}: {self.message}"


class Diagnostics:
    def __init__(self) -> None:
        self.items: list[Diagnostic] = []
        self._seen: set[tuple[str, int, str]] = set()

    def add(self, path: str, line: int, message: str) -> None:
        key = (path, line, message)
        if key not in self._seen:
            self._seen.add(key)
            self.items.append(Diagnostic(path, line, message))

    def extend(self, values: Iterable[Diagnostic]) -> None:
        for value in values:
            self.add(value.path, value.line, value.message)


@dataclass
class Edge:
    target: str
    source: str
    rationale: str
    line: int


@dataclass
class Node:
    node_id: str
    line: int
    fields: dict[str, str] = field(default_factory=dict)
    lines: dict[str, int] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    deps: list[str] = field(default_factory=list)
    routes: list[str] = field(default_factory=list)

    def line_of(self, field: str) -> int:
        return self.lines.get(field, self.line)

    def value(self, field: str) -> str:
        return self.fields.get(field, "")

    def copy(self) -> "Node":
        return Node(self.node_id, self.line, dict(self.fields), dict(self.lines), list(self.edges), list(self.deps), list(self.routes))


@dataclass
class Amendment:
    amend_id: str
    line: int
    fields: dict[str, str] = field(default_factory=dict)
    lines: dict[str, int] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)

    def line_of(self, field: str) -> int:
        return self.lines.get(field, self.line)


@dataclass
class Graph:
    path: str
    metadata: dict[str, str]
    metadata_lines: dict[str, int]
    nodes: dict[str, Node]
    node_records: list[Node]
    amendments: list[Amendment]
    diagnostics: Diagnostics


@dataclass
class Item:
    item_id: str
    line: int
    fields: dict[str, str] = field(default_factory=dict)
    lines: dict[str, int] = field(default_factory=dict)

    def line_of(self, field: str) -> int:
        return self.lines.get(field, self.line)


@dataclass
class Manifest:
    path: str
    metadata: dict[str, str]
    items: dict[str, Item]
    records: list[Item]
    diagnostics: Diagnostics


@dataclass
class Analysis:
    graph: Graph
    manifest: Manifest | None
    diagnostics: list[Diagnostic]
    root_closure: set[str]
    dependency_leaves: list[str]
    assumption_boundary: list[str]
    external_boundary: list[str]
    review_queue: list[str]
    alternative_route_count: int
    covered_nodes: set[str]
    uncovered_nodes: list[str]
    outside_root_closure: list[str]
    source_gaps: list[str]


def _id(value: str) -> bool:
    return bool(ID_RE.fullmatch(value))


def _nonempty(value: str) -> bool:
    value = value.strip()
    return bool(value and value != "-" and not (value.startswith("<") and value.endswith(">")))


@lru_cache(maxsize=None)
def _source_line_count(path: Path) -> int:
    return len(path.read_bytes().splitlines())


def _split_ids(value: str, *, path: str, line: int, description: str, errors: Diagnostics) -> list[str]:
    if value == "-":
        return []
    if not value:
        errors.add(path, line, f"{description} is empty; use '-' for none")
        return []
    answer = [part.strip() for part in value.split(",")]
    seen: set[str] = set()
    for identifier in answer:
        if not _id(identifier):
            errors.add(path, line, f"{description} has invalid ID {identifier!r}")
        if identifier in seen:
            errors.add(path, line, f"{description} repeats ID {identifier!r}")
        seen.add(identifier)
    return answer


def _parse_edge(value: str, *, path: str, line: int, errors: Diagnostics) -> Edge | None:
    parts = [part.strip() for part in value.split("|")]
    if len(parts) != 3 or not _id(parts[0]) or not _nonempty(parts[1]) or not _nonempty(parts[2]):
        errors.add(path, line, "EDGE must be '<dependency-or-route ID> | <source locator> | <direct-use rationale>'")
        return None
    return Edge(parts[0], parts[1], parts[2], line)


def _iter_active_lines(text: str):
    """Yield non-schema lines while ignoring fenced examples in Markdown."""
    fenced = False
    for line_no, raw in enumerate(text.splitlines(), 1):
        if raw.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            yield line_no, raw


def parse_graph(text: str, path: str = "<db>") -> Graph:
    errors = Diagnostics()
    metadata: dict[str, str] = {}
    metadata_lines: dict[str, int] = {}
    nodes: dict[str, Node] = {}
    records: list[Node] = []
    amendments: list[Amendment] = []
    amend_ids: set[str] = set()
    context: Node | Amendment | None = None
    saw_record = False
    for line, raw in _iter_active_lines(text):
        if raw.startswith("NODE:"):
            value = raw.removeprefix("NODE:").strip()
            context = Node(value, line)
            records.append(context)
            saw_record = True
            if not _id(value):
                errors.add(path, line, "NODE ID must be a stable nonempty token")
            elif value in nodes:
                errors.add(path, line, f"duplicate NODE {value!r}; first declared on line {nodes[value].line}")
            else:
                nodes[value] = context
            continue
        if raw.startswith("AMEND:"):
            value = raw.removeprefix("AMEND:").strip()
            context = Amendment(value, line)
            amendments.append(context)
            saw_record = True
            if not _id(value):
                errors.add(path, line, "AMEND ID must be a stable nonempty token")
            elif value in amend_ids:
                errors.add(path, line, f"duplicate AMEND {value!r}")
            amend_ids.add(value)
            continue
        match = FIELD_RE.fullmatch(raw)
        if not match:
            if not raw.strip() or raw.startswith("#"):
                context = None
            continue
        key, value = match.group(1), match.group(2).strip()
        if context is None and not saw_record and key in GRAPH_FIELDS:
            if key in metadata:
                errors.add(path, line, f"metadata {key} is repeated")
            else:
                metadata[key], metadata_lines[key] = value, line
            continue
        if context is None:
            continue
        allowed = NODE_FIELDS if isinstance(context, Node) else AMEND_FIELDS
        if key == "EDGE":
            edge = _parse_edge(value, path=path, line=line, errors=errors)
            if edge is not None:
                context.edges.append(edge)
            continue
        if key not in allowed:
            errors.add(path, line, f"{'node' if isinstance(context, Node) else 'amendment'} has unknown field {key!r}")
        elif key in context.fields:
            errors.add(path, line, f"field {key} repeats; first declared on line {context.lines[key]}")
        else:
            context.fields[key], context.lines[key] = value, line
    return Graph(path, metadata, metadata_lines, nodes, records, amendments, errors)


def parse_manifest(text: str, path: str = "<manifest>") -> Manifest:
    errors = Diagnostics()
    metadata: dict[str, str] = {}
    items: dict[str, Item] = {}
    records: list[Item] = []
    context: Item | None = None
    saw_item = False
    for line, raw in _iter_active_lines(text):
        if raw.startswith("ITEM:"):
            value = raw.removeprefix("ITEM:").strip()
            context = Item(value, line)
            records.append(context)
            saw_item = True
            if not _id(value):
                errors.add(path, line, "ITEM ID must be a stable nonempty token")
            elif value in items:
                errors.add(path, line, f"duplicate ITEM {value!r}; first declared on line {items[value].line}")
            else:
                items[value] = context
            continue
        match = FIELD_RE.fullmatch(raw)
        if not match:
            if not raw.strip() or raw.startswith("#"):
                context = None
            continue
        key, value = match.group(1), match.group(2).strip()
        if context is None and not saw_item and key == "CORPUS":
            metadata["CORPUS"] = value
            continue
        if context is None:
            continue
        if key not in MANIFEST_FIELDS:
            errors.add(path, line, f"coverage item has unknown field {key!r}")
        elif key in context.fields:
            errors.add(path, line, f"field {key} repeats; first declared on line {context.lines[key]}")
        else:
            context.fields[key], context.lines[key] = value, line
    return Manifest(path, metadata, items, records, errors)


def _validate_locator(value: str, *, path: str, line: int, field: str, errors: Diagnostics, source_root: Path | None) -> None:
    if value == "-":
        return
    if EXTERNAL_LOCATOR_RE.fullmatch(value):
        return
    match = LOCATOR_RE.fullmatch(value)
    if not match:
        errors.add(path, line, f"{field} must be '-' or '<path>#<anchor>@Lx-Ly' (or external:...#...)")
        return
    if int(match.group("first")) > int(match.group("last")):
        errors.add(path, line, f"{field} has descending line range")
    if source_root is not None:
        candidate = (source_root / match.group("path")).resolve()
        try:
            candidate.relative_to(source_root.resolve())
        except ValueError:
            errors.add(path, line, f"{field} path escapes --source-root")
        else:
            if not candidate.is_file():
                errors.add(path, line, f"{field} source path does not exist: {match.group('path')}")
            else:
                try:
                    line_count = _source_line_count(candidate)
                except OSError as error:
                    errors.add(path, line, f"{field} source path cannot be read: {error}")
                else:
                    if int(match.group("last")) > line_count:
                        errors.add(path, line, f"{field} range ends at L{match.group('last')}, beyond the source's {line_count} lines")


def _validate_frozen_path(value: str, *, path: str, line: int, field: str, errors: Diagnostics, source_root: Path | None) -> None:
    """Validate a declared anchor path without opening or interpreting Lean."""
    candidate_path = Path(value)
    if not value or value == "-" or candidate_path.is_absolute() or "\\" in value:
        errors.add(path, line, f"{field} must be a project-relative Lean declaration path")
        return
    if candidate_path.suffix != ".lean":
        errors.add(path, line, f"{field} must name a .lean declaration file")
    if any(part in {"", ".", ".."} for part in candidate_path.parts):
        errors.add(path, line, f"{field} must be a normalized project-relative path")
        return
    if source_root is not None:
        candidate = (source_root / candidate_path).resolve()
        try:
            candidate.relative_to(source_root.resolve())
        except ValueError:
            errors.add(path, line, f"{field} path escapes --source-root")
        else:
            if not candidate.is_file():
                errors.add(path, line, f"{field} declaration file does not exist: {value}")


def _frozen_manifest_path(value: str, *, graph: Graph) -> tuple[Path, str] | None:
    errors, path = graph.diagnostics, graph.path
    line = graph.metadata_lines.get("FROZEN_MANIFEST", 0)
    match = FROZEN_MANIFEST_RE.fullmatch(value)
    if match is None:
        errors.add(path, line, "FROZEN_MANIFEST must be '<project-relative manifest path> | sha256:<64 lowercase hex>'")
        return
    manifest_path = Path(match.group("path"))
    if manifest_path.is_absolute() or "\\" in match.group("path") or any(part in {"", ".", ".."} for part in manifest_path.parts):
        errors.add(path, line, "FROZEN_MANIFEST path must be normalized and project-relative")
        return None
    return manifest_path, match.group("hash")


def _validate_manifest_anchor_schema(payload: object, *, graph: Graph) -> dict[str, dict[str, str]] | None:
    """Read only immutable manifest identity fields, never proof/status metadata."""
    errors, path = graph.diagnostics, graph.path
    line = graph.metadata_lines.get("FROZEN_MANIFEST", 0)
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        errors.add(path, line, "FROZEN_MANIFEST JSON must use frozen-anchor manifest schema_version 1")
        return None
    anchors = payload.get("anchors")
    if not isinstance(anchors, list):
        errors.add(path, line, "FROZEN_MANIFEST JSON schema requires an anchors array")
        return None
    required = ("id", "path", "export", "abi_sha256")
    indexed: dict[str, dict[str, str]] = {}
    for index, anchor in enumerate(anchors):
        label = f"FROZEN_MANIFEST anchors[{index}]"
        if not isinstance(anchor, dict) or any(not isinstance(anchor.get(field), str) or not anchor[field] for field in required):
            errors.add(path, line, f"{label} must provide nonempty string id, path, export, and abi_sha256")
            continue
        contract = anchor.get("contract")
        if not isinstance(contract, dict) or not isinstance(contract.get("id"), str) or not contract["id"] or not isinstance(contract.get("version"), str) or not contract["version"]:
            errors.add(path, line, f"{label} must provide contract.id and contract.version strings")
            continue
        if not SHA256_RE.fullmatch(anchor["abi_sha256"]):
            errors.add(path, line, f"{label} abi_sha256 must be 64 lowercase hexadecimal characters")
            continue
        anchor_id = anchor["id"]
        if anchor_id in indexed:
            errors.add(path, line, f"FROZEN_MANIFEST has duplicate anchor id {anchor_id!r}")
            continue
        indexed[anchor_id] = {
            "id": anchor_id,
            "path": anchor["path"],
            "export": anchor["export"],
            "contract_id": contract["id"],
            "contract_version": contract["version"],
            "abi_sha256": anchor["abi_sha256"],
        }
    return indexed


def _load_frozen_manifest(value: str, *, graph: Graph, source_root: Path | None) -> dict[str, dict[str, str]] | None:
    """Bind anchors to the exact JSON manifest only when a source root is supplied."""
    parsed = _frozen_manifest_path(value, graph=graph)
    if parsed is None or source_root is None:
        return None
    manifest_path, expected_hash = parsed
    errors, path = graph.diagnostics, graph.path
    line = graph.metadata_lines.get("FROZEN_MANIFEST", 0)
    candidate = (source_root / manifest_path).resolve()
    try:
        candidate.relative_to(source_root.resolve())
    except ValueError:
        errors.add(path, line, "FROZEN_MANIFEST path escapes --source-root")
        return None
    try:
        raw = candidate.read_bytes()
    except OSError as error:
        errors.add(path, line, f"FROZEN_MANIFEST cannot be read: {error}")
        return None
    actual_hash = hashlib.sha256(raw).hexdigest()
    if actual_hash != expected_hash:
        errors.add(path, line, f"FROZEN_MANIFEST sha256 does not match {manifest_path}")
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        errors.add(path, line, f"FROZEN_MANIFEST is not valid UTF-8 JSON: {error}")
        return None
    return _validate_manifest_anchor_schema(payload, graph=graph)


def _validate_node_shape(graph: Graph, source_root: Path | None, frozen_anchors: set[str]) -> None:
    errors, path = graph.diagnostics, graph.path
    for node in graph.node_records:
        for field in NODE_FIELDS:
            if field not in node.fields:
                errors.add(path, node.line, f"node {node.node_id!r} is missing {field}")
        if not _id(node.node_id):
            continue
        for field in NODE_FIELDS:
            if field in node.fields and not node.fields[field]:
                errors.add(path, node.line_of(field), f"node {node.node_id!r} has empty {field}; use '-' where allowed")
        for field in ("KIND", "TITLE", "CONTRACT_ID", "CONTRACT_VERSION", "SOURCE_HYPOTHESES", "SOURCE_QUANTIFIERS", "SOURCE_CONCLUSION", "CONSTANT_SCOPE", "TOPOLOGY_STATUS", "EXTRACTOR", "LEAN_STATUS"):
            if not _nonempty(node.value(field)):
                errors.add(path, node.line_of(field), f"node {node.node_id!r} needs a non-placeholder {field}")
        if not _id(node.value("CONTRACT_ID")):
            errors.add(path, node.line_of("CONTRACT_ID"), f"node {node.node_id!r} CONTRACT_ID must be a stable contract-family ID")
        if node.value("KIND") not in KINDS:
            errors.add(path, node.line_of("KIND"), f"node {node.node_id!r} has invalid KIND {node.value('KIND')!r}")
        is_anchor = node.node_id in frozen_anchors
        frozen_fields = ("FROZEN_FILE", "FROZEN_DECL", "FROZEN_ANCHOR_ID", "FROZEN_ABI_SHA256")
        if is_anchor:
            for field in frozen_fields:
                if not _nonempty(node.value(field)):
                    errors.add(path, node.line_of(field), f"frozen anchor {node.node_id!r} needs a concrete {field}")
            if node.value("KIND") not in FROZEN_ANCHOR_KINDS:
                errors.add(path, node.line_of("KIND"), f"frozen anchor {node.node_id!r} has forbidden KIND {node.value('KIND')!r}")
            _validate_frozen_path(node.value("FROZEN_FILE"), path=path, line=node.line_of("FROZEN_FILE"), field=f"frozen anchor {node.node_id!r} FROZEN_FILE", errors=errors, source_root=source_root)
            if not LEAN_DECL_RE.fullmatch(node.value("FROZEN_DECL")):
                errors.add(path, node.line_of("FROZEN_DECL"), f"frozen anchor {node.node_id!r} FROZEN_DECL must be one Lean declaration name")
            if not _id(node.value("FROZEN_ANCHOR_ID")):
                errors.add(path, node.line_of("FROZEN_ANCHOR_ID"), f"frozen anchor {node.node_id!r} FROZEN_ANCHOR_ID must be a stable manifest anchor ID")
            if not SHA256_RE.fullmatch(node.value("FROZEN_ABI_SHA256")):
                errors.add(path, node.line_of("FROZEN_ABI_SHA256"), f"frozen anchor {node.node_id!r} FROZEN_ABI_SHA256 must be 64 lowercase hexadecimal characters")
        else:
            for field in frozen_fields:
                if node.value(field) != "-":
                    errors.add(path, node.line_of(field), f"ordinary node {node.node_id!r} must use {field}: -")
        if node.value("TOPOLOGY_STATUS") not in TOPOLOGY_STATUSES:
            errors.add(path, node.line_of("TOPOLOGY_STATUS"), f"node {node.node_id!r} has invalid TOPOLOGY_STATUS")
        node.deps = _split_ids(node.value("DEPS"), path=path, line=node.line_of("DEPS"), description=f"node {node.node_id!r} DEPS", errors=errors)
        node.routes = _split_ids(node.value("ROUTES"), path=path, line=node.line_of("ROUTES"), description=f"node {node.node_id!r} ROUTES", errors=errors)
        for field in ("STATEMENT_SOURCE", "PROOF_SOURCE"):
            _validate_locator(node.value(field), path=path, line=node.line_of(field), field=f"node {node.node_id!r} {field}", errors=errors, source_root=source_root)
        if not _nonempty(node.value("STATEMENT_SOURCE")):
            errors.add(path, node.line_of("STATEMENT_SOURCE"), f"node {node.node_id!r} needs a source-level STATEMENT_SOURCE")
        if node.value("KIND") in {"theorem", "proposition", "lemma", "corollary", "claim", "step", "application", "route"} and not _nonempty(node.value("PROOF_SOURCE")):
            errors.add(path, node.line_of("PROOF_SOURCE"), f"node {node.node_id!r} KIND {node.value('KIND')!r} needs a source-level PROOF_SOURCE")
        if node.value("TOPOLOGY_STATUS") == "REVIEWED":
            if not _nonempty(node.value("REVIEWER")):
                errors.add(path, node.line_of("REVIEWER"), f"reviewed node {node.node_id!r} needs REVIEWER")
            elif node.value("REVIEWER") == node.value("EXTRACTOR"):
                errors.add(path, node.line_of("REVIEWER"), f"reviewed node {node.node_id!r} reviewer equals extractor")
        elif node.value("REVIEWER") != "-" and node.value("REVIEWER") == node.value("EXTRACTOR"):
            errors.add(path, node.line_of("REVIEWER"), f"node {node.node_id!r} reviewer equals extractor")
        expected = node.deps + node.routes
        edge_ids = [edge.target for edge in node.edges]
        for target in sorted(set(expected)):
            count = edge_ids.count(target)
            if count != 1:
                errors.add(path, node.line, f"node {node.node_id!r} needs exactly one EDGE for {target!r}; found {count}")
        for target in sorted(set(edge_ids).difference(expected)):
            errors.add(path, node.line, f"node {node.node_id!r} EDGE {target!r} is not listed in DEPS or ROUTES")
        for edge in node.edges:
            _validate_locator(edge.source, path=path, line=edge.line, field=f"node {node.node_id!r} EDGE source", errors=errors, source_root=source_root)


def _validate_metadata(graph: Graph, source_root: Path | None) -> tuple[list[str], list[str], list[str], dict[str, dict[str, str]] | None]:
    errors, path = graph.diagnostics, graph.path
    for field in ("GRAPH_VERSION", "ROOTS", "CORPUS", "CONVENTIONS", "EXTERNAL_POLICY", "FROZEN_ANCHORS", "FROZEN_MANIFEST", "WRITER"):
        if field not in graph.metadata or not _nonempty(graph.metadata.get(field, "")):
            errors.add(path, graph.metadata_lines.get(field, 0), f"missing or placeholder graph metadata {field}")
    for field in ("GLOBAL_REVIEWER", "GLOBAL_REVIEW_REF"):
        if field not in graph.metadata:
            errors.add(path, 0, f"missing graph metadata {field}")
    if "STANDING_ASSUMPTIONS" not in graph.metadata:
        errors.add(path, 0, "missing graph metadata STANDING_ASSUMPTIONS")
    if graph.metadata.get("GRAPH_VERSION") not in {None, "4"}:
        errors.add(path, graph.metadata_lines.get("GRAPH_VERSION", 0), "GRAPH_VERSION must be 4")
    roots = _split_ids(graph.metadata.get("ROOTS", ""), path=path, line=graph.metadata_lines.get("ROOTS", 0), description="ROOTS", errors=errors)
    assumptions = _split_ids(graph.metadata.get("STANDING_ASSUMPTIONS", ""), path=path, line=graph.metadata_lines.get("STANDING_ASSUMPTIONS", 0), description="STANDING_ASSUMPTIONS", errors=errors)
    frozen_anchors = _split_ids(graph.metadata.get("FROZEN_ANCHORS", ""), path=path, line=graph.metadata_lines.get("FROZEN_ANCHORS", 0), description="FROZEN_ANCHORS", errors=errors)
    frozen_manifest = _load_frozen_manifest(graph.metadata.get("FROZEN_MANIFEST", ""), graph=graph, source_root=source_root)
    return roots, assumptions, frozen_anchors, frozen_manifest


def _validate_frozen_bindings(graph: Graph, frozen_anchors: list[str], manifest_anchors: dict[str, dict[str, str]] | None) -> None:
    """Compare graph anchor identity metadata to the author-approved manifest."""
    if manifest_anchors is None:
        return
    errors, path = graph.diagnostics, graph.path
    used_anchor_ids: dict[str, str] = {}
    fields = (
        ("FROZEN_FILE", "path"),
        ("FROZEN_DECL", "export"),
        ("CONTRACT_ID", "contract_id"),
        ("CONTRACT_VERSION", "contract_version"),
        ("FROZEN_ABI_SHA256", "abi_sha256"),
    )
    for node_id in frozen_anchors:
        node = graph.nodes.get(node_id)
        if node is None:
            continue
        anchor_id = node.value("FROZEN_ANCHOR_ID")
        anchor = manifest_anchors.get(anchor_id)
        if anchor is None:
            errors.add(path, node.line_of("FROZEN_ANCHOR_ID"), f"frozen anchor {node_id!r} FROZEN_ANCHOR_ID {anchor_id!r} has no unique entry in FROZEN_MANIFEST")
            continue
        prior = used_anchor_ids.get(anchor_id)
        if prior is not None:
            errors.add(path, node.line_of("FROZEN_ANCHOR_ID"), f"manifest anchor {anchor_id!r} is bound by both frozen graph nodes {prior!r} and {node_id!r}")
        else:
            used_anchor_ids[anchor_id] = node_id
        for graph_field, manifest_field in fields:
            if node.value(graph_field) != anchor[manifest_field]:
                errors.add(path, node.line_of(graph_field), f"frozen anchor {node_id!r} {graph_field} does not exactly match FROZEN_MANIFEST {manifest_field}")


def _amend_list(amend: Amendment, field: str, graph: Graph) -> list[str]:
    return _split_ids(amend.fields.get(field, "-"), path=graph.path, line=amend.line_of(field), description=f"amendment {amend.amend_id!r} {field}", errors=graph.diagnostics)


def _apply_amendments(graph: Graph, source_root: Path | None, frozen_anchors: set[str]) -> dict[str, Node]:
    errors, path = graph.diagnostics, graph.path
    effective = {node_id: node.copy() for node_id, node in graph.nodes.items()}
    for amend in graph.amendments:
        for field in AMEND_FIELDS:
            if field not in amend.fields:
                errors.add(path, amend.line, f"amendment {amend.amend_id!r} is missing {field}")
        target_id = amend.fields.get("TARGET", "")
        if target_id not in effective:
            errors.add(path, amend.line_of("TARGET"), f"amendment {amend.amend_id!r} targets unknown node {target_id!r}")
            continue
        author, reviewer = amend.fields.get("AUTHOR", ""), amend.fields.get("REVIEWER", "")
        if not _nonempty(author) or not _nonempty(reviewer):
            errors.add(path, amend.line, f"amendment {amend.amend_id!r} requires AUTHOR and independent REVIEWER")
        elif author == reviewer:
            errors.add(path, amend.line_of("REVIEWER"), f"amendment {amend.amend_id!r} reviewer equals author")
        if not _nonempty(amend.fields.get("NOTE", "")):
            errors.add(path, amend.line_of("NOTE"), f"amendment {amend.amend_id!r} needs a concrete NOTE")
        add_deps = _amend_list(amend, "ADD_DEPS", graph)
        drop_deps = _amend_list(amend, "DROP_DEPS", graph)
        add_routes = _amend_list(amend, "ADD_ROUTES", graph)
        drop_routes = _amend_list(amend, "DROP_ROUTES", graph)
        title = amend.fields.get("SET_TITLE", "-")
        if title != "-" and not _nonempty(title):
            errors.add(path, amend.line_of("SET_TITLE"), f"amendment {amend.amend_id!r} SET_TITLE must be non-placeholder")
        route_for = amend.fields.get("SET_ROUTE_FOR", "-")
        if route_for != "-" and not _id(route_for):
            errors.add(path, amend.line_of("SET_ROUTE_FOR"), f"amendment {amend.amend_id!r} SET_ROUTE_FOR must be a node ID or '-'")
        setter_fields = (
            "SET_TITLE", "SET_STATEMENT_SOURCE", "SET_PROOF_SOURCE",
            "SET_CONTRACT_ID", "SET_CONTRACT_VERSION", "SET_SOURCE_HYPOTHESES",
            "SET_SOURCE_QUANTIFIERS", "SET_SOURCE_CONCLUSION",
            "SET_CONSTANT_SCOPE", "SET_ROUTE_FOR",
        )
        setters = [field for field in setter_fields if amend.fields.get(field, "-") != "-"]
        if not (add_deps or drop_deps or add_routes or drop_routes or setters):
            errors.add(path, amend.line, f"amendment {amend.amend_id!r} has no operation")
        if target_id in frozen_anchors:
            anchor_immutable_setters = {
                "SET_STATEMENT_SOURCE", "SET_PROOF_SOURCE",
                "SET_CONTRACT_ID", "SET_CONTRACT_VERSION",
                "SET_SOURCE_HYPOTHESES", "SET_SOURCE_QUANTIFIERS",
                "SET_SOURCE_CONCLUSION", "SET_CONSTANT_SCOPE",
            }
            if any(amend.fields.get(field, "-") != "-" for field in anchor_immutable_setters):
                errors.add(path, amend.line, f"amendment {amend.amend_id!r} cannot alter immutable source or contract fields of frozen anchor {target_id!r}; create a new versioned anchor")
        target = effective[target_id]
        for additions, removals, name, current in ((add_deps, drop_deps, "DEPS", target.deps), (add_routes, drop_routes, "ROUTES", target.routes)):
            overlap = set(additions).intersection(removals)
            if overlap:
                errors.add(path, amend.line, f"amendment {amend.amend_id!r} both adds and drops {name} {sorted(overlap)}")
            for item in additions:
                if item in current:
                    errors.add(path, amend.line, f"amendment {amend.amend_id!r} adds existing {name} {item!r}")
            for item in removals:
                if item not in current:
                    errors.add(path, amend.line, f"amendment {amend.amend_id!r} drops absent {name} {item!r}")
        additions = add_deps + add_routes
        edge_ids = [edge.target for edge in amend.edges]
        for item in sorted(set(additions)):
            if edge_ids.count(item) != 1:
                errors.add(path, amend.line, f"amendment {amend.amend_id!r} needs exactly one EDGE for added {item!r}")
        for item in sorted(set(edge_ids).difference(additions)):
            errors.add(path, amend.line, f"amendment {amend.amend_id!r} EDGE {item!r} does not support an added dependency or route")
        for edge in amend.edges:
            _validate_locator(edge.source, path=path, line=edge.line, field=f"amendment {amend.amend_id!r} EDGE source", errors=errors, source_root=source_root)
        for field in ("SET_STATEMENT_SOURCE", "SET_PROOF_SOURCE"):
            value = amend.fields.get(field, "-")
            if value != "-":
                _validate_locator(value, path=path, line=amend.line_of(field), field=f"amendment {amend.amend_id!r} {field}", errors=errors, source_root=source_root)
        contract_id = amend.fields.get("SET_CONTRACT_ID", "-")
        if contract_id != "-" and not _id(contract_id):
            errors.add(path, amend.line_of("SET_CONTRACT_ID"), f"amendment {amend.amend_id!r} SET_CONTRACT_ID must be a stable contract-family ID")
        for field in ("SET_CONTRACT_VERSION", "SET_SOURCE_HYPOTHESES", "SET_SOURCE_QUANTIFIERS", "SET_SOURCE_CONCLUSION", "SET_CONSTANT_SCOPE"):
            value = amend.fields.get(field, "-")
            if value != "-" and not _nonempty(value):
                errors.add(path, amend.line_of(field), f"amendment {amend.amend_id!r} {field} must be non-placeholder")
        # Apply even where a later validator reports an issue: retaining a deterministic
        # effective graph improves diagnostics, but --check still fails.
        target.deps = [item for item in target.deps if item not in set(drop_deps)] + add_deps
        target.routes = [item for item in target.routes if item not in set(drop_routes)] + add_routes
        target.edges = [edge for edge in target.edges if edge.target not in set(drop_deps + drop_routes)] + amend.edges
        for source_field, target_field in (
            ("SET_TITLE", "TITLE"),
            ("SET_STATEMENT_SOURCE", "STATEMENT_SOURCE"),
            ("SET_PROOF_SOURCE", "PROOF_SOURCE"),
            ("SET_CONTRACT_ID", "CONTRACT_ID"),
            ("SET_CONTRACT_VERSION", "CONTRACT_VERSION"),
            ("SET_SOURCE_HYPOTHESES", "SOURCE_HYPOTHESES"),
            ("SET_SOURCE_QUANTIFIERS", "SOURCE_QUANTIFIERS"),
            ("SET_SOURCE_CONCLUSION", "SOURCE_CONCLUSION"),
            ("SET_CONSTANT_SCOPE", "CONSTANT_SCOPE"),
            ("SET_ROUTE_FOR", "ROUTE_FOR"),
        ):
            value = amend.fields.get(source_field, "-")
            if value != "-":
                target.fields[target_field] = value
                target.lines[target_field] = amend.line_of(source_field)
    return effective


def _validate_topology(graph: Graph, nodes: dict[str, Node], roots: list[str], standing_assumptions: list[str], frozen_anchors: list[str]) -> None:
    errors, path = graph.diagnostics, graph.path
    contracts: dict[tuple[str, str], str] = {}
    for node in nodes.values():
        contract = (node.value("CONTRACT_ID"), node.value("CONTRACT_VERSION"))
        if contract in contracts:
            errors.add(path, node.line_of("CONTRACT_ID"), f"contract identity {contract[0]!r} version {contract[1]!r} is shared by nodes {contracts[contract]!r} and {node.node_id!r}")
        elif all(contract):
            contracts[contract] = node.node_id
    for root in roots:
        if root not in nodes:
            errors.add(path, graph.metadata_lines.get("ROOTS", 0), f"ROOTS references unknown node {root!r}")
        elif nodes[root].value("KIND") == "route":
            errors.add(path, graph.metadata_lines.get("ROOTS", 0), f"ROOTS cannot designate route node {root!r}")
        elif root not in frozen_anchors:
            errors.add(path, graph.metadata_lines.get("ROOTS", 0), f"ROOT {root!r} must be listed in FROZEN_ANCHORS")
    frozen_files: dict[str, str] = {}
    frozen_decls: dict[str, str] = {}
    for identifier in frozen_anchors:
        if identifier not in nodes:
            errors.add(path, graph.metadata_lines.get("FROZEN_ANCHORS", 0), f"FROZEN_ANCHORS references unknown node {identifier!r}")
            continue
        node = nodes[identifier]
        frozen_file, frozen_decl = node.value("FROZEN_FILE"), node.value("FROZEN_DECL")
        if frozen_file in frozen_files:
            errors.add(path, node.line_of("FROZEN_FILE"), f"frozen anchor file {frozen_file!r} is shared by {frozen_files[frozen_file]!r} and {identifier!r}; one declaration file owns one anchor")
        else:
            frozen_files[frozen_file] = identifier
        if frozen_decl in frozen_decls:
            errors.add(path, node.line_of("FROZEN_DECL"), f"frozen declaration {frozen_decl!r} is shared by {frozen_decls[frozen_decl]!r} and {identifier!r}")
        else:
            frozen_decls[frozen_decl] = identifier
    declared_assumptions = set(standing_assumptions)
    for identifier in standing_assumptions:
        if identifier not in nodes:
            errors.add(path, graph.metadata_lines.get("STANDING_ASSUMPTIONS", 0), f"STANDING_ASSUMPTIONS references unknown node {identifier!r}")
        elif nodes[identifier].value("KIND") != "assumption":
            errors.add(path, graph.metadata_lines.get("STANDING_ASSUMPTIONS", 0), f"declared standing assumption {identifier!r} is not KIND: assumption")
    for node in nodes.values():
        if node.value("KIND") == "assumption" and node.node_id not in declared_assumptions:
            errors.add(path, node.line_of("KIND"), f"assumption node {node.node_id!r} is not declared in STANDING_ASSUMPTIONS")
    for node in nodes.values():
        for dep in node.deps:
            if dep not in nodes:
                errors.add(path, node.line_of("DEPS"), f"node {node.node_id!r} has dangling dependency {dep!r}")
            elif dep == node.node_id:
                errors.add(path, node.line_of("DEPS"), f"node {node.node_id!r} depends on itself")
            elif nodes[dep].value("KIND") == "route":
                errors.add(path, node.line_of("DEPS"), f"route {dep!r} must appear in ROUTES, not DEPS")
        if node.value("KIND") == "route":
            if node.routes:
                errors.add(path, node.line_of("ROUTES"), f"route node {node.node_id!r} cannot have ROUTES")
            owner = node.value("ROUTE_FOR")
            if owner == "-" or owner not in nodes:
                errors.add(path, node.line_of("ROUTE_FOR"), f"route node {node.node_id!r} has unknown ROUTE_FOR owner {owner!r}")
            elif node.node_id not in nodes[owner].routes:
                errors.add(path, node.line_of("ROUTE_FOR"), f"route node {node.node_id!r} is not listed by owner {owner!r}")
        elif node.value("ROUTE_FOR") != "-":
            errors.add(path, node.line_of("ROUTE_FOR"), f"only KIND: route may have ROUTE_FOR")
        if node.value("KIND") in {"assumption", "external"} and (node.deps or node.routes):
            errors.add(path, node.line, f"{node.value('KIND')} node {node.node_id!r} must be a dependency leaf")
        for route in node.routes:
            if route not in nodes:
                errors.add(path, node.line_of("ROUTES"), f"node {node.node_id!r} has dangling route {route!r}")
            elif nodes[route].value("KIND") != "route":
                errors.add(path, node.line_of("ROUTES"), f"node {node.node_id!r} ROUTES item {route!r} is not KIND: route")
            elif nodes[route].value("ROUTE_FOR") != node.node_id:
                errors.add(path, node.line_of("ROUTES"), f"route {route!r} does not name {node.node_id!r} in ROUTE_FOR")
    state: dict[str, int] = {}
    stack: list[str] = []
    positions: dict[str, int] = {}
    reported: set[tuple[str, ...]] = set()
    def visit(identifier: str) -> None:
        state[identifier] = 1
        positions[identifier] = len(stack)
        stack.append(identifier)
        for child in nodes[identifier].deps + nodes[identifier].routes:
            if child not in nodes:
                continue
            if state.get(child, 0) == 0:
                visit(child)
            elif state[child] == 1:
                cycle = tuple(stack[positions[child]:] + [child])
                if cycle not in reported:
                    reported.add(cycle)
                    errors.add(path, nodes[identifier].line, "dependency cycle: " + " -> ".join(cycle))
        stack.pop()
        positions.pop(identifier, None)
        state[identifier] = 2
    for identifier in sorted(nodes):
        if state.get(identifier, 0) == 0:
            visit(identifier)


def _parse_disposition(value: str, manifest: Manifest, item: Item) -> tuple[str, list[str]]:
    if value == "EXCLUDED":
        return "EXCLUDED", []
    prefix = "NODE "
    if not value.startswith(prefix):
        manifest.diagnostics.add(manifest.path, item.line_of("DISPOSITION"), "DISPOSITION must be EXCLUDED or NODE <comma-separated node IDs>")
        return "INVALID", []
    return "NODE", _split_ids(value.removeprefix(prefix), path=manifest.path, line=item.line_of("DISPOSITION"), description=f"item {item.item_id!r} DISPOSITION", errors=manifest.diagnostics)


def _validate_manifest(manifest: Manifest, nodes: dict[str, Node], source_root: Path | None, require_complete: bool) -> set[str]:
    errors, path = manifest.diagnostics, manifest.path
    if not _nonempty(manifest.metadata.get("CORPUS", "")):
        errors.add(path, 0, "missing or placeholder manifest CORPUS")
    covered: set[str] = set()
    for item in manifest.records:
        for field in MANIFEST_FIELDS:
            if field not in item.fields or not item.fields.get(field, ""):
                errors.add(path, item.line, f"item {item.item_id!r} is missing or has placeholder {field}")
        for field in ("KIND", "SOURCE", "DISPOSITION", "REASON", "COVERAGE_STATUS", "EXTRACTOR"):
            if not _nonempty(item.fields.get(field, "")):
                errors.add(path, item.line_of(field), f"item {item.item_id!r} needs a non-placeholder {field}")
        if item.fields.get("KIND") not in MANIFEST_KINDS:
            errors.add(path, item.line_of("KIND"), f"item {item.item_id!r} has invalid KIND")
        coverage_status = item.fields.get("COVERAGE_STATUS", "")
        if coverage_status not in TOPOLOGY_STATUSES:
            errors.add(path, item.line_of("COVERAGE_STATUS"), f"item {item.item_id!r} has invalid COVERAGE_STATUS")
        extractor, reviewer = item.fields.get("EXTRACTOR", ""), item.fields.get("REVIEWER", "")
        if coverage_status == "REVIEWED":
            if not _nonempty(reviewer):
                errors.add(path, item.line_of("REVIEWER"), f"reviewed item {item.item_id!r} needs REVIEWER")
            elif reviewer == extractor:
                errors.add(path, item.line_of("REVIEWER"), f"reviewed item {item.item_id!r} reviewer equals extractor")
        elif reviewer != "-" and reviewer == extractor:
            errors.add(path, item.line_of("REVIEWER"), f"item {item.item_id!r} reviewer equals extractor")
        _validate_locator(item.fields.get("SOURCE", ""), path=path, line=item.line_of("SOURCE"), field=f"item {item.item_id!r} SOURCE", errors=errors, source_root=source_root)
        mode, ids = _parse_disposition(item.fields.get("DISPOSITION", ""), manifest, item)
        if mode == "EXCLUDED" and not _nonempty(item.fields.get("REASON", "")):
            errors.add(path, item.line_of("REASON"), f"excluded item {item.item_id!r} needs concrete REASON")
        for identifier in ids:
            if identifier not in nodes:
                errors.add(path, item.line_of("DISPOSITION"), f"item {item.item_id!r} references unknown node {identifier!r}")
            else:
                covered.add(identifier)
    if require_complete:
        for node in nodes.values():
            if node.node_id not in covered:
                errors.add(path, 0, f"complete-coverage gate: node {node.node_id!r} is not named by any manifest ITEM")
    return covered


def _closure(nodes: dict[str, Node], roots: Sequence[str]) -> set[str]:
    seen: set[str] = set()
    todo = [root for root in roots if root in nodes]
    while todo:
        identifier = todo.pop()
        if identifier in seen:
            continue
        seen.add(identifier)
        todo.extend(nodes[identifier].deps + nodes[identifier].routes)
    return seen


def _initial_lean_status_errors(graph: Graph, nodes: dict[str, Node]) -> None:
    """Publish gate only: retain Lean fields without interpreting later status."""
    for node in nodes.values():
        expected = "ASSUMED" if node.value("KIND") == "assumption" else "EXTERNAL" if node.value("KIND") == "external" else "NOT_STARTED"
        if node.value("LEAN_STATUS") != expected:
            graph.diagnostics.add(graph.path, node.line_of("LEAN_STATUS"), f"initial-Lean gate: node {node.node_id!r} must use LEAN_STATUS: {expected}")
        for field in ("LEAN_REF", "LEAN_NOTE"):
            if node.value(field) != "-":
                graph.diagnostics.add(graph.path, node.line_of(field), f"initial-Lean gate: node {node.node_id!r} must use {field}: -")


def analyze(graph: Graph, manifest: Manifest | None = None, *, source_root: Path | None = None, require_reviewed: bool = False, require_complete_coverage: bool = False, require_initial_lean_status: bool = False, require_all_reachable: bool = False) -> Analysis:
    roots, standing_assumptions, frozen_anchors, frozen_manifest = _validate_metadata(graph, source_root)
    _validate_node_shape(graph, source_root, set(frozen_anchors))
    _validate_frozen_bindings(graph, frozen_anchors, frozen_manifest)
    nodes = _apply_amendments(graph, source_root, set(frozen_anchors))
    _validate_topology(graph, nodes, roots, standing_assumptions, frozen_anchors)
    closure = _closure(nodes, roots)
    outside = sorted(set(nodes).difference(closure))
    if require_all_reachable:
        for identifier in outside:
            graph.diagnostics.add(graph.path, nodes[identifier].line, f"root-connectivity gate: node {identifier!r} is outside every declared root closure")
    if require_reviewed:
        for field in ("GLOBAL_REVIEWER", "GLOBAL_REVIEW_REF"):
            if not _nonempty(graph.metadata.get(field, "")):
                graph.diagnostics.add(graph.path, graph.metadata_lines.get(field, 0), f"review gate: missing or placeholder {field}")
        if _nonempty(graph.metadata.get("GLOBAL_REVIEWER", "")) and graph.metadata.get("GLOBAL_REVIEWER") == graph.metadata.get("WRITER"):
            graph.diagnostics.add(graph.path, graph.metadata_lines.get("GLOBAL_REVIEWER", 0), "review gate: GLOBAL_REVIEWER must differ from WRITER")
        global_reviewer = graph.metadata.get("GLOBAL_REVIEWER", "")
        node_extractors = {node.value("EXTRACTOR") for node in nodes.values() if _nonempty(node.value("EXTRACTOR"))}
        if _nonempty(global_reviewer) and global_reviewer in node_extractors:
            graph.diagnostics.add(graph.path, graph.metadata_lines.get("GLOBAL_REVIEWER", 0), "review gate: GLOBAL_REVIEWER must be fresh, not a node extractor")
        for identifier in sorted(nodes):
            node = nodes[identifier]
            if node.value("TOPOLOGY_STATUS") != "REVIEWED":
                graph.diagnostics.add(graph.path, node.line_of("TOPOLOGY_STATUS"), f"review gate: graph node {identifier!r} is not REVIEWED")
    if require_initial_lean_status:
        _initial_lean_status_errors(graph, nodes)
    covered: set[str] = set()
    if manifest is not None:
        graph_corpus = graph.metadata.get("CORPUS", "")
        manifest_corpus = manifest.metadata.get("CORPUS", "")
        if _nonempty(graph_corpus) and _nonempty(manifest_corpus) and graph_corpus != manifest_corpus:
            manifest.diagnostics.add(manifest.path, 0, "manifest CORPUS does not exactly match graph CORPUS")
        covered = _validate_manifest(manifest, nodes, source_root, require_complete_coverage)
        if require_reviewed:
            for item in manifest.items.values():
                if item.fields.get("COVERAGE_STATUS") != "REVIEWED":
                    manifest.diagnostics.add(manifest.path, item.line_of("COVERAGE_STATUS"), f"review gate: coverage item {item.item_id!r} is not REVIEWED")
    elif require_complete_coverage:
        graph.diagnostics.add(graph.path, 0, "--require-complete-coverage needs --manifest")
    diagnostics = list(graph.diagnostics.items)
    if manifest is not None:
        diagnostics.extend(manifest.diagnostics.items)
    closure_nodes = [nodes[identifier] for identifier in sorted(closure)]
    leaves = [node.node_id for node in closure_nodes if not node.deps and not node.routes]
    assumptions = [node.node_id for node in closure_nodes if node.value("KIND") == "assumption" and not node.deps and not node.routes]
    externals = [node.node_id for node in closure_nodes if node.value("KIND") == "external" and not node.deps and not node.routes]
    review_queue = [identifier for identifier in sorted(nodes) if nodes[identifier].value("TOPOLOGY_STATUS") in {"PROPOSED", "DISPUTED"}]
    uncovered = sorted(node.node_id for node in nodes.values() if node.node_id not in covered)
    source_gaps = sorted(node.node_id for node in nodes.values() if "SOURCE_GAP:" in node.value("NOTE"))
    graph.nodes = nodes  # expose effective graph to rendering callers
    return Analysis(graph, manifest, diagnostics, closure, leaves, assumptions, externals, review_queue, sum(len(node.routes) for node in nodes.values()), covered, uncovered, outside, source_gaps)


def render_dashboard(analysis: Analysis) -> str:
    nodes = analysis.graph.nodes
    roots = _split_ids(analysis.graph.metadata.get("ROOTS", "-"), path=analysis.graph.path, line=0, description="ROOTS", errors=Diagnostics())
    frozen_anchors = _split_ids(analysis.graph.metadata.get("FROZEN_ANCHORS", "-"), path=analysis.graph.path, line=0, description="FROZEN_ANCHORS", errors=Diagnostics())
    contracts = {(node.value("CONTRACT_ID"), node.value("CONTRACT_VERSION")) for node in nodes.values()}
    lines = ["Regenerated by `proof_depgraph.py`; do not hand-edit.", "", "### Dashboard", "", f"* Total nodes: **{len(nodes)}**", f"* Frozen anchors: **{len(frozen_anchors)}**", f"* Versioned statement contracts: **{len(contracts)}**", f"* Total edges: **{sum(len(node.deps) + len(node.routes) for node in nodes.values())}**", f"* Root-closure nodes: **{len(analysis.root_closure)}**", f"* Dependency leaves in root closure: **{len(analysis.dependency_leaves)}**", f"* Assumption boundary leaves: **{len(analysis.assumption_boundary)}**", f"* External boundary leaves: **{len(analysis.external_boundary)}**", f"* Alternative routes: **{analysis.alternative_route_count}**", f"* Topology review queue: **{len(analysis.review_queue)}**", f"* Explicit source gaps: **{len(analysis.source_gaps)}**"]
    if analysis.manifest is not None:
        excluded = sum(1 for item in analysis.manifest.items.values() if item.fields.get("DISPOSITION") == "EXCLUDED")
        lines.append(f"* Coverage items: **{len(analysis.manifest.items)}**; excluded: **{excluded}**")
    lines += ["", "### Roots", ""]
    for root in roots:
        node = nodes.get(root)
        state = node.value("TOPOLOGY_STATUS") if node else "MISSING"
        contract = f"{node.value('CONTRACT_ID')}@{node.value('CONTRACT_VERSION')}" if node else "MISSING"
        frozen = "frozen" if root in frozen_anchors else "not frozen"
        lines.append(f"* `{root}` [{state}; {frozen}] — contract `{contract}`")
    def section(title: str, identifiers: Sequence[str]) -> None:
        lines.extend(["", f"### {title}", ""])
        if identifiers:
            for identifier in identifiers:
                node = nodes[identifier]
                lines.append(f"* `{identifier}` [{node.value('TOPOLOGY_STATUS')}] — {node.value('TITLE')}")
        else:
            lines.append("* _(none)_")
    section("Topology review queue", analysis.review_queue)
    section("Dependency leaves in root closure", analysis.dependency_leaves)
    section("Assumption boundary leaves", analysis.assumption_boundary)
    section("External boundary leaves", analysis.external_boundary)
    section("Uncovered graph nodes", analysis.uncovered_nodes)
    section("Nodes outside every root closure", analysis.outside_root_closure)
    section("Explicit source gaps", analysis.source_gaps)
    return "\n".join(lines)


def as_json(analysis: Analysis) -> str:
    nodes = analysis.graph.nodes
    result = {
        "roots": _split_ids(analysis.graph.metadata.get("ROOTS", "-"), path=analysis.graph.path, line=0, description="ROOTS", errors=Diagnostics()),
        "frozen_anchors": _split_ids(analysis.graph.metadata.get("FROZEN_ANCHORS", "-"), path=analysis.graph.path, line=0, description="FROZEN_ANCHORS", errors=Diagnostics()),
        "frozen_manifest": analysis.graph.metadata.get("FROZEN_MANIFEST", ""),
        "root_closure": sorted(analysis.root_closure),
        "dependency_leaves": analysis.dependency_leaves,
        "assumption_boundary": analysis.assumption_boundary,
        "external_boundary": analysis.external_boundary,
        "topology_review_queue": analysis.review_queue,
        "alternative_route_count": analysis.alternative_route_count,
        "uncovered_nodes": analysis.uncovered_nodes,
        "outside_root_closure": analysis.outside_root_closure,
        "source_gaps": analysis.source_gaps,
        "nodes": [{"id": identifier, "kind": nodes[identifier].value("KIND"), "contract_id": nodes[identifier].value("CONTRACT_ID"), "contract_version": nodes[identifier].value("CONTRACT_VERSION"), "frozen_file": nodes[identifier].value("FROZEN_FILE"), "frozen_decl": nodes[identifier].value("FROZEN_DECL"), "frozen_anchor_id": nodes[identifier].value("FROZEN_ANCHOR_ID"), "frozen_abi_sha256": nodes[identifier].value("FROZEN_ABI_SHA256"), "source_hypotheses": nodes[identifier].value("SOURCE_HYPOTHESES"), "source_quantifiers": nodes[identifier].value("SOURCE_QUANTIFIERS"), "source_conclusion": nodes[identifier].value("SOURCE_CONCLUSION"), "constant_scope": nodes[identifier].value("CONSTANT_SCOPE"), "topology_status": nodes[identifier].value("TOPOLOGY_STATUS"), "deps": nodes[identifier].deps, "routes": nodes[identifier].routes} for identifier in sorted(nodes)],
    }
    return json.dumps(result, indent=2, sort_keys=True) + "\n"


def _marker_region(text: str, path: str, errors: Diagnostics) -> tuple[int, int, str] | None:
    begins: list[tuple[int, int, str]] = []
    ends: list[tuple[int, int]] = []
    fenced = False
    offset = 0
    for line, raw in enumerate(text.splitlines(keepends=True), 1):
        bare = raw.rstrip("\r\n")
        if bare.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and bare == BEGIN:
            begins.append((line, offset + len(raw), "\r\n" if raw.endswith("\r\n") else "\n"))
        elif not fenced and bare == END:
            ends.append((line, offset))
        offset += len(raw)
    if len(begins) != 1 or len(ends) != 1 or not begins or not ends or begins[0][0] >= ends[0][0]:
        errors.add(path, 0, "database needs exactly one ordered pair of generated dashboard markers")
        return None
    return begins[0][1], ends[0][1], begins[0][2]


def _expected_body(body: str, newline: str) -> str:
    return body.replace("\n", newline) + newline


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True, help="Markdown dependency database")
    parser.add_argument("--manifest", type=Path, help="optional Markdown coverage manifest")
    parser.add_argument("--source-root", type=Path, help="optional root used to verify source locator paths")
    parser.add_argument("--require-reviewed", action="store_true", help="require REVIEWED topology for every graph node and coverage item")
    parser.add_argument("--require-complete-coverage", action="store_true", help="require every graph node in a manifest disposition")
    parser.add_argument("--require-initial-lean-status", action="store_true", help="require initialized Lean planning fields without inspecting Lean")
    parser.add_argument("--require-all-reachable", action="store_true", help="require every graph node to feed at least one declared root")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="validate and require a current generated dashboard")
    modes.add_argument("--report", action="store_true", help="print the deterministic topology dashboard without writing")
    modes.add_argument("--json", action="store_true", help="print machine-readable effective source topology")
    modes.add_argument("--write-dashboard", action="store_true", help="replace only the generated dashboard marker interior")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        db_text = args.db.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as error:
        print(f"{args.db}: cannot read database: {error}", file=sys.stderr)
        return 1
    manifest = None
    if args.manifest is not None:
        try:
            manifest = parse_manifest(args.manifest.read_bytes().decode("utf-8"), str(args.manifest))
        except (OSError, UnicodeError) as error:
            print(f"{args.manifest}: cannot read manifest: {error}", file=sys.stderr)
            return 1
    graph = parse_graph(db_text, str(args.db))
    analysis = analyze(graph, manifest, source_root=args.source_root, require_reviewed=args.require_reviewed, require_complete_coverage=args.require_complete_coverage, require_initial_lean_status=args.require_initial_lean_status, require_all_reachable=args.require_all_reachable)
    diagnostics = Diagnostics()
    diagnostics.extend(analysis.diagnostics)
    body = render_dashboard(analysis)
    region = _marker_region(db_text, str(args.db), diagnostics) if (args.check or args.write_dashboard) else None
    if args.check and region is not None:
        begin, end, newline = region
        if db_text[begin:end] != _expected_body(body, newline):
            diagnostics.add(str(args.db), 0, "generated dashboard is stale; run --write-dashboard")
    if diagnostics.items:
        for diagnostic in diagnostics.items:
            print(diagnostic.render(), file=sys.stderr)
        return 1
    if args.json:
        print(as_json(analysis), end="")
    elif args.report:
        print(body)
    elif args.write_dashboard:
        assert region is not None
        begin, end, newline = region
        updated = db_text[:begin] + _expected_body(body, newline) + db_text[end:]
        args.db.write_bytes(updated.encode("utf-8"))
        print("dashboard: updated" if updated != db_text else "dashboard: current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
