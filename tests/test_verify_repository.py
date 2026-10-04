"""Forbidden-reference checks cover exported documents and resources."""

import importlib.util
from pathlib import Path
import re
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("verify_repository", Path(__file__).resolve().parents[1] / "scripts/verify_repository.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class ForbiddenReferenceTests(unittest.TestCase):
    def test_patterns_cover_root_metadata_templates_and_paths_but_not_git(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for rel in ("README.md", "skills/example/agents/openai.yaml",
                        "skills/example/assets/template.json", "HiddenCampaign/notes.md",
                        ".gitignore", "policy", "Fixture.lean", "source.tex", "helper.sh",
                        ".git/config"):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('HiddenCampaign')
            findings = verifier.validate(root, (re.compile('HiddenCampaign', re.I),))
            forbidden = [item for item in findings if 'forbidden pattern' in item]
            self.assertTrue(any('README.md:1' in item for item in forbidden))
            self.assertTrue(any('openai.yaml:1' in item for item in forbidden))
            self.assertTrue(any('template.json:1' in item for item in forbidden))
            for rel in ('.gitignore', 'policy', 'Fixture.lean', 'source.tex', 'helper.sh'):
                self.assertTrue(any(f'{rel}:1' in item for item in forbidden), rel)
            self.assertTrue(any('in path: HiddenCampaign/' in item for item in forbidden))
            self.assertFalse(any('.git/' in item for item in forbidden))


if __name__ == '__main__':
    unittest.main()
