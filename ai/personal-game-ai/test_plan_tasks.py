import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import execute_plan
import plan_tasks
import run_tasks


class PlanTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.target = self.root / "module.py"
        self.test = self.root / "test_module.py"
        self.target.write_text("value = 0\n", encoding="utf-8")
        self.test.write_text("# fixed\n", encoding="utf-8")
        self.allowed = [{
            "kind": "edit",
            "target": "sandbox/module.py",
            "test_module": "test_module",
        }]
        self.task = {
            **self.allowed[0],
            "id": "001",
            "prompt": "Set value to one.",
        }
        for module, name, value in (
            (plan_tasks, "BASE_DIR", self.root),
            (execute_plan, "BASE_DIR", self.root),
        ):
            patcher = patch.object(module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name, value in (
            ("read_context", Mock(return_value="CONTEXT")),
            ("prepare_edit", Mock(return_value=(self.target, self.test))),
        ):
            patcher = patch.object(plan_tasks, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def proposal(self, task=None):
        return json.dumps({"tasks": [self.task if task is None else task]})

    def test_generation_preserves_files_and_normalizes_status(self):
        before = (self.target.read_bytes(), self.test.read_bytes())
        path = plan_tasks.generate_plan(
            "Implement value.", self.allowed,
            model=lambda prompt: self.proposal(),
        )
        tasks = json.loads(path.read_text())
        self.assertEqual(tasks[0]["status"], "pending")
        self.assertIn("Implement value.", tasks[0]["prompt"])
        self.assertEqual(
            before, (self.target.read_bytes(), self.test.read_bytes())
        )

    def test_invalid_json_retries_then_succeeds(self):
        model = Mock(side_effect=["invalid", self.proposal()])
        path = plan_tasks.generate_plan("Goal", self.allowed, model)
        self.assertTrue(path.is_file())
        self.assertEqual(model.call_count, 2)

    def test_outside_target_is_rejected(self):
        task = {**self.task, "target": "sandbox/other.py"}
        with self.assertRaises(ValueError):
            plan_tasks.validate_plan(
                {"tasks": [task]}, self.allowed, "Goal"
            )

    def test_model_cannot_add_status_or_commands(self):
        for key, value in (("status", "tests_passed"), ("command", "echo x")):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    plan_tasks.validate_plan(
                        {"tasks": [{**self.task, key: value}]},
                        self.allowed, "Goal",
                    )

    def test_duplicate_target_is_rejected(self):
        with self.assertRaises(ValueError):
            plan_tasks.validate_options("Goal", self.allowed * 2)

    def test_request_length_is_checked_by_existing_preflight(self):
        plan_tasks.prepare_edit.side_effect = ValueError("too long")
        with self.assertRaises(ValueError):
            plan_tasks.validate_plan(
                {"tasks": [self.task]}, self.allowed, "Goal"
            )

    def test_external_change_stops_without_overwrite(self):
        def model(prompt):
            self.target.write_text("# external\n", encoding="utf-8")
            return self.proposal()

        with self.assertRaises(RuntimeError):
            plan_tasks.generate_plan("Goal", self.allowed, model)
        self.assertEqual(self.target.read_text(), "# external\n")

    def test_failed_generation_saves_logs_without_tasks(self):
        with self.assertRaises(RuntimeError):
            plan_tasks.generate_plan(
                "Goal", self.allowed, lambda prompt: "invalid"
            )
        folders = list((self.root / "outputs").glob("plan_*"))
        self.assertEqual(len(folders), 1)
        self.assertFalse((folders[0] / "tasks.json").exists())
        self.assertEqual(len(list(folders[0].glob("answer_*.txt"))), 3)

    def write_plan(self, status="pending"):
        folder = self.root / "outputs" / "plan_test"
        folder.mkdir(parents=True)
        path = folder / "tasks.json"
        path.write_text(
            json.dumps([{**self.task, "status": status}]),
            encoding="utf-8",
        )
        return path

    def test_execution_uses_separate_list_and_restores_default(self):
        path = self.write_plan()
        original = run_tasks.TASKS_PATH

        def runner(**kwargs):
            self.assertEqual(run_tasks.TASKS_PATH, path)

        with patch.object(run_tasks, "run_tasks", side_effect=runner):
            execute_plan.execute_plan(path)
        self.assertEqual(run_tasks.TASKS_PATH, original)

    def test_execution_exception_restores_default(self):
        path = self.write_plan()
        original = run_tasks.TASKS_PATH
        with patch.object(
            run_tasks, "run_tasks", side_effect=RuntimeError("stopped")
        ):
            with self.assertRaises(RuntimeError):
                execute_plan.execute_plan(path)
        self.assertEqual(run_tasks.TASKS_PATH, original)

    def test_failed_plan_blocks_runner(self):
        path = self.write_plan("failed")
        with patch.object(run_tasks, "run_tasks") as runner:
            with self.assertRaises(RuntimeError):
                execute_plan.execute_plan(path)
            runner.assert_not_called()

    def test_existing_task_list_path_is_rejected(self):
        with self.assertRaises(ValueError):
            execute_plan.resolve_plan(self.root / "runner_tasks.json")

    def test_symlink_plan_is_rejected(self):
        path = self.write_plan()
        saved = path.with_name("saved.json")
        path.rename(saved)
        path.symlink_to(saved)
        with self.assertRaises(ValueError):
            execute_plan.resolve_plan(path)


if __name__ == "__main__":
    unittest.main()