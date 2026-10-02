import json
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

        replacements = {
            "BASE_DIR": self.root,
            "SANDBOX": self.sandbox,
            "TARGET": self.target,
            "TEST": self.test,
        }
        for name, value in replacements.items():
            patcher = patch.object(edit_loop, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.context = self.mock("read_context", return_value="CONTEXT")
        self.model = self.mock("ask_model")
        self.runner = self.mock("run_test")

    def mock(self, name, **kwargs):
        patcher = patch.object(edit_loop, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def proposal(self, code):
        return json.dumps({"action": "edit", "code": code})

    def test_success_and_backup(self):
        code = (
            "def clamp(value, minimum, maximum):\n"
            "    return max(minimum, min(value, maximum))\n"
        )
        self.model.return_value = self.proposal(code)
        self.runner.return_value = (True, "7 tests passed")

        edit_loop.main()

        self.assertEqual(self.target.read_text(), code)
        self.assertEqual(self.test.read_text(), "# fixed test\n")
        self.assertEqual(self.model.call_count, 1)
        backups = list((self.root / "outputs").glob("*/original.py"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), self.original)
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

        edit_loop.main()

        self.assertEqual(self.model.call_count, 2)
        second_prompt = self.model.call_args_list[1].args[0]
        self.assertIn("FAILED: below minimum", second_prompt)

    def test_question_stops_without_edit(self):
        self.model.return_value = json.dumps({
            "action": "question",
            "question": "어떤 동작을 원하시나요?",
        })

        edit_loop.main()

        self.assertEqual(self.target.read_text(), self.original)
        self.runner.assert_not_called()
        self.assertEqual(self.model.call_count, 1)

    def test_invalid_response_is_limited_to_three(self):
        self.model.return_value = "not JSON"

        edit_loop.main()

        self.assertEqual(self.model.call_count, 3)
        self.runner.assert_not_called()
        self.assertEqual(self.target.read_text(), self.original)

    def test_context_failure_blocks_model(self):
        self.context.side_effect = RuntimeError("wrong branch")

        with self.assertRaises(RuntimeError):
            edit_loop.main()

        self.model.assert_not_called()
        self.assertEqual(self.target.read_text(), self.original)

    def test_existing_lock_blocks_model(self):
        lock = self.root / ".edit_loop.lock"
        lock.write_text("existing", encoding="utf-8")

        with self.assertRaises(RuntimeError):
            edit_loop.main()

        self.model.assert_not_called()
        self.assertEqual(lock.read_text(), "existing")

    def test_external_edit_is_preserved(self):
        def model(prompt):
            self.target.write_text("# user edit\n", encoding="utf-8")
            return self.proposal("value = 1\n")

        self.model.side_effect = model

        with self.assertRaises(RuntimeError):
            edit_loop.main()

        self.assertEqual(self.target.read_text(), "# user edit\n")
        self.runner.assert_not_called()

    def test_model_error_releases_lock(self):
        self.model.side_effect = RuntimeError("model unavailable")

        with self.assertRaises(RuntimeError):
            edit_loop.main()

        self.assertEqual(self.target.read_text(), self.original)
        self.assertFalse((self.root / ".edit_loop.lock").exists())


if __name__ == "__main__":
    unittest.main()