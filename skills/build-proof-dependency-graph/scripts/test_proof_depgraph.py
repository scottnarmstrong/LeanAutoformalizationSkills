#!/usr/bin/env python3
"""Focused tests for the source-only proof dependency graph linter."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))
import proof_depgraph as graph  # noqa: E402


LOC = "paper.tex#sec@L1-L2"
SHA = "a" * 64


def header(*, roots: str = "root", frozen_anchors: str | None = None, standing_assumptions: str = "-", global_reviewer: str = "global-b", global_ref: str = "review-report", manifest_hash: str = SHA) -> str:
    anchors = roots if frozen_anchors is None else frozen_anchors
    return "\n".join((
        "GRAPH_VERSION: 4",
        f"ROOTS: {roots}",
        "CORPUS: paper.tex @ test-revision",
        "CONVENTIONS: carrier and normalization checked separately",
        f"STANDING_ASSUMPTIONS: {standing_assumptions}",
        "EXTERNAL_POLICY: explicit external leaf nodes",
        f"FROZEN_ANCHORS: {anchors}",
        f"FROZEN_MANIFEST: Frozen/manifest.json | sha256:{manifest_hash}",
        "WRITER: central-writer",
        f"GLOBAL_REVIEWER: {global_reviewer}",
        f"GLOBAL_REVIEW_REF: {global_ref}",
    ))


def node(
    identifier: str,
    *,
    kind: str = "lemma",
    deps: str = "-",
    routes: str = "-",
    route_for: str = "-",
    topology: str = "REVIEWED",
    extractor: str = "extractor-a",
    reviewer: str = "reviewer-b",
    lean_status: str = "NOT_STARTED",
    lean_ref: str = "-",
    edges: bool = True,
    frozen: bool | None = None,
) -> str:
    is_frozen = identifier in {"root", "thm:root"} if frozen is None else frozen
    required = [] if deps == "-" else [part.strip() for part in deps.split(",")]
    required += [] if routes == "-" else [part.strip() for part in routes.split(",")]
    lines = [
        f"NODE: {identifier}",
        f"KIND: {kind}",
        f"TITLE: title for {identifier}",
        f"STATEMENT_SOURCE: {LOC}",
        f"PROOF_SOURCE: {LOC}",
        f"CONTRACT_ID: contract.{identifier}",
        "CONTRACT_VERSION: 1",
        "SOURCE_HYPOTHESES: none",
        "SOURCE_QUANTIFIERS: all source variables, outer-to-inner",
        f"SOURCE_CONCLUSION: exact normalized conclusion for {identifier}",
        "CONSTANT_SCOPE: none",
        f"FROZEN_FILE: Frozen/{identifier.replace('#', '_').replace(':', '_')}.lean" if is_frozen else "FROZEN_FILE: -",
        f"FROZEN_DECL: Contracts.{identifier.replace('#', '_').replace(':', '_')}" if is_frozen else "FROZEN_DECL: -",
        f"FROZEN_ANCHOR_ID: {identifier}" if is_frozen else "FROZEN_ANCHOR_ID: -",
        f"FROZEN_ABI_SHA256: {SHA}" if is_frozen else "FROZEN_ABI_SHA256: -",
        f"DEPS: {deps}",
        f"ROUTES: {routes}",
        f"ROUTE_FOR: {route_for}",
        f"TOPOLOGY_STATUS: {topology}",
        f"EXTRACTOR: {extractor}",
        f"REVIEWER: {reviewer}",
        f"LEAN_STATUS: {lean_status}",
        f"LEAN_REF: {lean_ref}",
        "LEAN_NOTE: -",
        "NOTE: test record",
    ]
    if edges:
        lines.extend(f"EDGE: {target} | {LOC} | directly used" for target in required)
    return "\n".join(lines)


def amend(identifier: str, target: str, *, add_deps: str = "-", drop_deps: str = "-", add_routes: str = "-", drop_routes: str = "-", edges: tuple[str, ...] = ()) -> str:
    lines = [
        f"AMEND: {identifier}",
        f"TARGET: {target}",
        "AUTHOR: author-a",
        "REVIEWER: reviewer-b",
        f"ADD_DEPS: {add_deps}",
        f"DROP_DEPS: {drop_deps}",
        f"ADD_ROUTES: {add_routes}",
        f"DROP_ROUTES: {drop_routes}",
        "SET_TITLE: -",
        "SET_STATEMENT_SOURCE: -",
        "SET_PROOF_SOURCE: -",
        "SET_CONTRACT_ID: -",
        "SET_CONTRACT_VERSION: -",
        "SET_SOURCE_HYPOTHESES: -",
        "SET_SOURCE_QUANTIFIERS: -",
        "SET_SOURCE_CONCLUSION: -",
        "SET_CONSTANT_SCOPE: -",
        "SET_ROUTE_FOR: -",
    ]
    lines.extend(f"EDGE: {edge} | {LOC} | amendment direct use" for edge in edges)
    lines.append("NOTE: independently reviewed topology correction")
    return "\n".join(lines)


def manifest_item(identifier: str, disposition: str, *, status: str = "REVIEWED", extractor: str = "coverage-a", reviewer: str = "coverage-b") -> str:
    return "\n".join((
        f"ITEM: {identifier}",
        "KIND: theorem",
        f"SOURCE: {LOC}",
        f"DISPOSITION: {disposition}",
        "REASON: explicit inventory disposition",
        f"COVERAGE_STATUS: {status}",
        f"EXTRACTOR: {extractor}",
        f"REVIEWER: {reviewer}",
    ))


def manifest(*items: str) -> str:
    return "CORPUS: paper.tex @ test-revision\n\n" + "\n\n".join(items) + "\n"


class GraphTests(unittest.TestCase):
    def materialize_frozen_inputs(self, root: Path, *identifiers: str) -> str:
        frozen = root / "Frozen"
        frozen.mkdir(exist_ok=True)
        anchors = []
        for identifier in identifiers:
            name = identifier.replace("#", "_").replace(":", "_")
            (frozen / f"{name}.lean").write_text("-- declaration body intentionally unread by this linter\n", encoding="utf-8")
            anchors.append({
                "id": identifier,
                "path": f"Frozen/{name}.lean",
                "export": f"Contracts.{name}",
                "contract": {"id": f"contract.{identifier}", "version": "1"},
                "abi_sha256": SHA,
            })
        raw = json.dumps({"schema_version": 1, "anchors": anchors}, indent=2).encode("utf-8")
        (frozen / "manifest.json").write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def analyse(self, text: str, manifest_text: str | None = None, **kwargs: object) -> graph.Analysis:
        db = graph.parse_graph(text, "graph.md")
        coverage = graph.parse_manifest(manifest_text, "coverage.md") if manifest_text is not None else None
        return graph.analyze(db, coverage, **kwargs)

    def messages(self, analysis: graph.Analysis) -> str:
        return "\n".join(item.render() for item in analysis.diagnostics)

    def test_and_or_routes_are_topological_and_do_not_use_lean_status(self) -> None:
        text = "\n\n".join((
            header(),
            node("common"),
            node("missing"),
            node("root#first", kind="route", deps="missing", route_for="root", lean_status="NOT_STARTED"),
            node("root#second", kind="route", deps="common", route_for="root", lean_status="PROVED", lean_ref="-"),
            node("root", kind="proposition", deps="common", routes="root#first, root#second"),
        ))
        analysis = self.analyse(text)
        self.assertFalse(analysis.diagnostics, self.messages(analysis))
        self.assertEqual(analysis.alternative_route_count, 2)
        self.assertEqual(analysis.root_closure, {"root", "common", "missing", "root#first", "root#second"})
        self.assertEqual(analysis.dependency_leaves, ["common", "missing"])
        self.assertFalse(analysis.review_queue)

    def test_tex_style_colon_labels_are_valid_ids(self) -> None:
        text = "\n\n".join((header(roots="thm:root"), node("3.1:input"), node("thm:root", kind="theorem", deps="3.1:input")))
        analysis = self.analyse(text)
        self.assertFalse(analysis.diagnostics, self.messages(analysis))
        self.assertEqual(analysis.root_closure, {"thm:root", "3.1:input"})

    def test_manifest_and_independent_review_gate(self) -> None:
        text = "\n\n".join((header(), node("root")))
        good_manifest = manifest(manifest_item("m.root", "NODE root"))
        good = self.analyse(text, good_manifest, require_reviewed=True, require_complete_coverage=True)
        self.assertFalse(good.diagnostics, self.messages(good))
        bad_manifest = manifest(manifest_item("m.root", "NODE root", status="PROPOSED"))
        bad = self.analyse(text, bad_manifest, require_reviewed=True)
        self.assertIn("coverage item 'm.root' is not REVIEWED", self.messages(bad))

    def test_amendment_changes_effective_dependencies(self) -> None:
        text = "\n\n".join((
            header(),
            node("extra", lean_status="PROVED", lean_ref="Extra.lean#ok"),
            node("root"),
            amend("review-1", "root", add_deps="extra", edges=("extra",)),
        ))
        analysis = self.analyse(text)
        self.assertFalse(analysis.diagnostics, self.messages(analysis))
        self.assertEqual(analysis.graph.nodes["root"].deps, ["extra"])
        self.assertEqual(analysis.root_closure, {"root", "extra"})

    def test_cycle_and_missing_edge_are_hard_errors(self) -> None:
        text = "\n\n".join((
            header(),
            node("root", deps="a", edges=False),
            node("a", deps="root"),
        ))
        analysis = self.analyse(text)
        message = self.messages(analysis)
        self.assertIn("needs exactly one EDGE for 'a'", message)
        self.assertIn("dependency cycle", message)

    def test_fenced_schema_example_is_ignored(self) -> None:
        text = "\n\n".join((
            header(),
            "```text\nNODE: <invalid schema example>\nKIND: nonsense\n```",
            node("root"),
        ))
        analysis = self.analyse(text)
        self.assertFalse(analysis.diagnostics, self.messages(analysis))
        self.assertEqual(set(analysis.graph.nodes), {"root"})

    def test_global_review_and_node_review_gate(self) -> None:
        text = "\n\n".join((header(global_reviewer="-", global_ref="-"), node("root", topology="PROPOSED", reviewer="-")))
        analysis = self.analyse(text, require_reviewed=True)
        message = self.messages(analysis)
        self.assertIn("missing or placeholder GLOBAL_REVIEWER", message)
        self.assertIn("graph node 'root' is not REVIEWED", message)

    def test_global_reviewer_must_differ_from_writer(self) -> None:
        text = "\n\n".join((header(global_reviewer="central-writer"), node("root")))
        analysis = self.analyse(text, require_reviewed=True)
        self.assertIn("GLOBAL_REVIEWER must differ from WRITER", self.messages(analysis))

    def test_global_reviewer_must_not_be_a_node_extractor(self) -> None:
        text = "\n\n".join((header(global_reviewer="extractor-a"), node("root")))
        analysis = self.analyse(text, require_reviewed=True)
        self.assertIn("GLOBAL_REVIEWER must be fresh", self.messages(analysis))

    def test_initial_lean_status_gate_only_checks_initialization(self) -> None:
        text = "\n\n".join((
            header(standing_assumptions="assume.h"),
            node("ordinary"),
            node("assume.h", kind="assumption", lean_status="ASSUMED"),
            node("external.x", kind="external", lean_status="EXTERNAL"),
            node("root", deps="ordinary, assume.h, external.x"),
        ))
        good = self.analyse(text, require_initial_lean_status=True)
        self.assertFalse(good.diagnostics, self.messages(good))
        bad = self.analyse(text.replace("LEAN_STATUS: NOT_STARTED", "LEAN_STATUS: PROVED", 1), require_initial_lean_status=True)
        self.assertIn("initial-Lean gate", self.messages(bad))

    def test_optional_source_root_checks_locator_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper.tex").write_text("source\nsource\n", encoding="utf-8")
            manifest_hash = self.materialize_frozen_inputs(root, "root")
            text = "\n\n".join((header(manifest_hash=manifest_hash), node("root")))
            good = self.analyse(text, source_root=root)
            self.assertFalse(good.diagnostics, self.messages(good))
            bad = self.analyse(text.replace("paper.tex", "missing.tex"), source_root=root)
            self.assertIn("source path does not exist", self.messages(bad))

    def test_source_line_bounds_and_paths_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "proof notes.md").write_text("one\ntwo\n", encoding="utf-8")
            manifest_hash = self.materialize_frozen_inputs(root, "root")
            text = "\n\n".join((header(manifest_hash=manifest_hash), node("root").replace(LOC, "proof notes.md#root@L1-L2")))
            good = self.analyse(text, source_root=root)
            self.assertFalse(good.diagnostics, self.messages(good))
            bad = self.analyse(text.replace("@L1-L2", "@L1-L3"), source_root=root)
            self.assertIn("beyond the source's 2 lines", self.messages(bad))

    def test_leaf_and_root_connectivity_gates(self) -> None:
        text = "\n\n".join((
            header(standing_assumptions="assume.h"),
            node("leaf"),
            node("orphan"),
            node("assume.h", kind="assumption", deps="leaf", lean_status="ASSUMED"),
            node("root", deps="assume.h"),
        ))
        analysis = self.analyse(text, require_all_reachable=True)
        message = self.messages(analysis)
        self.assertIn("assumption node 'assume.h' must be a dependency leaf", message)
        self.assertIn("node 'orphan' is outside every declared root closure", message)

    def test_assumption_nodes_must_be_frozen_in_header(self) -> None:
        text = "\n\n".join((header(), node("assume.h", kind="assumption", lean_status="ASSUMED"), node("root", deps="assume.h")))
        analysis = self.analyse(text)
        self.assertIn("assumption node 'assume.h' is not declared", self.messages(analysis))

    def test_manifest_corpus_must_match_graph(self) -> None:
        text = "\n\n".join((header(), node("root")))
        coverage = manifest(manifest_item("m.root", "NODE root")).replace(
            "paper.tex @ test-revision", "paper.tex @ another-revision"
        )
        analysis = self.analyse(text, coverage)
        self.assertIn("manifest CORPUS does not exactly match graph CORPUS", self.messages(analysis))

    def test_source_gaps_are_reported_without_becoming_proof_status(self) -> None:
        text = "\n\n".join((header(), node("root").replace(
            "NOTE: test record", "NOTE: SOURCE_GAP: the prose invokes an unstated estimate"
        )))
        analysis = self.analyse(text, require_reviewed=True, require_initial_lean_status=True)
        self.assertFalse(analysis.diagnostics, self.messages(analysis))
        self.assertEqual(analysis.source_gaps, ["root"])
        self.assertIn("Explicit source gaps: **1**", graph.render_dashboard(analysis))

    def test_statement_contract_is_required_and_unique(self) -> None:
        missing = "\n\n".join((header(), node("root").replace(
            "CONTRACT_ID: contract.root\n", ""
        )))
        self.assertIn("is missing CONTRACT_ID", self.messages(self.analyse(missing)))

        duplicate = "\n\n".join((
            header(),
            node("input"),
            node("root", deps="input").replace("contract.root", "contract.input"),
        ))
        self.assertIn("contract identity 'contract.input' version '1' is shared", self.messages(self.analyse(duplicate)))

        distinct_version = duplicate.replace("CONTRACT_VERSION: 1", "CONTRACT_VERSION: 2", 1)
        self.assertFalse(self.analyse(distinct_version).diagnostics, self.messages(self.analyse(distinct_version)))

    def test_statement_contract_amendment_updates_effective_contract(self) -> None:
        change = amend("contract-fix", "input").replace(
            "SET_CONTRACT_VERSION: -", "SET_CONTRACT_VERSION: 2"
        ).replace(
            "SET_SOURCE_HYPOTHESES: -", "SET_SOURCE_HYPOTHESES: corrected source premise"
        )
        text = "\n\n".join((header(), node("input"), node("root", deps="input"), change))
        analysis = self.analyse(text)
        self.assertFalse(analysis.diagnostics, self.messages(analysis))
        self.assertEqual(analysis.graph.nodes["input"].value("CONTRACT_ID"), "contract.input")
        self.assertEqual(analysis.graph.nodes["input"].value("CONTRACT_VERSION"), "2")
        self.assertEqual(analysis.graph.nodes["input"].value("SOURCE_HYPOTHESES"), "corrected source premise")

        placeholder = amend("contract-version-fix", "input").replace(
            "SET_CONTRACT_VERSION: -", "SET_CONTRACT_VERSION: <version>"
        )
        bad = self.analyse("\n\n".join((header(), node("input"), node("root", deps="input"), placeholder)))
        self.assertIn("SET_CONTRACT_VERSION must be non-placeholder", self.messages(bad))

    def test_frozen_anchor_metadata_and_fields_are_required(self) -> None:
        text = "\n\n".join((header(), node("root")))
        self.assertFalse(self.analyse(text).diagnostics, self.messages(self.analyse(text)))
        missing_manifest = text.replace(f"FROZEN_MANIFEST: Frozen/manifest.json | sha256:{SHA}\n", "")
        self.assertIn("missing or placeholder graph metadata FROZEN_MANIFEST", self.messages(self.analyse(missing_manifest)))
        bad_hash = text.replace(f"FROZEN_ABI_SHA256: {SHA}", "FROZEN_ABI_SHA256: abc")
        self.assertIn("must be 64 lowercase hexadecimal", self.messages(self.analyse(bad_hash)))

    def test_every_root_must_be_frozen(self) -> None:
        text = "\n\n".join((header(frozen_anchors="input"), node("input", frozen=True), node("root", frozen=False, deps="input")))
        self.assertIn("ROOT 'root' must be listed in FROZEN_ANCHORS", self.messages(self.analyse(text)))

    def test_duplicate_frozen_bindings_are_rejected(self) -> None:
        text = "\n\n".join((
            header(frozen_anchors="root,input"),
            node("input", frozen=True),
            node("root", deps="input").replace("FROZEN_FILE: Frozen/root.lean", "FROZEN_FILE: Frozen/input.lean"),
        ))
        self.assertIn("one declaration file owns one anchor", self.messages(self.analyse(text)))
        duplicate_decl = text.replace("FROZEN_DECL: Contracts.root", "FROZEN_DECL: Contracts.input")
        self.assertIn("frozen declaration 'Contracts.input' is shared", self.messages(self.analyse(duplicate_decl)))

    def test_ordinary_node_cannot_pretend_to_be_an_anchor(self) -> None:
        text = "\n\n".join((header(), node("input", frozen=True), node("root", deps="input")))
        self.assertIn("ordinary node 'input' must use FROZEN_FILE: -", self.messages(self.analyse(text)))

    def test_anchor_kind_and_immutable_field_amendments_are_restricted(self) -> None:
        bad_kind = "\n\n".join((header(), node("root", kind="step")))
        self.assertIn("forbidden KIND 'step'", self.messages(self.analyse(bad_kind)))
        change = amend("contract-fix", "root").replace("SET_CONTRACT_ID: -", "SET_CONTRACT_ID: contract.root.v2")
        text = "\n\n".join((header(), node("root"), change))
        self.assertIn("cannot alter immutable source or contract fields of frozen anchor 'root'", self.messages(self.analyse(text)))
        version_change = amend("contract-version-fix", "root").replace("SET_CONTRACT_VERSION: -", "SET_CONTRACT_VERSION: 2")
        version_text = "\n\n".join((header(), node("root"), version_change))
        self.assertIn("cannot alter immutable source or contract fields of frozen anchor 'root'", self.messages(self.analyse(version_text)))
        statement_source_change = amend("statement-source-fix", "root").replace(
            "SET_STATEMENT_SOURCE: -", "SET_STATEMENT_SOURCE: paper.tex#corrected-statement@L1-L2"
        )
        statement_source_text = "\n\n".join((header(), node("root"), statement_source_change))
        self.assertIn("cannot alter immutable source or contract fields of frozen anchor 'root'", self.messages(self.analyse(statement_source_text)))
        proof_source_change = amend("proof-source-fix", "root").replace(
            "SET_PROOF_SOURCE: -", "SET_PROOF_SOURCE: paper.tex#corrected-proof@L1-L2"
        )
        proof_source_text = "\n\n".join((header(), node("root"), proof_source_change))
        self.assertIn("cannot alter immutable source or contract fields of frozen anchor 'root'", self.messages(self.analyse(proof_source_text)))

    def test_frozen_paths_are_checked_only_when_source_root_is_provided(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper.tex").write_text("source\nsource\n", encoding="utf-8")
            manifest_hash = self.materialize_frozen_inputs(root, "root")
            good = self.analyse("\n\n".join((header(manifest_hash=manifest_hash), node("root"))), source_root=root)
            self.assertFalse(good.diagnostics, self.messages(good))
            bad = self.analyse("\n\n".join((header(manifest_hash=manifest_hash), node("root").replace("Frozen/root.lean", "Frozen/missing.lean"))), source_root=root)
            self.assertIn("declaration file does not exist", self.messages(bad))

    def test_frozen_manifest_binding_accepts_exact_author_approved_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper.tex").write_text("source\nsource\n", encoding="utf-8")
            manifest_hash = self.materialize_frozen_inputs(root, "root")
            analysis = self.analyse("\n\n".join((header(manifest_hash=manifest_hash), node("root"))), source_root=root)
            self.assertFalse(analysis.diagnostics, self.messages(analysis))

    def test_frozen_manifest_binding_allows_distinct_versioned_anchor_id_and_rejects_identity_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper.tex").write_text("source\nsource\n", encoding="utf-8")
            self.materialize_frozen_inputs(root, "root")
            manifest_path = root / "Frozen" / "manifest.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["anchors"][0]["id"] = "root.v2"
            raw = json.dumps(payload).encode("utf-8")
            manifest_path.write_bytes(raw)
            manifest_hash = hashlib.sha256(raw).hexdigest()
            base = "\n\n".join((header(manifest_hash=manifest_hash), node("root")))
            successor = base.replace("FROZEN_ANCHOR_ID: root", "FROZEN_ANCHOR_ID: root.v2")
            self.assertFalse(self.analyse(successor, source_root=root).diagnostics, self.messages(self.analyse(successor, source_root=root)))
            for field, changed in (
                ("FROZEN_FILE", "Frozen/missing.lean"),
                ("FROZEN_DECL", "Contracts.wrong"),
                ("CONTRACT_VERSION", "2"),
                ("FROZEN_ABI_SHA256", "b" * 64),
            ):
                if field == "FROZEN_FILE":
                    text = base.replace("FROZEN_FILE: Frozen/root.lean", f"FROZEN_FILE: {changed}")
                elif field == "FROZEN_DECL":
                    text = base.replace("FROZEN_DECL: Contracts.root", f"FROZEN_DECL: {changed}")
                elif field == "CONTRACT_VERSION":
                    text = base.replace("CONTRACT_VERSION: 1", f"CONTRACT_VERSION: {changed}")
                else:
                    text = base.replace(f"FROZEN_ABI_SHA256: {SHA}", f"FROZEN_ABI_SHA256: {changed}")
                text = text.replace("FROZEN_ANCHOR_ID: root", "FROZEN_ANCHOR_ID: root.v2")
                self.assertIn(f"{field} does not exactly match FROZEN_MANIFEST", self.messages(self.analyse(text, source_root=root)))

    def test_frozen_manifest_hash_json_and_schema_are_checked_with_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper.tex").write_text("source\nsource\n", encoding="utf-8")
            manifest_hash = self.materialize_frozen_inputs(root, "root")
            text = "\n\n".join((header(manifest_hash=manifest_hash), node("root")))
            self.assertIn("sha256 does not match", self.messages(self.analyse(text.replace(manifest_hash, "b" * 64), source_root=root)))
            malformed = b"{ this is not JSON"
            (root / "Frozen" / "manifest.json").write_bytes(malformed)
            malformed_text = "\n\n".join((header(manifest_hash=hashlib.sha256(malformed).hexdigest()), node("root")))
            self.assertIn("not valid UTF-8 JSON", self.messages(self.analyse(malformed_text, source_root=root)))
            invalid_schema = json.dumps({"schema_version": 2, "anchors": []}).encode("utf-8")
            (root / "Frozen" / "manifest.json").write_bytes(invalid_schema)
            schema_text = "\n\n".join((header(manifest_hash=hashlib.sha256(invalid_schema).hexdigest()), node("root")))
            self.assertIn("schema_version 1", self.messages(self.analyse(schema_text, source_root=root)))

    def test_duplicate_manifest_anchor_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "paper.tex").write_text("source\nsource\n", encoding="utf-8")
            self.materialize_frozen_inputs(root, "root")
            manifest_path = root / "Frozen" / "manifest.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["anchors"].append(payload["anchors"][0].copy())
            raw = json.dumps(payload).encode("utf-8")
            manifest_path.write_bytes(raw)
            text = "\n\n".join((header(manifest_hash=hashlib.sha256(raw).hexdigest()), node("root")))
            self.assertIn("duplicate anchor id 'root'", self.messages(self.analyse(text, source_root=root)))

    def test_dashboard_and_json_expose_frozen_anchor_identity(self) -> None:
        analysis = self.analyse("\n\n".join((header(), node("root"))))
        self.assertIn("Frozen anchors: **1**", graph.render_dashboard(analysis))
        payload = json.loads(graph.as_json(analysis))
        self.assertEqual(payload["frozen_anchors"], ["root"])
        self.assertEqual(payload["nodes"][0]["frozen_decl"], "Contracts.root")


class CliTests(unittest.TestCase):
    def _db(self, newline: str = "\n", stale: bool = True) -> str:
        interior = "stale" if stale else ""
        pieces = [header(), node("root"), graph.BEGIN, interior, graph.END, ""]
        return newline.join(pieces)

    def test_write_check_and_crlf_preservation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "DEPGRAPH.md"
            db_path.write_bytes(self._db("\r\n").encode("utf-8"))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(graph.main(["--db", str(db_path), "--write-dashboard"]), 0)
                self.assertEqual(graph.main(["--db", str(db_path), "--check"]), 0)
            data = db_path.read_bytes()
            self.assertIn(b"\r\n", data)
            self.assertNotIn(b"\nRegenerated", data.replace(b"\r\n", b""))

    def test_check_rejects_stale_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "DEPGRAPH.md"
            db_path.write_text(self._db(), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stderr(output):
                self.assertEqual(graph.main(["--db", str(db_path), "--check"]), 1)
            self.assertIn("generated dashboard is stale", output.getvalue())


if __name__ == "__main__":
    unittest.main()
