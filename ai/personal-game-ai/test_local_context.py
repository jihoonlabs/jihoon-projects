import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from read_context import read_context


class LocalContextTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init", "-b", "feature/context")
        (self.root / "AGENTS.md").write_text("common rules")
        self.doc = self.root / "docs/personal-game-ai/LOCAL.md"
        self.doc.parent.mkdir(parents=True)
        self.doc.write_text("<!-- personal-game-ai-branch: feature/context -->\ncontract")
        (self.root / ".gitignore").write_text("/docs/personal-game-ai/LOCAL.md\n")
        self.config = self.root / "target.json"
        self.settings = dict(repository_root=".", expected_branch="feature/context",
                             branch_document="docs/personal-game-ai/LOCAL.md",
                             branch_document_policy="local", code_files=[],
                             max_context_chars=12000)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              capture_output=True, text=True)

    def read(self):
        self.config.write_text(json.dumps(self.settings))
        return read_context(self.config)

    def test_own_document_only(self):
        self.doc.with_name("SIBLING.md").write_text("sibling-secret")
        self.assertIn("contract", self.read())
        self.assertNotIn("sibling-secret", self.read())

    def test_wrong_owner(self):
        self.doc.write_text("<!-- personal-game-ai-branch: feature/sibling -->\n")
        with self.assertRaisesRegex(RuntimeError, "소속"):
            self.read()

    def test_tracked_document(self):
        self.git("add", "-f", "--", str(self.doc.relative_to(self.root)))
        with self.assertRaisesRegex(RuntimeError, "추적"):
            self.read()

    def test_missing_ignore(self):
        (self.root / ".gitignore").write_text("")
        with self.assertRaisesRegex(RuntimeError, "제외 설정"):
            self.read()

    def test_missing_document(self):
        self.doc.unlink()
        with self.assertRaises(FileNotFoundError):
            self.read()

    def test_extra_md(self):
        self.settings["code_files"] = ["docs/personal-game-ai/SIBLING.md"]
        self.doc.with_name("SIBLING.md").write_text("other")
        with self.assertRaisesRegex(ValueError, "추가 MD"):
            self.read()

    def test_legacy_still_supported(self):
        self.settings.pop("branch_document_policy")
        self.doc.write_text("legacy contract")
        self.assertIn("legacy contract", self.read())

    def test_symlink_rejected(self):
        other = self.doc.with_name("OTHER.md")
        other.write_text(self.doc.read_text())
        self.doc.unlink()
        self.doc.symlink_to(other)
        with self.assertRaises(ValueError):
            self.read()

    def test_unknown_policy(self):
        self.settings["branch_document_policy"] = "unknown"
        with self.assertRaises(ValueError):
            self.read()


if __name__ == "__main__":
    unittest.main()
