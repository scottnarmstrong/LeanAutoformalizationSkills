"""Installation checks use isolated directories and never touch personal skills."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("install_skills", Path(__file__).resolve().parents[1] / "scripts/install_skills.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        for name in ("first", "second"):
            skill = self.source / name
            (skill / "scripts").mkdir(parents=True)
            (skill / "SKILL.md").write_text("instructions")
            (skill / "scripts/helper.py").write_text("print('helper')")
        self.destination = self.root / "installed"

    def test_entire_resource_tree_is_available_and_reinstall_is_idempotent(self):
        self.assertEqual(installer.install(self.source, self.destination), 2)
        link = self.destination / "first"
        self.assertTrue(link.is_symlink())
        self.assertEqual((link / "scripts/helper.py").read_text(), "print('helper')")
        self.assertEqual(installer.install(self.source, self.destination), 2)

    def test_collision_aborts_before_creating_any_links(self):
        existing = self.destination / "second"
        existing.mkdir(parents=True)
        (existing / "SKILL.md").write_text("existing instructions")
        with self.assertRaises(ValueError):
            installer.install(self.source, self.destination)
        self.assertFalse((self.destination / "first").exists())
        self.assertEqual((existing / "SKILL.md").read_text(), "existing instructions")

    def test_broken_symlink_is_also_a_collision(self):
        self.destination.mkdir()
        (self.destination / "second").symlink_to(self.root / "missing")
        with self.assertRaises(ValueError):
            installer.install(self.source, self.destination)
        self.assertFalse((self.destination / "first").exists())

    def test_dry_run_creates_nothing(self):
        self.assertEqual(installer.install(self.source, self.destination, dry_run=True), 2)
        self.assertFalse(self.destination.exists())

    def test_creation_failure_rolls_back_only_new_links(self):
        real_symlink = Path.symlink_to
        def failing_symlink(path, target, **kwargs):
            if path.name == "second":
                raise OSError("simulated unsupported symlink")
            return real_symlink(path, target, **kwargs)
        with patch.object(Path, "symlink_to", failing_symlink):
            with self.assertRaises(OSError):
                installer.install(self.source, self.destination)
        self.assertEqual(list(self.destination.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
