import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_tasks


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.tasks_path = self.root / "runner_tasks.json"

        for name, value in (
            ("BASE_DIR", self.root),
            ("TASKS_PATH", self.tasks_path),
            ("OUTPUT_DIR", self.root / "outputs"),
            ("RUN_LOG_PATH", self.root / "outputs" / "run_events.jsonl"),
        ):
            self.mock(name, new=value)

        self.context = self.mock(
            "read_context", return_value="TEST_CONTEXT"
        )
        self.prepare = self.mock("prepare_edit")
        self.editor = self.mock("run_edit")

    def mock(self, name, **kwargs):
        patcher = patch.object(run_tasks, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def write_tasks(self, tasks):
        self.tasks_path.write_text(
            json.dumps(tasks), encoding="utf-8"
        )

    def read_tasks(self):
        return json.loads(self.tasks_path.read_text(encoding="utf-8"))

    def task(self, task_id, kind="text"):
        task = {
            "id": task_id,
            "status": "pending",
            "kind": kind,
            "prompt": f"request-{task_id}",
        }
        if kind == "edit":
            task.update(
                target="sandbox/clamp.py",
                test_module="test_clamp",
            )
        return task

    def read_events(self):
        path = self.root / "outputs" / "run_events.jsonl"
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
        ]

    def test_run_events_are_append_only_and_minimal(self):
        self.write_tasks([self.task("001")])
        run_tasks.run_tasks(lambda prompt: "answer")
        first = self.read_events()
        self.assertEqual(
            [(item["task_id"], item["status"]) for item in first],
            [("001", "running"), ("001", "response_saved")],
        )
        self.assertEqual(
            set(first[0]), {"timestamp", "task_id", "status"}
        )

        self.write_tasks([self.task("002")])
        run_tasks.run_tasks(lambda prompt: "answer")
        second = self.read_events()
        self.assertEqual(first, second[:2])
        self.assertEqual(
            [(item["task_id"], item["status"]) for item in second[2:]],
            [("002", "running"), ("002", "response_saved")],
        )

    def test_failed_task_records_failure(self):
        self.write_tasks([self.task("001")])
        run_tasks.run_tasks(
            lambda prompt: (_ for _ in ()).throw(RuntimeError("failed"))
        )
        self.assertEqual(
            [(item["task_id"], item["status"]) for item in self.read_events()],
            [("001", "running"), ("001", "failed")],
        )

    def test_order_context_and_skip_completed(self):
        self.write_tasks([
            self.task("001"),
            {"id": "002", "status": "response_saved"},
            self.task("003"),
        ])
        calls = []

        def model(prompt):
            calls.append(prompt)
            return "answer"

        run_tasks.run_tasks(model)
        self.assertEqual(len(calls), 2)
        self.assertIn("TEST_CONTEXT", calls[0])
        self.assertIn("request-001", calls[0])
        self.assertIn("request-003", calls[1])
        self.assertEqual(
            [task["status"] for task in self.read_tasks()],
            ["response_saved"] * 3,
        )

        run_tasks.run_tasks(model)
        self.assertEqual(len(calls), 2)

    def test_waiting_and_running_are_not_called(self):
        self.write_tasks([
            {
                "id": "001",
                "status": "waiting_for_user",
                "question": "Choose?",
            },
            {"id": "002", "status": "running"},
        ])
        run_tasks.run_tasks(self.block_model)
        self.assertEqual(
            [task["status"] for task in self.read_tasks()],
            ["waiting_for_user", "running"],
        )

    def block_model(self, prompt):
        self.fail("Model must not be called.")

    def test_model_failure_continues(self):
        self.write_tasks([self.task("001"), self.task("002")])
        calls = []

        def model(prompt):
            calls.append(prompt)
            if len(calls) == 1:
                raise RuntimeError("model failed")
            return "answer"

        run_tasks.run_tasks(model)
        tasks = self.read_tasks()
        self.assertEqual(tasks[0]["status"], "failed")
        self.assertEqual(tasks[0]["error"], "model failed")
        self.assertEqual(tasks[1]["status"], "response_saved")

    def test_python_is_checked_without_execution(self):
        self.write_tasks([self.task("001", "python")])
        run_tasks.run_tasks(
            lambda prompt: '```python\nraise RuntimeError("DO NOT RUN")\n```'
        )
        task = self.read_tasks()[0]
        self.assertEqual(task["status"], "syntax_passed")
        self.assertTrue((self.root / task["code"]).is_file())

    def test_invalid_python_fails(self):
        self.write_tasks([self.task("001", "python")])
        run_tasks.run_tasks(lambda prompt: "```python\ndef broken(\n```")
        self.assertEqual(self.read_tasks()[0]["status"], "failed")

    def test_missing_code_block_fails(self):
        self.write_tasks([self.task("001", "python")])
        run_tasks.run_tasks(lambda prompt: "no code")
        task = self.read_tasks()[0]
        self.assertEqual(task["status"], "failed")
        self.assertTrue((self.root / task["output"]).is_file())

    def test_context_failure_blocks_model(self):
        self.write_tasks([self.task("001")])
        self.context.side_effect = RuntimeError("wrong branch")
        with self.assertRaises(RuntimeError):
            run_tasks.run_tasks(self.block_model)
        self.assertEqual(self.read_tasks()[0]["status"], "pending")

    def test_save_failure_blocks_model(self):
        self.write_tasks([self.task("001")])
        with patch.object(
            run_tasks, "save_tasks", side_effect=OSError("disk failed")
        ):
            with self.assertRaises(OSError):
                run_tasks.run_tasks(self.block_model)
        self.assertFalse((self.root / ".run_tasks.lock").exists())

    def test_duplicate_id_blocks_model(self):
        self.write_tasks([self.task("001"), self.task("001")])
        with self.assertRaises(ValueError):
            run_tasks.run_tasks(self.block_model)

    def test_edit_success_is_saved_and_not_repeated(self):
        self.write_tasks([self.task("001", "edit")])
        self.editor.return_value = {
            "status": "tests_passed",
            "output": "outputs/edit_example",
            "attempts": 2,
        }
        model = self.block_model
        run_tasks.run_tasks(model)
        self.editor.assert_called_once_with(
            "sandbox/clamp.py",
            "request-001",
            "test_clamp",
            model=model,
        )
        task = self.read_tasks()[0]
        self.assertEqual(task["status"], "tests_passed")
        self.assertEqual(task["attempts"], 2)
        self.assertEqual(task["output"], "outputs/edit_example")

        run_tasks.run_tasks(model)
        self.assertEqual(self.editor.call_count, 1)

    def test_edit_question_stops_following_task(self):
        self.write_tasks([
            self.task("001", "edit"),
            self.task("002"),
        ])
        self.editor.return_value = {
            "status": "waiting_for_user",
            "output": "outputs/edit_example",
            "question": "Choose?",
        }
        run_tasks.run_tasks(self.block_model)
        tasks = self.read_tasks()
        self.assertEqual(tasks[0]["status"], "waiting_for_user")
        self.assertEqual(tasks[0]["question"], "Choose?")
        self.assertEqual(tasks[1]["status"], "pending")

        run_tasks.run_tasks(self.block_model)
        self.assertEqual(self.editor.call_count, 1)

    def test_existing_question_blocks_entire_list(self):
        self.write_tasks([
            self.task("001"),
            {
                "id": "002",
                "status": "waiting_for_user",
                "question": "Choose?",
            },
        ])
        run_tasks.run_tasks(self.block_model)
        self.assertEqual(self.read_tasks()[0]["status"], "pending")

    def test_existing_running_blocks_entire_list(self):
        self.write_tasks([
            self.task("001"),
            {"id": "002", "status": "running"},
        ])
        run_tasks.run_tasks(self.block_model)
        self.assertEqual(self.read_tasks()[0]["status"], "pending")

    def test_git_failure_blocks_all_pending_tasks(self):
        self.write_tasks([
            self.task("001"),
            self.task("002", "edit"),
        ])
        self.prepare.side_effect = RuntimeError("dirty target")
        with self.assertRaises(RuntimeError):
            run_tasks.run_tasks(self.block_model)
        self.assertEqual(
            [task["status"] for task in self.read_tasks()],
            ["pending", "pending"],
        )
        self.editor.assert_not_called()

    def test_edit_failure_stops_following_task(self):
        self.write_tasks([
            self.task("001", "edit"),
            self.task("002"),
        ])
        self.editor.return_value = {
            "status": "failed",
            "output": "outputs/edit_example",
            "error": "attempt limit",
        }
        run_tasks.run_tasks(self.block_model)
        self.assertEqual(
            [task["status"] for task in self.read_tasks()],
            ["failed", "pending"],
        )

    def test_edit_exception_is_saved_and_stops(self):
        self.write_tasks([
            self.task("001", "edit"),
            self.task("002"),
        ])
        self.editor.side_effect = RuntimeError("external change")
        with self.assertRaises(RuntimeError):
            run_tasks.run_tasks(self.block_model)
        tasks = self.read_tasks()
        self.assertEqual(tasks[0]["error"], "external change")
        self.assertEqual(tasks[1]["status"], "pending")
        self.assertFalse((self.root / ".run_tasks.lock").exists())

    def test_existing_lock_is_preserved(self):
        lock = self.root / ".run_tasks.lock"
        lock.write_text("existing", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            run_tasks.run_tasks(self.block_model)
        self.assertEqual(lock.read_text(), "existing")

    def test_missing_edit_configuration_is_rejected(self):
        task = self.task("001", "edit")
        del task["test_module"]
        self.write_tasks([task])
        with self.assertRaises(ValueError):
            run_tasks.run_tasks(self.block_model)
        self.editor.assert_not_called()


if __name__ == "__main__":
    unittest.main()