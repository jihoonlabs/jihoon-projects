import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from read_context import CONFIG_PATH, read_context


class ContextTests(unittest.TestCase):
    def run_config(self, **changes):
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        config.update(changes)

        # 상대 경로 기준을 유지하기 위해 원래 설정 옆에 임시 파일을 둔다.
        with tempfile.TemporaryDirectory(dir=CONFIG_PATH.parent) as folder:
            path = Path(folder) / "target.json"
            config["repository_root"] = str(
                (CONFIG_PATH.parent / config["repository_root"]).resolve()
            )
            path.write_text(json.dumps(config), encoding="utf-8")
            return read_context(path)

    def test_normal(self):
        context = self.run_config()
        self.assertIn("--- AGENTS.md ---", context)
        self.assertIn(
            "--- docs/personal-game-ai/personal-game-ai-context-router.md ---",
            context,
        )
        self.assertNotIn("--- docs/personal-game-ai/personal-game-ai.md ---", context)

    def test_branch_document_is_derived_from_current_branch(self):
        with self.assertRaises(FileNotFoundError):
            self.run_config(expected_branch="feature/personal-game-ai-missing-context")

    def test_wrong_branch(self):
        with self.assertRaises(RuntimeError):
            self.run_config(expected_branch="test/intentionally-wrong")

    def test_child_branch_is_allowed_by_ancestry(self):
        real_run = __import__("subprocess").run

        def run_with_child(command, *args, **kwargs):
            if command[:3] == ["git", "branch", "--show-current"]:
                return __import__("subprocess").CompletedProcess(
                    command, 0, stdout="feature/personal-game-ai-child\n", stderr=""
                )
            if command[:3] == ["git", "merge-base", "--is-ancestor"]:
                return __import__("subprocess").CompletedProcess(
                    command, 0, stdout="", stderr=""
                )
            return real_run(command, *args, **kwargs)

        with patch("read_context.subprocess.run", side_effect=run_with_child):
            self.assertIn("--- AGENTS.md ---", self.run_config())

    def test_unrelated_branch_is_rejected_by_ancestry(self):
        real_run = __import__("subprocess").run

        def run_with_unrelated_branch(command, *args, **kwargs):
            if command[:3] == ["git", "branch", "--show-current"]:
                return __import__("subprocess").CompletedProcess(
                    command, 0, stdout="feature/unrelated\n", stderr=""
                )
            if command[:3] == ["git", "merge-base", "--is-ancestor"]:
                return __import__("subprocess").CompletedProcess(
                    command, 1, stdout="", stderr=""
                )
            return real_run(command, *args, **kwargs)

        with patch("read_context.subprocess.run", side_effect=run_with_unrelated_branch):
            with self.assertRaises(RuntimeError):
                self.run_config()

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            self.run_config(code_files=["__missing_test__.py"])

    def test_parent_path(self):
        with self.assertRaises(ValueError):
            self.run_config(code_files=["../outside.py"])

    def test_absolute_path(self):
        with self.assertRaises(ValueError):
            self.run_config(code_files=["/tmp/outside.py"])

    def test_extra_document(self):
        with self.assertRaises(ValueError):
            self.run_config(code_files=["docs/personal-game-ai/EPIC.md"])

    def test_invalid_project(self):
        with self.assertRaises(ValueError):
            self.run_config(project="../personal-game-ai")

    def test_duplicate(self):
        with self.assertRaises(ValueError):
            self.run_config(code_files=["AGENTS.md"])

    def test_size_limit(self):
        with self.assertRaises(ValueError):
            self.run_config(max_context_chars=10)

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.run_config(max_context_chars=True)


if __name__ == "__main__":
    unittest.main()