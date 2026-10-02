import json
import tempfile
import unittest
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
        self.assertIn("--- AGENTS.md ---", self.run_config())

    def test_wrong_branch(self):
        with self.assertRaises(RuntimeError):
            self.run_config(expected_branch="test/intentionally-wrong")

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