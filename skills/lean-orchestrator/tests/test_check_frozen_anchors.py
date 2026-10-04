import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "check_frozen_anchors.py"
SPEC = importlib.util.spec_from_file_location("frozen_guard", SCRIPT)
guard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(guard)


def sha(data):
    raw = data.encode() if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()


class FrozenAnchorGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.write("Project/Internal/Target.lean", self.internal_target())
        self.write("Project/Frozen/Definition.lean",
                   "module\n\n@[expose] public section\n\nnamespace Project\ndef frozenDefinition : Nat := 1\n"
                   "end Project\n\nend\n")
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry"))
        self.manifest = self.valid_manifest()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def write_bytes(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def internal_target(self, section="public section\n\n"):
        return ("module\n\n" + section + "namespace Project.Internal\n"
                "theorem internalTarget : True := True.intro\nend Project.Internal\n\nend\n")

    def anchor(self, body, import_line="public import Project.Internal.Target",
               section="@[expose] public section\n\n", declaration="theorem target"):
        return ("-- bytes before the first marker are frozen\n"
                "-- FROZEN_ANCHOR_PREFIX_BEGIN\nmodule\n\n" + import_line + "\n\n" + section +
                "namespace Project\n/-- source docstring -/\n" + declaration + " : True :=\n"
                "-- FROZEN_ANCHOR_PROOF_BEGIN\n" + body + "\n"
                "-- FROZEN_ANCHOR_PROOF_END\n-- FROZEN_ANCHOR_SUFFIX_BEGIN\n"
                "end Project\n\nend\n-- suffix\n-- FROZEN_ANCHOR_SUFFIX_END\n"
                "-- bytes after the final marker are frozen\n")

    def legacy_anchor(self, body):
        return ("-- bytes before the first marker are frozen\n"
                "-- FROZEN_ANCHOR_PREFIX_BEGIN\nimport Project.Internal.Target\n"
                "namespace Project\n/-- source docstring -/\ntheorem target : True :=\n"
                "-- FROZEN_ANCHOR_PROOF_BEGIN\n" + body + "\n"
                "-- FROZEN_ANCHOR_PROOF_END\n-- FROZEN_ANCHOR_SUFFIX_BEGIN\n"
                "end Project\n-- suffix\n-- FROZEN_ANCHOR_SUFFIX_END\n"
                "-- bytes after the final marker are frozen\n")

    def regions(self, text):
        body_start = text.index("\n", text.index("FROZEN_ANCHOR_PROOF_BEGIN")) + 1
        body_end = text.rfind("\n", 0, text.index("FROZEN_ANCHOR_PROOF_END")) + 1
        return text[:body_start], text[body_start:body_end], text[body_end:]

    def approval(self):
        return {"approved_by": "A", "approved_at": "2026-01-01", "approval_ref": "r", "approval_version": "1"}

    def valid_manifest(self):
        text = (self.root / "Project/Frozen/Target.lean").read_bytes().decode()
        prefix, _body, suffix = self.regions(text)
        definition = (self.root / "Project/Frozen/Definition.lean").read_bytes()
        return {"schema_version": 1, "manifest_state": "AUTHOR_APPROVED",
                "seal_limits": {"max_body_lines": 3, "max_body_bytes": 100},
                "anchors": [{"id": "target_v1", "kind": "theorem",
                "author_approval": self.approval(), "source": {"revision": "abc", "range": "x:1-2"},
                "contract": {"id": "c", "version": "1"}, "path": "Project/Frozen/Target.lean",
                "export": "Project.target", "implementation": {"module": "Project.Internal.Target", "export": "Project.Internal.internalTarget"},
                "split_policy": {"source_group": "paper.target", "mode": "NOT_SPLIT", "ruling_ref": "ruling-target"},
                "abi_sha256": "a" * 64,
                "definition_closure": [{"path": "Project/Frozen/Definition.lean", "sha256": sha(definition)}],
                "state": "DRAFT_SORRY", "prefix_sha256": sha(prefix), "suffix_sha256": sha(suffix),
                "draft_allowlist": {"frozen_paths": [], "audit_paths": []}},
                {"id": "definition_v1", "kind": "definition", "author_approval": self.approval(),
                "source": {"revision": "abc", "range": "x:0-0"}, "contract": {"id": "d", "version": "1"},
                "path": "Project/Frozen/Definition.lean", "export": "Project.frozenDefinition",
                "split_policy": {"source_group": "paper.definition", "mode": "NOT_SPLIT", "ruling_ref": "ruling-definition"},
                "abi_sha256": "b" * 64, "definition_closure": [], "state": "SEALED",
                "full_file_sha256": sha(definition)}]}

    def check_manifest(self, manifest=None, allow_non_module=False):
        checker = guard.Guard(self.root, allow_non_module=allow_non_module)
        checker.check(manifest or self.manifest)
        return checker.errors

    def assert_error(self, needle):
        self.assertTrue(any(needle in error for error in self.check_manifest()), self.check_manifest())

    def test_valid_draft_passes(self):
        self.assertEqual(self.check_manifest(), [])

    def test_non_module_anchor_fails(self):
        self.write("Project/Frozen/Target.lean", self.legacy_anchor("by sorry"))
        self.manifest = self.valid_manifest()
        self.assert_error("frozen file is not a module")

    def test_non_module_definition_fails(self):
        self.write("Project/Frozen/Definition.lean", "namespace Project\ndef frozenDefinition : Nat := 1\nend Project\n")
        self.manifest = self.valid_manifest()
        self.assert_error("frozen file is not a module")

    def test_legacy_repository_passes_only_with_flag(self):
        self.write("Project/Internal/Target.lean",
                   "namespace Project.Internal\ntheorem internalTarget : True := True.intro\nend Project.Internal\n")
        self.write("Project/Frozen/Definition.lean", "namespace Project\ndef frozenDefinition : Nat := 1\nend Project\n")
        self.write("Project/Frozen/Target.lean", self.legacy_anchor("by exact Project.Internal.internalTarget"))
        self.manifest = self.valid_manifest()
        self.manifest["anchors"][0]["state"] = "SEALED"
        self.assertEqual(self.check_manifest(allow_non_module=True), [])
        self.assertTrue(self.check_manifest())

    def test_module_private_by_default_declaration_fails(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry", section=""))
        self.manifest = self.valid_manifest()
        self.assert_error("frozen declaration cannot be private")

    def test_public_modifier_outside_public_section_passes(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry", section="", declaration="public theorem target"))
        self.manifest = self.valid_manifest()
        self.assertEqual(self.check_manifest(), [])

    def test_dotted_section_name_keeps_namespace(self):
        text = "module\n\npublic section\n\nnamespace Project\nsection A.B\nend A.B\ntheorem t : True := trivial\nend Project\n"
        self.assertEqual(guard.Guard(self.root).declarations(text), [(None, "theorem", "t", "Project.t")])

    def test_root_prefixed_export_resolves(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry", declaration="theorem _root_.Other.target"))
        self.manifest = self.valid_manifest()
        self.manifest["anchors"][0]["export"] = "Other.target"
        self.assertEqual(self.check_manifest(), [])

    def test_sealed_module_private_implementation_rejected(self):
        self.write("Project/Internal/Target.lean", self.internal_target(section=""))
        self.write("Project/Frozen/Target.lean", self.anchor("by exact Project.Internal.internalTarget"))
        self.manifest = self.valid_manifest()
        self.manifest["anchors"][0]["state"] = "SEALED"
        self.assert_error("implementation export is not declared exactly once")

    def test_module_system_extra_public_declaration_fails(self):
        text = (self.root / "Project/Frozen/Target.lean").read_text()
        self.write("Project/Frozen/Target.lean",
                   text.replace("namespace Project\n", "namespace Project\npublic theorem extra : True := trivial\n"))
        self.manifest = self.valid_manifest()
        self.assertTrue(self.check_manifest())

    def test_private_noncomputable_declaration_fails(self):
        text = (self.root / "Project/Frozen/Target.lean").read_text()
        self.write("Project/Frozen/Target.lean",
                   text.replace("namespace Project\n", "namespace Project\nprivate noncomputable def hidden : Nat := 0\n"))
        self.manifest = self.valid_manifest()
        self.assertTrue(self.check_manifest())

    def test_duplicate_nonempty_anchor_id_fails(self):
        self.manifest["anchors"][1]["id"] = self.manifest["anchors"][0]["id"]
        self.assert_error("duplicate anchor ID target_v1")

    def test_sixty_five_extra_hypotheses_mutation_fails(self):
        extras = " ".join(f"(h{i} : True)" for i in range(65))
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry").replace("theorem target : True :=", f"theorem target {extras} : True :="))
        self.assert_error("prefix hash drift")

    def test_bundled_assumption_mutation_fails(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry").replace("target : True", "target (h : True ∧ True) : True"))
        self.assert_error("prefix hash drift")

    def test_import_mutation_fails(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry", "import Mathlib"))
        self.assert_error("prefix hash drift")

    def test_docstring_mutation_fails(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry").replace("source docstring", "altered docstring"))
        self.assert_error("prefix hash drift")

    def test_before_prefix_marker_mutation_fails(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry").replace("bytes before", "changed before"))
        self.assert_error("prefix hash drift")

    def test_after_suffix_marker_mutation_fails(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry").replace("bytes after", "changed after"))
        self.assert_error("suffix hash drift")

    def test_draft_body_must_be_only_sorry(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by\n  exact True.intro"))
        self.assert_error("exactly the single authorized")

    def test_ordinary_file_sorry_fails(self):
        self.write("Project/Ordinary.lean", "theorem ordinary : True := by sorry\n")
        self.assert_error("unauthorized `sorry`")

    def test_comment_and_string_sorry_do_not_trigger(self):
        self.write("Project/Prose.lean", "-- sorry is prose\n#check \"sorry\"\ntheorem prose : True := True.intro\n")
        self.assertEqual(self.check_manifest(), [])

    def test_reverse_import_fails(self):
        self.write("Project/Internal/Target.lean", "import Project.Frozen.Target\ntheorem internalTarget : True := True.intro\n")
        self.assert_error("reverse-import")

    def test_draft_use_outside_allowlist_fails(self):
        self.write("Project/Consumer.lean", "import Project.Frozen.Target\n#check Project.target\n")
        self.assert_error("DRAFT_SORRY imported directly or transitively")

    def test_audit_draft_import_cannot_flow_to_ordinary_module(self):
        self.write("Project/Audit/DraftInspection.lean", "import Project.Frozen.Target\n#check Project.target\n")
        self.write("Project/Consumer.lean", "import Project.Audit.DraftInspection\n")
        self.manifest["anchors"][0]["draft_allowlist"]["audit_paths"] = ["Project/Audit/DraftInspection.lean"]
        self.assert_error("DRAFT_SORRY imported directly or transitively")

    def test_draft_provider_direct_import_fails(self):
        self.write("Project/Consumer.lean", "import Project.Internal.Target\n")
        self.assert_error("DRAFT provider imported directly or transitively")

    def test_draft_provider_transitive_import_fails(self):
        self.write("Project/Bridge.lean", "import Project.Internal.Target\n")
        self.write("Project/Consumer.lean", "import Project.Bridge\n")
        self.assert_error("DRAFT provider imported directly or transitively")

    def test_draft_provider_export_use_fails_without_import_edge(self):
        self.write("Project/Consumer.lean", "#check Project.Internal.internalTarget\n")
        self.assert_error("DRAFT provider export used outside")

    def test_draft_provider_itself_and_own_frozen_anchor_are_allowed(self):
        self.assertEqual(self.check_manifest(), [])

    def test_two_draft_anchors_cannot_share_provider(self):
        first = self.manifest["anchors"][0]
        text = self.anchor("by sorry").replace("theorem target", "theorem otherTarget")
        self.write("Project/Frozen/OtherTarget.lean", text)
        second = dict(first)
        second.update({"id": "other_target_v1", "path": "Project/Frozen/OtherTarget.lean",
                       "export": "Project.otherTarget",
                       "contract": {"id": "other", "version": "1"},
                       "split_policy": {"source_group": "paper.other", "mode": "NOT_SPLIT",
                                        "ruling_ref": "ruling-other"}})
        prefix, _body, suffix = self.regions(text)
        second["prefix_sha256"], second["suffix_sha256"] = sha(prefix), sha(suffix)
        self.manifest["anchors"].append(second)
        self.assert_error("DRAFT provider imported directly or transitively")

    def test_declared_implementation_must_be_imported(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry", "import Mathlib"))
        self.assert_error("does not import declared implementation")

    def test_wrong_export_fails(self):
        self.manifest["anchors"][0]["export"] = "Project.wrongName"
        self.assert_error("does not match fully qualified export")

    def test_wrong_namespace_fails(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry").replace("namespace Project", "namespace Wrong", 1))
        self.assert_error("does not match fully qualified export")

    def test_extra_public_declaration_fails(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry") + "theorem extra : True := True.intro\n")
        self.assert_error("exactly one top-level declaration total")

    def test_private_declaration_fails(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry") + "private def hidden : Nat := 0\n")
        self.assert_error("exactly one top-level declaration total")

    def test_same_line_attribute_prefixed_declaration_fails(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by sorry") + "@[simp] theorem extra : True := True.intro\n")
        self.assert_error("exactly one top-level declaration total")

    def test_extra_proof_surface_commands_fail(self):
        for command in ("axiom extraAxiom : True", "constant extraConstant : Prop",
                        "instance : Inhabited Nat := ⟨0⟩", "example : True := True.intro"):
            with self.subTest(command=command):
                self.write("Project/Frozen/Target.lean", self.anchor("by sorry") + command + "\n")
                self.assert_error("exactly one top-level declaration total")

    def test_ordinary_file_admit_fails(self):
        self.write("Project/Ordinary.lean", "theorem ordinary : True := by admit\n")
        self.assert_error("unauthorized `admit`")

    def test_project_owned_axiom_and_constant_fail(self):
        for command, needle in (("axiom badAxiom : True", "`axiom`"),
                                ("@[deprecated] constant badConstant : Prop", "`constant`")):
            with self.subTest(command=command):
                self.write("Project/Ordinary.lean", command + "\n")
                self.assert_error(needle + " command is forbidden")

    def test_legitimate_seal_changes_body_only(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by exact Project.Internal.internalTarget"))
        self.manifest["anchors"][0]["state"] = "SEALED"
        self.assertEqual(self.check_manifest(), [])

    def test_nonexistent_implementation_export_rejected(self):
        self.manifest["anchors"][0]["implementation"]["export"] = "Project.Internal.missing"
        self.write("Project/Frozen/Target.lean", self.anchor("by exact Project.Internal.missing"))
        self.manifest["anchors"][0]["state"] = "SEALED"
        self.assert_error("implementation export is not declared exactly once")

    def test_wrong_namespace_implementation_export_rejected(self):
        self.write("Project/Internal/Target.lean", "namespace Wrong.Internal\ntheorem internalTarget : True := True.intro\nend Wrong.Internal\n")
        self.write("Project/Frozen/Target.lean", self.anchor("by exact Project.Internal.internalTarget"))
        self.manifest["anchors"][0]["state"] = "SEALED"
        self.assert_error("implementation export is not declared exactly once")

    def test_unrelated_short_seal_rejected(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by exact True.intro"))
        self.manifest["anchors"][0]["state"] = "SEALED"
        self.assert_error("exactly implementation.export")

    def test_long_seal_rejected(self):
        self.write("Project/Frozen/Target.lean", self.anchor("by\n  exact Project.Internal.internalTarget\n  exact Project.Internal.internalTarget\n  exact Project.Internal.internalTarget"))
        self.manifest["anchors"][0]["state"] = "SEALED"
        self.assert_error("exceeds configured")

    def test_definition_drift_fails(self):
        self.write("Project/Frozen/Definition.lean", "def frozenDefinition : Nat := 2\n")
        self.assert_error("semantic definition hash drift")

    def test_crlf_byte_identity_passes(self):
        for name in ("Project/Internal/Target.lean", "Project/Frozen/Definition.lean",
                     "Project/Frozen/Target.lean"):
            path = self.root / name
            self.write_bytes(name, path.read_bytes().replace(b"\n", b"\r\n"))
        self.manifest = self.valid_manifest()
        self.assertEqual(self.check_manifest(), [])

    def test_crlf_to_lf_theorem_drift_fails(self):
        path = self.root / "Project/Frozen/Target.lean"
        self.write_bytes("Project/Frozen/Target.lean", path.read_bytes().replace(b"\n", b"\r\n"))
        self.manifest = self.valid_manifest()
        self.write_bytes("Project/Frozen/Target.lean", path.read_bytes().replace(b"\r\n", b"\n"))
        self.assert_error("prefix hash drift")

    def test_crlf_to_lf_definition_drift_fails(self):
        path = self.root / "Project/Frozen/Definition.lean"
        self.write_bytes("Project/Frozen/Definition.lean", path.read_bytes().replace(b"\n", b"\r\n"))
        self.manifest = self.valid_manifest()
        self.write_bytes("Project/Frozen/Definition.lean", path.read_bytes().replace(b"\r\n", b"\n"))
        errors = self.check_manifest()
        self.assertTrue(any("whole-file definition anchor hash drift" in error for error in errors), errors)
        self.assertTrue(any("semantic definition hash drift" in error for error in errors), errors)

    def test_bad_baseline_format_fails_closed(self):
        self.manifest["anchors"][0]["abi_sha256"] = "BAD"
        self.assert_error("64 lowercase")

    def test_split_policy_is_required(self):
        del self.manifest["anchors"][0]["split_policy"]
        self.assert_error("schema has missing or unauthorized fields")

    def test_independent_split_requires_two_entries(self):
        policy = self.manifest["anchors"][0]["split_policy"]
        policy.update({"source_group": "paper.split", "mode": "INDEPENDENT_BY_AUTHOR", "ruling_ref": "split-ruling"})
        self.assert_error("INDEPENDENT_BY_AUTHOR requires at least two entries")

    def test_independent_split_with_shared_ruling_passes(self):
        for anchor in self.manifest["anchors"]:
            anchor["split_policy"] = {"source_group": "paper.split", "mode": "INDEPENDENT_BY_AUTHOR", "ruling_ref": "split-ruling"}
        self.assertEqual(self.check_manifest(), [])

    def test_independent_split_requires_same_ruling(self):
        self.manifest["anchors"][0]["split_policy"] = {"source_group": "paper.split", "mode": "INDEPENDENT_BY_AUTHOR", "ruling_ref": "ruling-a"}
        self.manifest["anchors"][1]["split_policy"] = {"source_group": "paper.split", "mode": "INDEPENDENT_BY_AUTHOR", "ruling_ref": "ruling-b"}
        self.assert_error("same nonempty ruling_ref")

    def test_not_split_cannot_have_multiple_anchor_entries(self):
        self.manifest["anchors"][1]["split_policy"] = dict(self.manifest["anchors"][0]["split_policy"])
        self.assert_error("NOT_SPLIT requires one joint constitutional anchor")


if __name__ == "__main__":
    unittest.main()
