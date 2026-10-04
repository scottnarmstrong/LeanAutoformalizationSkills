import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "check_lean_modules.py"
SPEC = importlib.util.spec_from_file_location("check_lean_modules", SCRIPT)
checker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(checker)

HEADER = "/-\nCopyright (c) 2026 A. All rights reserved.\n-/\n"
CHALLENGE = (HEADER + "module\n\npublic import Mathlib.Data.Real.Basic\n\n/-! # Challenge -/\n\n"
             "@[expose] public section\n\nnamespace Demo\n\n"
             "theorem main : True := by\n  sorry\n\nend Demo\n\nend\n")
SOLUTION = CHALLENGE.replace("  sorry", "  trivial")


class CheckLeanModulesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.write("Demo/Basic.lean", HEADER + "module\n\npublic import Mathlib\n\npublic section\n\n"
                   "namespace Demo\ntheorem basic : True := trivial\nend Demo\n\nend\n")
        self.write("lakefile.lean", "import Lake\nopen Lake DSL\n")
        self.write("comparators/Challenge.lean", CHALLENGE)
        self.write("comparators/Solution.lean", SOLUTION)
        self.config = {"challenge_module": "comparators.Challenge", "solution_module": "comparators.Solution",
                       "theorem_names": ["Demo.main"], "definition_names": [],
                       "permitted_axioms": ["propext", "Classical.choice", "Quot.sound"], "enable_nanoda": True}
        self.write("comparator.json", json.dumps(self.config))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def run_checker(self, *extra):
        out = io.StringIO()
        with redirect_stdout(out):
            status = checker.main(["--root", str(self.root), *extra])
        return status, out.getvalue()

    def assert_fails(self, needle, *extra):
        status, output = self.run_checker(*extra)
        self.assertEqual(status, 1, output)
        self.assertIn(needle, output)

    def test_valid_tree_passes(self):
        status, output = self.run_checker()
        self.assertEqual(status, 0, output)
        self.assertIn("PASS (4 Lean files, 1 comparator configurations)", output)

    def test_header_forms(self):
        cases = {
            "module\n": True,
            "-- line comment\nmodule\n": True,
            "/- outer /- nested -/ still comment -/\nmodule\n": True,
            "﻿module\n": True,
            "import Mathlib\n": False,
            "/-! module doc -/\nmodule\n": False,
            "/-- doc comment -/\nmodule\n": False,
            "modules\n": False,
            "module.foo\n": False,
            "": False,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(checker.has_module_header(text), expected)

    def test_non_module_file_fails(self):
        self.write("Demo/Legacy.lean", HEADER + "import Mathlib\n\ntheorem legacy : True := trivial\n")
        self.assert_fails("Demo/Legacy.lean: not a module")

    def test_module_doc_before_header_fails(self):
        self.write("Demo/Doc.lean", "/-! # Title -/\nmodule\n")
        self.assert_fails("Demo/Doc.lean: not a module")

    def test_lakefile_is_exempt(self):
        status, output = self.run_checker()
        self.assertNotIn("lakefile.lean", output)
        self.assertEqual(status, 0, output)

    def test_line_cap(self):
        self.write("Demo/Long.lean", "module\n" + "-- line\n" * 20)
        self.assert_fails("Demo/Long.lean: 21 lines exceeds 10", "--max-lines", "10")

    def test_symlinked_lean_file_fails(self):
        os.symlink(self.root / "Demo/Basic.lean", self.root / "Demo/Link.lean")
        self.assert_fails("Demo/Link.lean: symlinked .lean file")

    def test_lake_directory_is_not_scanned(self):
        self.write(".lake/packages/dep/Legacy.lean", "import Mathlib\n")
        status, output = self.run_checker()
        self.assertEqual(status, 0, output)

    def test_import_only_aggregator(self):
        self.assertTrue(checker.is_import_only(
            HEADER + "module\n\npublic import A.B\npublic meta import C\nimport all D\n\n"
            "/-! # Aggregator -/\n\n@[expose] public section\n\nopen Demo\n\nend\n"))
        self.assertFalse(checker.is_import_only("module\n\npublic import A\n\ndef x : Nat := 0\n"))
        self.assertFalse(checker.is_import_only("module\n\n-- no imports\n"))

    def test_import_forms(self):
        text = "module\npublic import A.B\nmeta import C\npublic meta import D\nimport all E\nimport F\n-- import G\n"
        self.assertEqual(checker.IMPORT.findall(checker.code_mask(text)), ["A.B", "C", "D", "E", "F"])

    def test_declaration_names_and_visibility(self):
        text = ("module\n\nnamespace A\n\ndef hidden : Nat := 0\n\npublic def shown : Nat := 0\n\n"
                "@[expose] public section\n\nnamespace B\n\ntheorem t : True := trivial\n\n"
                "private theorem p : True := trivial\n\ntheorem _root_.Other.r : True := trivial\n\n"
                "end B\n\nsection\n\n@[simp] lemma inner : True := trivial\n\nend\n\nend\n\n"
                "theorem after : True := trivial\n\nend A\n")
        self.assertEqual(checker.declarations(text), [
            ("def", "A.hidden", False), ("def", "A.shown", True), ("theorem", "A.B.t", True),
            ("theorem", "A.B.p", False), ("theorem", "Other.r", True), ("lemma", "A.inner", True),
            ("theorem", "A.after", False)])

    def test_reviewed_lexer_edge_cases(self):
        text = ("module\n\n@[expose] public section\n\nnamespace X\n\nsection A.B\n\ndef c : Char := '\"'\n\n"
                "end A.B\n\nopen Nat in theorem b : True := trivial\n\n"
                "set_option linter.unusedVariables false in\ntheorem «a b» : True := trivial\n\nend X\n\nend\n")
        self.assertEqual(checker.declarations(text), [
            ("def", "X.c", True), ("theorem", "X.b", True), ("theorem", "X.«a b»", True)])

    def test_files_outside_root_and_undecodable_files_are_reported(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        stray = Path(outside.name) / "Stray.lean"
        stray.write_text("import Mathlib\n")
        self.assert_fails("Stray.lean: not a module", "--files", str(stray))
        (self.root / "Demo/Bytes.lean").write_bytes(b"module\n\xff\xfe\n")
        self.assert_fails("Demo/Bytes.lean: unreadable")

    def test_non_module_declarations_are_exported(self):
        self.assertEqual(checker.declarations("namespace A\ntheorem t : True := trivial\nend A\n"),
                         [("theorem", "A.t", True)])

    def test_comparator_nonstandard_axiom_fails(self):
        self.config["permitted_axioms"].append("sorryAx")
        self.write("comparator.json", json.dumps(self.config))
        self.assert_fails("permitted_axioms must name only")

    def test_comparator_requires_nanoda(self):
        self.config["enable_nanoda"] = False
        self.write("comparator.json", json.dumps(self.config))
        self.assert_fails("enable_nanoda must be true")

    def test_comparator_missing_theorem_fails(self):
        self.config["theorem_names"].append("Demo.absent")
        self.write("comparator.json", json.dumps(self.config))
        self.assert_fails("does not declare public theorem Demo.absent")

    def test_comparator_private_theorem_fails(self):
        self.write("comparators/Solution.lean", SOLUTION.replace("theorem main", "private theorem main"))
        self.assert_fails("solution_module comparators.Solution does not declare public theorem Demo.main")

    def test_comparator_missing_module_fails(self):
        self.config["solution_module"] = "comparators.Absent"
        self.write("comparator.json", json.dumps(self.config))
        self.assert_fails("solution_module comparators.Absent has no file")

    def test_challenge_size_limits(self):
        self.write("comparators/Challenge.lean", CHALLENGE + "-- padding\n" * 400)
        status, output = self.run_checker()
        self.assertEqual(status, 0, output)
        self.assertIn("review threshold", output)
        self.write("comparators/Challenge.lean", CHALLENGE + "-- padding\n" * 1000)
        self.assert_fails("limit 1000 lines")

    def test_files_mode_skips_comparators(self):
        self.config["enable_nanoda"] = False
        self.write("comparator.json", json.dumps(self.config))
        status, output = self.run_checker("--files", "Demo/Basic.lean")
        self.assertEqual(status, 0, output)
        self.assertIn("1 Lean files, 0 comparator configurations", output)


if __name__ == "__main__":
    unittest.main()
