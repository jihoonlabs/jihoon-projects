import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import edit_loop


class EditLoopTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.sandbox = self.root / "sandbox"
        self.sandbox.mkdir()
        self.target = self.sandbox / "clamp.py"
        self.test = self.sandbox / "test_clamp.py"

        self.original = (
            "def clamp(value, minimum, maximum):\n"
            "    raise NotImplementedError\n"
        )
        self.target.write_text(self.original, encoding="utf-8")
        self.test.write_text("# fixed test\n", encoding="utf-8")

        for name, value in (
            ("BASE_DIR", self.root),
            ("SANDBOX", self.sandbox),
        ):
            self.mock(name, new=value)

        self.context = self.mock("read_context", return_value="CONTEXT")
        self.model = self.mock("ask_model")
        self.runner = self.mock("run_test")

        # 実Gitを使い、追跡済みの変更なし状態を用意する。
        self.git("init")
        self.git("add", "sandbox/clamp.py", "sandbox/test_clamp.py")
        self.git(
            "-c", "user.name=Test",
            "-c", "user.email=test@example.invalid",
            "-c", "commit.gpgsign=false",
            "commit", "-m", "fixture",
        )

    def git(self, *args):
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def mock(self, name, **kwargs):
        patcher = patch.object(edit_loop, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def proposal(self, code):
        return json.dumps({"action": "edit", "code": code})

    def run_edit(self):
        return edit_loop.run_edit(
            "sandbox/clamp.py",
            "Implement clamp.",
            "test_clamp",
        )

    def test_success_and_backup(self):
        code = (
            "def clamp(value, minimum, maximum):\n"
            "    return max(minimum, min(value, maximum))\n"
        )
        self.model.return_value = self.proposal(code)
        self.runner.return_value = (True, "7 tests passed")

        result = self.run_edit()

        self.assertEqual(result["status"], "tests_passed")
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(self.target.read_text(), code)
        self.assertEqual(self.test.read_text(), "# fixed test\n")
        self.assertEqual(self.model.call_count, 1)
        output = self.root / result["output"]
        self.assertEqual(
            (output / "original.py").read_text(), self.original
        )
        self.assertEqual(
            json.loads((output / "result.json").read_text()), result
        )
        self.assertFalse((self.root / ".edit_loop.lock").exists())

    def test_failed_test_is_sent_back(self):
        self.model.side_effect = [
            self.proposal("def clamp(v, lo, hi):\n    return v\n"),
            self.proposal(
                "def clamp(v, lo, hi):\n"
                "    return max(lo, min(v, hi))\n"
            ),
        ]
        self.runner.side_effect = [
            (False, "FAILED: below minimum"),
            (True, "passed"),
        ]

        result = self.run_edit()

        self.assertEqual(result["status"], "tests_passed")
        self.assertEqual(result["attempts"], 2)
        second_prompt = self.model.call_args_list[1].args[0]
        self.assertIn("FAILED: below minimum", second_prompt)

    def test_question_stops_without_edit(self):
        self.model.return_value = json.dumps({
            "action": "question",
            "question": "Choose?",
        })

        result = self.run_edit()

        self.assertEqual(result["status"], "waiting_for_user")
        self.assertEqual(result["question"], "Choose?")
        self.assertEqual(self.target.read_text(), self.original)
        self.runner.assert_not_called()

    def test_invalid_response_is_limited_to_three(self):
        self.model.return_value = "not JSON"

        result = self.run_edit()

        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.model.call_count, 3)
        self.runner.assert_not_called()
        self.assertEqual(self.target.read_text(), self.original)

    def test_context_failure_blocks_model(self):
        self.context.side_effect = RuntimeError("wrong branch")
        with self.assertRaises(RuntimeError):
            self.run_edit()
        self.model.assert_not_called()
        self.assertEqual(self.target.read_text(), self.original)

    def test_existing_lock_blocks_model(self):
        lock = self.root / ".edit_loop.lock"
        lock.write_text("existing", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.run_edit()
        self.model.assert_not_called()
        self.assertEqual(lock.read_text(), "existing")

    def test_external_edit_is_preserved(self):
        def model(prompt):
            self.target.write_text("# user edit\n", encoding="utf-8")
            return self.proposal("value = 1\n")

        self.model.side_effect = model
        with self.assertRaises(RuntimeError):
            self.run_edit()
        self.assertEqual(self.target.read_text(), "# user edit\n")
        self.runner.assert_not_called()

    def test_model_error_releases_lock(self):
        self.model.side_effect = RuntimeError("model unavailable")
        with self.assertRaises(RuntimeError):
            self.run_edit()
        self.assertEqual(self.target.read_text(), self.original)
        self.assertFalse((self.root / ".edit_loop.lock").exists())

    def test_dirty_target_blocks_model(self):
        self.target.write_text("# existing edit\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.run_edit()
        self.model.assert_not_called()
        self.assertEqual(self.target.read_text(), "# existing edit\n")

    def test_staged_test_change_blocks_model(self):
        self.test.write_text("# changed test\n", encoding="utf-8")
        self.git("add", "sandbox/test_clamp.py")
        with self.assertRaises(RuntimeError):
            self.run_edit()
        self.model.assert_not_called()

    def test_untracked_target_is_rejected(self):
        other = self.sandbox / "other.py"
        other.write_text("value = 1\n", encoding="utf-8")
        with self.assertRaises(subprocess.CalledProcessError):
            edit_loop.run_edit(
                "sandbox/other.py", "Implement.", "test_clamp"
            )
        self.model.assert_not_called()

    def test_unrelated_changes_are_preserved(self):
        unrelated = self.root / "existing.txt"
        unrelated.write_text("preserve", encoding="utf-8")
        self.model.return_value = json.dumps({
            "action": "question",
            "question": "Choose?",
        })
        result = self.run_edit()
        self.assertEqual(result["status"], "waiting_for_user")
        self.assertEqual(unrelated.read_text(), "preserve")

    def test_invalid_paths_and_modules_are_rejected(self):
        cases = [
            ("../clamp.py", "test_clamp"),
            (str(self.target), "test_clamp"),
            ("sandbox/nested/clamp.py", "test_clamp"),
            ("sandbox/test_clamp.py", "test_clamp"),
            ("sandbox/clamp.py", "../test_clamp"),
            ("sandbox/clamp.py", "clamp"),
        ]
        for target, module in cases:
            with self.subTest(target=target, module=module):
                with self.assertRaises(ValueError):
                    edit_loop.run_edit(target, "Implement.", module)
        self.model.assert_not_called()

    def test_symlink_target_is_rejected(self):
        original = self.sandbox / "original.py"
        self.target.rename(original)
        self.target.symlink_to(original)
        with self.assertRaises(ValueError):
            self.run_edit()
        self.model.assert_not_called()

    def test_fixed_test_change_during_model_call_stops(self):
        def model(prompt):
            self.test.write_text("# external edit\n", encoding="utf-8")
            return self.proposal("value = 1\n")

        self.model.side_effect = model
        with self.assertRaises(RuntimeError):
            self.run_edit()
        self.assertEqual(self.target.read_text(), self.original)
        self.assertEqual(self.test.read_text(), "# external edit\n")
        self.runner.assert_not_called()

    def test_failed_docker_tests_are_limited_to_three(self):
        self.model.return_value = self.proposal("value = 1\n")
        self.runner.return_value = (False, "FAILED")
        result = self.run_edit()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.model.call_count, 3)
        self.assertEqual(self.runner.call_count, 3)

    def test_context_change_after_model_call_stops(self):
        self.context.side_effect = [
            "CONTEXT",
            "CONTEXT",
            "CHANGED",
        ]
        self.model.return_value = self.proposal("value = 1\n")
        with self.assertRaises(RuntimeError):
            self.run_edit()
        self.assertEqual(self.target.read_text(), self.original)
        self.runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()