import json
import unittest

import edit_loop
import run_tasks
import test_edit_loop
import test_run_tasks


class ResumeTests(unittest.TestCase):
    setUp = test_run_tasks.RunnerTests.setUp
    mock = test_run_tasks.RunnerTests.mock
    write_tasks = test_run_tasks.RunnerTests.write_tasks
    read_tasks = test_run_tasks.RunnerTests.read_tasks
    task = test_run_tasks.RunnerTests.task
    block_model = test_run_tasks.RunnerTests.block_model

    def waiting_task(self, task_id="001"):
        task = self.task(task_id, "edit")
        task.update(
            status="waiting_for_user",
            question="Choose?",
            output="outputs/previous",
        )
        return task

    def test_answer_resumes_and_runs_following_task(self):
        self.write_tasks([self.waiting_task(), self.task("002")])
        self.editor.return_value = {
            "status": "tests_passed",
            "output": "outputs/resumed",
            "attempts": 1,
        }
        calls = []

        def model(prompt):
            calls.append(prompt)
            return "following answer"

        run_tasks.run_tasks(
            model, answer_task_id="001", answer="Use the first option."
        )
        tasks = self.read_tasks()
        self.assertEqual(
            [task["status"] for task in tasks],
            ["tests_passed", "response_saved"],
        )
        self.assertEqual(tasks[0]["prompt"], "request-001")
        self.assertEqual(tasks[0]["answers"], [{
            "question": "Choose?",
            "answer": "Use the first option.",
        }])
        request = self.editor.call_args.args[1]
        self.assertIn("request-001", request)
        self.assertIn("Choose?", request)
        self.assertIn("Use the first option.", request)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("question", tasks[0])

        run_tasks.run_tasks(model)
        self.assertEqual(self.editor.call_count, 1)
        self.assertEqual(len(calls), 1)

    def test_repeated_question_preserves_answer_history(self):
        self.write_tasks([self.waiting_task(), self.task("002")])
        self.editor.return_value = {
            "status": "waiting_for_user",
            "output": "outputs/second",
            "question": "Second choice?",
        }
        run_tasks.run_tasks(
            self.block_model, answer_task_id="001", answer="First answer"
        )
        tasks = self.read_tasks()
        self.assertEqual(tasks[0]["question"], "Second choice?")
        self.assertEqual(tasks[1]["status"], "pending")

        self.editor.return_value = {
            "status": "failed",
            "output": "outputs/third",
            "error": "attempt limit",
        }
        run_tasks.run_tasks(
            self.block_model, answer_task_id="001", answer="Second answer"
        )
        tasks = self.read_tasks()
        self.assertEqual(len(tasks[0]["answers"]), 2)
        request = self.editor.call_args.args[1]
        for value in (
            "Choose?", "First answer", "Second choice?", "Second answer"
        ):
            self.assertIn(value, request)
        self.assertEqual(tasks[0]["status"], "failed")
        self.assertEqual(tasks[1]["status"], "pending")

    def test_invalid_answers_leave_task_file_unchanged(self):
        for task_id, answer in (
            ("missing", "Answer"),
            ("001", ""),
            ("001", "   "),
        ):
            with self.subTest(task_id=task_id, answer=answer):
                self.write_tasks([self.waiting_task()])
                before = self.tasks_path.read_bytes()
                with self.assertRaises(ValueError):
                    run_tasks.run_tasks(
                        self.block_model,
                        answer_task_id=task_id,
                        answer=answer,
                    )
                self.assertEqual(self.tasks_path.read_bytes(), before)
                self.assertFalse((self.root / ".run_tasks.lock").exists())
        self.editor.assert_not_called()

    def test_completed_task_cannot_be_answered(self):
        task = self.waiting_task()
        task["status"] = "tests_passed"
        self.write_tasks([task])
        before = self.tasks_path.read_bytes()
        with self.assertRaises(ValueError):
            run_tasks.run_tasks(
                self.block_model, answer_task_id="001", answer="Answer"
            )
        self.assertEqual(self.tasks_path.read_bytes(), before)
        self.editor.assert_not_called()

    def test_git_failure_does_not_save_answer(self):
        self.write_tasks([self.waiting_task()])
        before = self.tasks_path.read_bytes()
        self.prepare.side_effect = RuntimeError("dirty target")
        with self.assertRaises(RuntimeError):
            run_tasks.run_tasks(
                self.block_model, answer_task_id="001", answer="Answer"
            )
        self.assertEqual(self.tasks_path.read_bytes(), before)
        self.editor.assert_not_called()

    def test_another_question_blocks_execution_after_answer_saved(self):
        self.write_tasks([
            self.waiting_task("001"),
            self.waiting_task("002"),
        ])
        run_tasks.run_tasks(
            self.block_model, answer_task_id="001", answer="Answer"
        )
        tasks = self.read_tasks()
        self.assertEqual(tasks[0]["status"], "pending")
        self.assertEqual(tasks[0]["answers"][0]["answer"], "Answer")
        self.assertEqual(tasks[1]["status"], "waiting_for_user")
        self.editor.assert_not_called()

    def test_running_task_blocks_answer_and_execution(self):
        self.write_tasks([
            self.waiting_task(),
            {"id": "002", "status": "running"},
        ])
        before = self.tasks_path.read_bytes()
        run_tasks.run_tasks(
            self.block_model, answer_task_id="001", answer="Answer"
        )
        self.assertEqual(self.tasks_path.read_bytes(), before)
        self.editor.assert_not_called()

    def test_malformed_history_is_rejected(self):
        task = self.waiting_task()
        task["answers"] = [{"question": "Choose?", "answer": ""}]
        self.write_tasks([task])
        with self.assertRaises(ValueError):
            run_tasks.run_tasks(self.block_model)
        self.editor.assert_not_called()


class QuestionRestoreTests(unittest.TestCase):
    setUp = test_edit_loop.EditLoopTests.setUp
    git = test_edit_loop.EditLoopTests.git
    mock = test_edit_loop.EditLoopTests.mock
    proposal = test_edit_loop.EditLoopTests.proposal
    run_edit = test_edit_loop.EditLoopTests.run_edit

    def test_question_after_failed_edit_restores_original(self):
        candidate = "value = 1\n"
        self.model.side_effect = [
            self.proposal(candidate),
            json.dumps({"action": "question", "question": "Choose?"}),
        ]
        self.runner.return_value = (False, "FAILED")

        result = self.run_edit()

        self.assertEqual(result["status"], "waiting_for_user")
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(self.target.read_text(), self.original)
        self.assertEqual(self.test.read_text(), "# fixed test\n")
        output = self.root / result["output"]
        self.assertEqual((output / "candidate_1.py").read_text(), candidate)
        self.assertTrue((output / "answer_2.txt").is_file())
        edit_loop.prepare_edit(
            "sandbox/clamp.py", "Resume.", "test_clamp"
        )

    def test_external_change_before_question_is_preserved(self):
        calls = []

        def model(prompt):
            calls.append(prompt)
            if len(calls) == 1:
                return self.proposal("value = 1\n")
            self.target.write_text("# user edit\n", encoding="utf-8")
            return json.dumps({
                "action": "question",
                "question": "Choose?",
            })

        self.model.side_effect = model
        self.runner.return_value = (False, "FAILED")

        with self.assertRaises(RuntimeError):
            self.run_edit()

        self.assertEqual(self.target.read_text(), "# user edit\n")
        self.assertEqual(self.runner.call_count, 1)
        self.assertFalse((self.root / ".edit_loop.lock").exists())


if __name__ == "__main__":
    unittest.main()