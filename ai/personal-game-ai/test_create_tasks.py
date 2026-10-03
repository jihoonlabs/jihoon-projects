import unittest

import run_tasks
import test_run_tasks


class CreateTaskTests(unittest.TestCase):
    mock = test_run_tasks.RunnerTests.mock
    write_tasks = test_run_tasks.RunnerTests.write_tasks
    read_tasks = test_run_tasks.RunnerTests.read_tasks
    block_model = test_run_tasks.RunnerTests.block_model

    def setUp(self):
        test_run_tasks.RunnerTests.setUp(self)
        self.create_prepare = self.mock("prepare_create")
        self.creator = self.mock("run_create")

    def task(self, task_id="001", status="pending"):
        task = {
            "id": task_id,
            "status": status,
            "kind": "create",
            "target": "sandbox/new_module.py",
            "test_module": "test_new_module",
            "prompt": "Create the requested module.",
        }
        if status == "waiting_for_user":
            task["question"] = "Choose?"
        return task

    def success(self):
        self.creator.return_value = {
            "status": "tests_passed",
            "output": "outputs/create_example",
            "attempts": 1,
        }

    def test_create_success_is_saved_and_not_repeated(self):
        self.write_tasks([self.task()])
        self.success()

        run_tasks.run_tasks(self.block_model)

        self.creator.assert_called_once_with(
            "sandbox/new_module.py",
            "Create the requested module.",
            "test_new_module",
            model=self.block_model,
        )
        self.editor.assert_not_called()
        self.prepare.assert_not_called()
        self.assertEqual(self.read_tasks()[0]["status"], "tests_passed")

        run_tasks.run_tasks(self.block_model)
        self.assertEqual(self.creator.call_count, 1)

    def test_preflight_failure_blocks_all_pending_tasks(self):
        self.write_tasks([
            {"id": "text", "status": "pending", "kind": "text",
             "prompt": "Following task."},
            self.task(),
        ])
        self.create_prepare.side_effect = ValueError("already exists")

        with self.assertRaises(ValueError):
            run_tasks.run_tasks(self.block_model)

        self.assertEqual(
            [task["status"] for task in self.read_tasks()],
            ["pending", "pending"],
        )
        self.creator.assert_not_called()

    def test_question_stops_following_task(self):
        self.write_tasks([
            self.task(),
            {"id": "next", "status": "pending", "kind": "text",
             "prompt": "Following task."},
        ])
        self.creator.return_value = {
            "status": "waiting_for_user",
            "output": "outputs/question",
            "question": "Choose?",
        }

        run_tasks.run_tasks(self.block_model)

        self.assertEqual(
            [task["status"] for task in self.read_tasks()],
            ["waiting_for_user", "pending"],
        )

    def test_answer_resumes_create_and_runs_following_task(self):
        self.write_tasks([
            self.task(status="waiting_for_user"),
            {"id": "next", "status": "pending", "kind": "text",
             "prompt": "Following task."},
        ])
        self.success()

        run_tasks.run_tasks(
            lambda prompt: "Following answer.",
            answer_task_id="001",
            answer="Use option one.",
        )

        tasks = self.read_tasks()
        self.assertEqual(
            [task["status"] for task in tasks],
            ["tests_passed", "response_saved"],
        )
        self.assertEqual(tasks[0]["answers"], [{
            "question": "Choose?", "answer": "Use option one."
        }])
        request = self.creator.call_args.args[1]
        for text in (
            "Create the requested module.", "Choose?", "Use option one."
        ):
            self.assertIn(text, request)
        self.prepare.assert_not_called()

    def test_failed_resume_check_does_not_save_answer(self):
        self.write_tasks([self.task(status="waiting_for_user")])
        before = self.tasks_path.read_bytes()
        self.create_prepare.side_effect = ValueError("external file")

        with self.assertRaises(ValueError):
            run_tasks.run_tasks(
                self.block_model, answer_task_id="001", answer="Answer"
            )

        self.assertEqual(self.tasks_path.read_bytes(), before)
        self.creator.assert_not_called()

    def test_repeated_question_keeps_answer_history(self):
        self.write_tasks([self.task(status="waiting_for_user")])
        self.creator.return_value = {
            "status": "waiting_for_user",
            "output": "outputs/second_question",
            "question": "Second choice?",
        }
        run_tasks.run_tasks(
            self.block_model, answer_task_id="001", answer="First answer"
        )

        self.success()
        run_tasks.run_tasks(
            self.block_model, answer_task_id="001", answer="Second answer"
        )

        task = self.read_tasks()[0]
        self.assertEqual(len(task["answers"]), 2)
        self.assertEqual(task["status"], "tests_passed")
        request = self.creator.call_args.args[1]
        for text in (
            "Choose?", "First answer", "Second choice?", "Second answer"
        ):
            self.assertIn(text, request)

    def test_create_failure_stops_following_task(self):
        self.write_tasks([
            self.task(),
            {"id": "next", "status": "pending", "kind": "text",
             "prompt": "Following task."},
        ])
        self.creator.return_value = {
            "status": "failed",
            "output": "outputs/failed",
            "error": "attempt limit",
        }

        run_tasks.run_tasks(self.block_model)

        self.assertEqual(
            [task["status"] for task in self.read_tasks()],
            ["failed", "pending"],
        )

    def test_create_exception_is_saved_and_releases_runner_lock(self):
        self.write_tasks([self.task()])
        self.creator.side_effect = RuntimeError("external change")

        with self.assertRaises(RuntimeError):
            run_tasks.run_tasks(self.block_model)

        task = self.read_tasks()[0]
        self.assertEqual(task["status"], "failed")
        self.assertEqual(task["error"], "external change")
        self.assertFalse((self.root / ".run_tasks.lock").exists())

    def test_another_question_blocks_execution_after_answer_saved(self):
        self.write_tasks([
            self.task(status="waiting_for_user"),
            self.task("002", status="waiting_for_user"),
        ])

        run_tasks.run_tasks(
            self.block_model, answer_task_id="001", answer="Answer"
        )

        tasks = self.read_tasks()
        self.assertEqual(tasks[0]["status"], "pending")
        self.assertEqual(tasks[1]["status"], "waiting_for_user")
        self.creator.assert_not_called()

    def test_running_task_blocks_answer_save(self):
        self.write_tasks([
            self.task(status="waiting_for_user"),
            {"id": "running", "status": "running"},
        ])
        before = self.tasks_path.read_bytes()

        run_tasks.run_tasks(
            self.block_model, answer_task_id="001", answer="Answer"
        )

        self.assertEqual(self.tasks_path.read_bytes(), before)
        self.create_prepare.assert_not_called()
        self.creator.assert_not_called()

    def test_missing_create_configuration_is_rejected(self):
        for key in ("target", "test_module"):
            with self.subTest(key=key):
                task = self.task()
                del task[key]
                self.write_tasks([task])
                with self.assertRaises(ValueError):
                    run_tasks.run_tasks(self.block_model)
        self.creator.assert_not_called()


if __name__ == "__main__":
    unittest.main()