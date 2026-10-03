import json
import unittest

import create_loop
import edit_loop
import test_edit_loop


class CreateLoopTests(unittest.TestCase):
    setUp = test_edit_loop.EditLoopTests.setUp
    git = test_edit_loop.EditLoopTests.git
    mock = test_edit_loop.EditLoopTests.mock

    @property
    def created(self):
        return self.sandbox / "new_module.py"

    def proposal(self, code="value = 1\n"):
        return json.dumps({"action": "create", "code": code})

    def run_create(self):
        return create_loop.run_create(
            "sandbox/new_module.py", "Create a module.", "test_clamp"
        )

    def test_success_keeps_file_and_records_candidate(self):
        self.model.return_value = self.proposal()
        self.runner.return_value = (True, "passed")

        result = self.run_create()

        self.assertEqual(result["status"], "tests_passed")
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(self.created.read_text(), "value = 1\n")
        self.assertEqual(self.test.read_text(), "# fixed test\n")
        output = self.root / result["output"]
        self.assertEqual((output / "candidate_1.py").read_bytes(),
                         self.created.read_bytes())
        self.assertEqual(json.loads((output / "result.json").read_text()),
                         result)
        self.runner.assert_called_once_with(
            output / "test_1.txt", "test_clamp", work_dir=self.sandbox
        )
        self.assertFalse((self.root / ".edit_loop.lock").exists())

    def test_failed_test_feedback_reaches_next_attempt(self):
        self.model.side_effect = [
            self.proposal("value = 0\n"),
            self.proposal("value = 1\n"),
        ]
        self.runner.side_effect = [(False, "FAILED: wrong value"),
                                   (True, "passed")]

        result = self.run_create()

        self.assertEqual(result["attempts"], 2)
        self.assertEqual(self.created.read_text(), "value = 1\n")
        prompt = self.model.call_args_list[1].args[0]
        self.assertIn("FAILED: wrong value", prompt)
        self.assertIn("value = 0", prompt)

    def test_question_before_creation_leaves_no_file(self):
        self.model.return_value = json.dumps({
            "action": "question", "question": "Choose?"
        })

        result = self.run_create()

        self.assertEqual(result["status"], "waiting_for_user")
        self.assertFalse(self.created.exists())
        self.runner.assert_not_called()

    def test_question_after_failure_removes_candidate_and_can_resume(self):
        self.model.side_effect = [
            self.proposal("value = 0\n"),
            json.dumps({"action": "question", "question": "Choose?"}),
            self.proposal("value = 1\n"),
        ]
        self.runner.side_effect = [(False, "FAILED"), (True, "passed")]

        result = self.run_create()

        self.assertEqual(result["status"], "waiting_for_user")
        self.assertFalse(self.created.exists())
        output = self.root / result["output"]
        self.assertEqual((output / "candidate_1.py").read_text(), "value = 0\n")
        create_loop.prepare_create(
            "sandbox/new_module.py", "Resume.", "test_clamp"
        )
        resumed = self.run_create()
        self.assertEqual(resumed["status"], "tests_passed")

    def test_final_failure_removes_file_but_keeps_candidates(self):
        self.model.return_value = self.proposal()
        self.runner.return_value = (False, "FAILED")

        result = self.run_create()

        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.runner.call_count, 3)
        self.assertFalse(self.created.exists())
        output = self.root / result["output"]
        self.assertTrue((output / "candidate_3.py").is_file())

    def test_invalid_response_is_limited_to_three(self):
        self.model.return_value = "not JSON"

        result = self.run_create()

        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.model.call_count, 3)
        self.runner.assert_not_called()
        self.assertFalse(self.created.exists())

    def test_existing_file_is_preserved(self):
        self.created.write_text("# existing\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_create()
        self.assertEqual(self.created.read_text(), "# existing\n")
        self.model.assert_not_called()

    def test_deleted_tracked_file_is_not_treated_as_new(self):
        self.target.unlink()
        with self.assertRaises(RuntimeError):
            create_loop.run_create(
                "sandbox/clamp.py", "Create.", "test_clamp"
            )
        self.model.assert_not_called()

    def test_ignored_target_is_rejected(self):
        (self.root / ".gitignore").write_text(
            "sandbox/new_module.py\n", encoding="utf-8"
        )
        with self.assertRaises(ValueError):
            self.run_create()
        self.model.assert_not_called()

    def test_dirty_fixed_test_blocks_model(self):
        self.test.write_text("# changed\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.run_create()
        self.model.assert_not_called()

    def test_external_creation_is_preserved(self):
        def model(prompt):
            self.created.write_text("# user file\n", encoding="utf-8")
            return self.proposal()

        self.model.side_effect = model
        with self.assertRaises(RuntimeError):
            self.run_create()
        self.assertEqual(self.created.read_text(), "# user file\n")
        self.runner.assert_not_called()

    def test_external_candidate_change_is_preserved(self):
        def runner(*args, **kwargs):
            self.created.write_text("# user edit\n", encoding="utf-8")
            return False, "FAILED"

        self.model.return_value = self.proposal()
        self.runner.side_effect = runner
        with self.assertRaises(RuntimeError):
            self.run_create()
        self.assertEqual(self.created.read_text(), "# user edit\n")

    def test_same_content_external_replacement_is_preserved(self):
        replacement = self.sandbox / "replacement.py"

        def runner(*args, **kwargs):
            replacement.write_bytes(self.created.read_bytes())
            replacement.replace(self.created)
            return False, "FAILED"

        self.model.return_value = self.proposal()
        self.runner.side_effect = runner
        with self.assertRaises(RuntimeError):
            self.run_create()
        self.assertEqual(self.created.read_text(), "value = 1\n")

    def test_model_exception_after_candidate_removes_own_file(self):
        self.model.side_effect = [
            self.proposal(), RuntimeError("model unavailable")
        ]
        self.runner.return_value = (False, "FAILED")
        with self.assertRaises(RuntimeError):
            self.run_create()
        self.assertFalse(self.created.exists())
        self.assertFalse((self.root / ".edit_loop.lock").exists())

    def test_docker_exception_removes_own_file(self):
        self.model.return_value = self.proposal()
        self.runner.side_effect = RuntimeError("Docker unavailable")
        with self.assertRaises(RuntimeError):
            self.run_create()
        self.assertFalse(self.created.exists())

    def test_shared_edit_lock_blocks_creation(self):
        lock = self.root / ".edit_loop.lock"
        lock.write_text("existing", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.run_create()
        self.assertEqual(lock.read_text(), "existing")
        self.model.assert_not_called()

    def test_invalid_paths_and_modules_are_rejected(self):
        cases = (
            ("../new.py", "test_clamp"),
            ("sandbox/nested/new.py", "test_clamp"),
            ("sandbox/test_new.py", "test_clamp"),
            ("sandbox/new_module.py", "../test_clamp"),
            ("sandbox/new_module.py", "clamp"),
            (str(self.created), "test_clamp"),
        )
        for target, module in cases:
            with self.subTest(target=target, module=module):
                with self.assertRaises(ValueError):
                    create_loop.run_create(target, "Create.", module)
        self.model.assert_not_called()

    def test_symlink_target_is_preserved(self):
        self.created.symlink_to(self.target)
        with self.assertRaises(ValueError):
            self.run_create()
        self.assertTrue(self.created.is_symlink())
        self.model.assert_not_called()


if __name__ == "__main__":
    unittest.main()