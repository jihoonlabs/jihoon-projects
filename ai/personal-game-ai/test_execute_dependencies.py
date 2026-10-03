import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import execute_plan
import run_tasks


class ExecuteDependencyTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.folder = self.root / "outputs" / "plan_test"
        self.folder.mkdir(parents=True)
        self.path = self.folder / "tasks.json"
        self.fixed = self.root / "test_fixed.py"
        self.fixed.write_text("# fixed\n", encoding="utf-8")
        self.calls = []

        for module, name, value in (
            (execute_plan, "BASE_DIR", self.root),
            (run_tasks, "BASE_DIR", self.root),
            (run_tasks, "OUTPUT_DIR", self.root / "outputs"),
            (run_tasks, "read_context", Mock(return_value="CONTEXT")),
            (run_tasks, "prepare_file_task", Mock()),
            (run_tasks, "handle_edit", Mock(side_effect=self.handle)),
            (execute_plan.edit_loop, "resolve_files", Mock(
                side_effect=self.resolve
            )),
            (execute_plan.edit_loop, "check_git_files", Mock()),
        ):
            patcher = patch.object(module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def resolve(self, target, test_module):
        return self.root / Path(target).name, self.fixed

    def task(self, task_id, dependencies=None):
        return {
            "id": task_id,
            "kind": "create",
            "target": f"sandbox/{task_id}.py",
            "test_module": "test_fixed",
            "prompt": f"Implement {task_id}.",
            "depends_on": dependencies or [],
            "status": "pending",
        }

    def save(self, tasks):
        self.path.write_text(json.dumps(tasks), encoding="utf-8")

    def load(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def handle(self, task, model):
        self.calls.append((task["id"], task["prompt"]))
        model(task["prompt"])
        target, _ = self.resolve(task["target"], task["test_module"])
        target.write_text(
            f"VALUE = {task['id']!r}\n", encoding="utf-8"
        )
        task.update(status="tests_passed", output="outputs/mock", attempts=1)

    def execute(self, **kwargs):
        return execute_plan.execute_plan(
            self.path, model=lambda prompt: "response", **kwargs
        )

    def test_order_and_dependency_code_are_passed(self):
        self.save([self.task("b", ["a"]), self.task("a")])
        self.execute()
        self.assertEqual([item[0] for item in self.calls], ["a", "b"])
        self.assertIn("VALUE = 'a'", self.calls[1][1])
        self.assertIn("sandbox/a.py", self.calls[1][1])
        self.assertTrue(all(
            task["status"] == "tests_passed" for task in self.load()
        ))
        self.assertTrue(all("artifact" in task for task in self.load()))

    def test_completed_plan_is_not_executed_again(self):
        self.save([self.task("a"), self.task("b", ["a"])])
        self.execute()
        self.execute()
        self.assertEqual(len(self.calls), 2)

    def test_external_dependency_change_blocks_resume(self):
        self.save([self.task("a"), self.task("b", ["a"])])
        self.execute()
        (self.root / "a.py").write_text("# external\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.execute()
        self.assertEqual(
            (self.root / "a.py").read_text(), "# external\n"
        )
        self.assertEqual(len(self.calls), 2)

    def test_fixed_test_change_blocks_resume(self):
        self.save([self.task("a"), self.task("b", ["a"])])
        self.execute()
        self.fixed.write_text("# changed\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.execute()

    def test_question_stops_and_answer_resumes(self):
        self.save([self.task("a"), self.task("b", ["a"])])
        original = self.handle

        def question(task, model):
            if task["id"] == "b":
                task.update(
                    status="waiting_for_user",
                    question="Choose?",
                    output="outputs/question",
                )
            else:
                original(task, model)

        run_tasks.handle_edit.side_effect = question
        self.execute()
        tasks = self.load()
        self.assertEqual(
            [task["status"] for task in tasks],
            ["tests_passed", "waiting_for_user"],
        )

        run_tasks.handle_edit.side_effect = original
        self.execute(answer_task_id="b", answer="Use option one.")
        tasks = self.load()
        self.assertEqual(tasks[1]["status"], "tests_passed")
        self.assertNotIn("question", tasks[1])
        self.assertIn("Use option one.", self.calls[-1][1])
        self.assertIn("VALUE = 'a'", self.calls[-1][1])
        self.assertEqual(
            [item[0] for item in self.calls], ["a", "b"]
        )

    def test_failed_task_stops_following_task(self):
        self.save([self.task("a"), self.task("b", ["a"])])

        def fail(task, model):
            task.update(status="failed", output="outputs/fail", error="fail")

        run_tasks.handle_edit.side_effect = fail
        self.execute()
        self.assertEqual(
            [task["status"] for task in self.load()], ["failed", "pending"]
        )
        with self.assertRaises(RuntimeError):
            self.execute()

    def test_running_task_blocks_execution(self):
        tasks = [self.task("a"), self.task("b", ["a"])]
        tasks[0]["status"] = "running"
        self.save(tasks)
        before = self.path.read_bytes()
        self.execute()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.calls, [])

    def test_existing_lock_is_preserved(self):
        self.save([self.task("a"), self.task("b", ["a"])])
        lock = self.root / ".run_tasks.lock"
        lock.write_text("existing", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.execute()
        self.assertEqual(lock.read_text(), "existing")

    def test_dependency_change_during_model_call_stops(self):
        self.save([self.task("a"), self.task("b", ["a"])])

        def model(prompt):
            if "Implement b." in prompt:
                (self.root / "a.py").write_text(
                    "# external\n", encoding="utf-8"
                )
            return "response"

        with self.assertRaises(RuntimeError):
            execute_plan.execute_plan(self.path, model=model)
        self.assertEqual(self.load()[1]["status"], "failed")
        self.assertFalse((self.root / "b.py").exists())
        self.assertFalse((self.root / ".run_tasks.lock").exists())

    def test_dependency_code_length_blocks_next_task(self):
        self.save([self.task("a"), self.task("b", ["a"])])

        def large(task, model):
            original_target, _ = self.resolve(
                task["target"], task["test_module"]
            )
            original_target.write_text(
                "#" + "x" * 4000 + "\n", encoding="utf-8"
            )
            task.update(status="tests_passed", output="outputs/large")

        run_tasks.handle_edit.side_effect = large
        with self.assertRaises(ValueError):
            self.execute()
        self.assertEqual(self.load()[1]["status"], "pending")
        self.assertFalse((self.root / ".run_tasks.lock").exists())


if __name__ == "__main__":
    unittest.main()