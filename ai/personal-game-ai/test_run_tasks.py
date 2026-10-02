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
        ):
            patcher = patch.object(run_tasks, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        patcher = patch.object(
            run_tasks, "read_context", return_value="TEST_CONTEXT"
        )
        self.context = patcher.start()
        self.addCleanup(patcher.stop)

    def write_tasks(self, tasks):
        self.tasks_path.write_text(
            json.dumps(tasks), encoding="utf-8"
        )

    def read_tasks(self):
        return json.loads(self.tasks_path.read_text(encoding="utf-8"))

    def task(self, task_id, kind="text"):
        return {
            "id": task_id,
            "status": "pending",
            "kind": kind,
            "prompt": f"request-{task_id}",
        }

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

        def model(prompt):
            self.fail("보류 작업에서 모델을 호출했습니다.")

        run_tasks.run_tasks(model)
        self.assertEqual(
            [task["status"] for task in self.read_tasks()],
            ["waiting_for_user", "running"],
        )

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

        def model(prompt):
            self.fail("文脈確認の失敗後にモデルを呼びました。")

        with self.assertRaises(RuntimeError):
            run_tasks.run_tasks(model)
        self.assertEqual(self.read_tasks()[0]["status"], "pending")

    def test_save_failure_blocks_model(self):
        self.write_tasks([self.task("001")])

        def model(prompt):
            self.fail("저장 실패 후 모델을 호출했습니다.")

        with patch.object(
            run_tasks, "save_tasks", side_effect=OSError("disk failed")
        ):
            with self.assertRaises(OSError):
                run_tasks.run_tasks(model)

    def test_duplicate_id_blocks_model(self):
        self.write_tasks([self.task("001"), self.task("001")])

        def model(prompt):
            self.fail("중복 id가 있는 목록을 실행했습니다.")

        with self.assertRaises(ValueError):
            run_tasks.run_tasks(model)


if __name__ == "__main__":
    unittest.main()