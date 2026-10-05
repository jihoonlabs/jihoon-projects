import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import workflow


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.request = self.root / "request.json"
        self.request.write_text(json.dumps({
            "goal": "회복 구현",
            "requirements": ["최대 체력을 넘지 않는다"],
            "area": "sandbox",
        }), encoding="utf-8")
        self.context = Mock(return_value="CONTEXT")
        for owner, name, value in (
            (workflow, "BASE_DIR", self.root),
            (workflow.edit_loop, "read_context", self.context),
        ):
            patcher = patch.object(owner, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(workflow.design_plan, "validate_input")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.generator = Mock(side_effect=self.generate_design)
        patcher = patch.object(
            workflow.design_plan, "generate_design", self.generator
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def generate_design(self, *args, **kwargs):
        kwargs["model"]("design prompt")
        folder = self.root / "outputs" / "design_fixture"
        folder.mkdir()
        path = folder / "design.json"
        path.write_text('{"design": "fixture"}', encoding="utf-8")
        return path

    def run_flow(self, **kwargs):
        return workflow.run_workflow(
            self.request, model=Mock(return_value="answer"), **kwargs
        )

    def test_first_run_stops_for_design_review(self):
        result = self.run_flow()
        self.assertEqual(result["stage"], "review_design")
        self.assertTrue(Path(result["review_file"]).is_file())
        self.assertEqual(self.generator.call_count, 1)

    def test_repeated_review_does_not_call_model_again(self):
        first = self.run_flow()
        second = self.run_flow()
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(self.generator.call_count, 1)

    def test_wrong_approval_does_not_advance(self):
        self.run_flow()
        with patch.object(workflow.design_plan, "approve_design") as approve:
            result = self.run_flow(approve="wrong")
        self.assertIn("error", result)
        approve.assert_not_called()
        self.assertEqual(result["stage"], "review_design")

    def test_request_change_blocks_resume(self):
        self.run_flow()
        self.request.write_text(self.request.read_text() + "\n")
        with self.assertRaises(RuntimeError):
            self.run_flow()
        self.assertEqual(self.generator.call_count, 1)

    def test_context_change_blocks_resume(self):
        self.run_flow()
        self.context.return_value = "OTHER"
        with self.assertRaises(RuntimeError):
            self.run_flow()

    def test_changed_design_blocks_resume(self):
        first = self.run_flow()
        Path(first["review_file"]).write_text("changed")
        with self.assertRaises(RuntimeError):
            self.run_flow()

    def test_existing_lock_blocks_model(self):
        (self.root / ".workflow.lock").write_text("existing")
        with self.assertRaises(RuntimeError):
            self.run_flow()
        self.generator.assert_not_called()

    def test_model_request_change_stops_generation(self):
        def model(prompt):
            self.request.write_text(self.request.read_text() + "\n")
            return "answer"
        result = workflow.run_workflow(self.request, model=model)
        self.assertIn("error", result)
        self.assertEqual(result["stage"], "generating_design")

    def test_interrupted_generation_is_not_repeated(self):
        self.generator.side_effect = RuntimeError("model failed")
        first = self.run_flow()
        second = self.run_flow()
        self.assertIn("error", first)
        self.assertIn("error", second)
        self.assertEqual(self.generator.call_count, 1)

    def test_conflicting_actions_rejected(self):
        with self.assertRaises(ValueError):
            self.run_flow(approve="sha", confirm="sha")

    def test_invalid_request_fields_rejected(self):
        self.request.write_text('{"goal":"only goal"}')
        with self.assertRaises(ValueError):
            self.run_flow()
        self.generator.assert_not_called()

    def test_plan_status_reports_question(self):
        path = self.root / "tasks.json"
        path.write_text(json.dumps([{
            "id": "001", "status": "waiting_for_user", "question": "選択?",
        }]))
        with patch.object(
            workflow.execute_plan, "resolve_plan", return_value=path
        ):
            status, details = workflow.plan_status(path)
        self.assertEqual(status, "waiting_for_user")
        self.assertEqual(details[0]["id"], "001")

    def test_plan_status_reports_failed_task(self):
        path = self.root / "tasks.json"
        path.write_text(json.dumps([{
            "id": "001", "status": "failed", "error": "failed test",
        }]))
        with patch.object(
            workflow.execute_plan, "resolve_plan", return_value=path
        ):
            status, details = workflow.plan_status(path)
        self.assertEqual(status, "blocked")
        self.assertEqual(details[0]["error"], "failed test")


    def test_approval_generates_tests_then_stops_for_review(self):
        first = self.run_flow()
        design = Path(first["review_file"])

        def approve(path, sha):
            record = path.with_name("approval.json")
            record.write_text("approval")
            return record

        def generate(path, model=None):
            folder = self.root / "outputs" / "test_plan_fixture"
            folder.mkdir()
            manifest = folder / "tests.json"
            manifest.write_text(json.dumps({
                "tests": {"files": [{"filename": "test_health.py"}]}
            }))
            (folder / "test_health.py.txt").write_text("candidate")
            return manifest

        with patch.object(
            workflow.design_plan, "approve_design", side_effect=approve
        ), patch.object(
            workflow.test_plan, "generate_tests", side_effect=generate
        ), patch.object(workflow.implementation_link, "install_tests") as install:
            result = self.run_flow(approve=first["sha256"])
        self.assertEqual(result["stage"], "review_tests")
        self.assertTrue(design.with_name("approval.json").exists())
        install.assert_not_called()

    def test_confirmation_installs_then_stops_before_execution(self):
        folder = self.root / "outputs" / "workflow_fixture"
        folder.mkdir(parents=True)
        manifest = self.root / "outputs" / "test_plan_fixture" / "tests.json"
        manifest.parent.mkdir()
        manifest.write_text("candidate")
        installed = self.root / "sandbox" / "test_health.py"
        installed.parent.mkdir()
        installed.write_text("fixed test")
        state = {
            "stage": "review_tests", "protected": {},
            "tests": str(manifest.relative_to(self.root)),
            "tests_sha256": "sha",
        }

        def confirm(path, sha):
            path.with_name("confirmation.json").write_text("confirmation")

        with patch.object(
            workflow.test_plan, "confirm_tests", side_effect=confirm
        ), patch.object(
            workflow.implementation_link, "install_tests",
            return_value=[installed],
        ), patch.object(workflow.execute_plan, "execute_plan") as execute:
            workflow.advance(
                state, folder / "state.json", Mock(),
                None, "sha", None, None,
            )
        self.assertEqual(state["stage"], "waiting_git")
        self.assertIn("sandbox/test_health.py", state["installed"])
        execute.assert_not_called()

    def test_git_wait_does_not_create_plan_or_execute(self):
        folder = self.root / "outputs" / "workflow_fixture"
        folder.mkdir(parents=True)
        state = {"stage": "waiting_git"}
        with patch.object(
            workflow, "installed_tests", return_value=["test_health.py"]
        ), patch.object(
            workflow.implementation_link, "create_plan"
        ) as create, patch.object(
            workflow.execute_plan, "execute_plan"
        ) as execute:
            workflow.advance(
                state, folder / "state.json", Mock(),
                None, None, None, None,
            )
        create.assert_not_called()
        execute.assert_not_called()

    def test_answer_is_passed_to_existing_executor(self):
        folder = self.root / "outputs" / "workflow_fixture"
        folder.mkdir(parents=True)
        state = {"stage": "execute", "plan": "outputs/plan_fixture/tasks.json"}
        model = Mock()
        with patch.object(
            workflow, "installed_tests", return_value=[]
        ), patch.object(
            workflow, "plan_status",
            side_effect=[
                ("waiting_for_user", [{"id": "001", "question": "Choose?"}]),
                ("completed", []),
            ],
        ), patch.object(
            workflow.execute_plan, "execute_plan"
        ) as execute:
            workflow.advance(
                state, folder / "state.json", model,
                None, None, "001", "답변",
            )
        execute.assert_called_once_with(
            self.root / state["plan"], model=model,
            answer_task_id="001", answer="답변",
        )
        self.assertEqual(state["stage"], "completed")

    def test_failed_execution_is_not_automatically_retried(self):
        folder = self.root / "outputs" / "workflow_fixture"
        folder.mkdir(parents=True)
        state = {"stage": "execute", "plan": "outputs/plan_fixture/tasks.json"}
        with patch.object(
            workflow, "installed_tests", return_value=[]
        ), patch.object(
            workflow, "plan_status",
            return_value=("blocked", [{"id": "001", "status": "failed"}]),
        ), patch.object(
            workflow.execute_plan, "execute_plan"
        ) as execute:
            workflow.advance(
                state, folder / "state.json", Mock(),
                None, None, None, None,
            )
        execute.assert_not_called()
        self.assertEqual(state["details"][0]["status"], "failed")

    def test_plan_contract_change_is_rejected(self):
        path = self.root / "tasks.json"
        task = {
            "id": "001", "kind": "create", "target": "sandbox/health.py",
            "test_module": "test_health", "prompt": "heal",
            "depends_on": [], "status": "pending",
        }
        path.write_text(json.dumps([task]))
        with patch.object(
            workflow.execute_plan, "resolve_plan", return_value=path
        ):
            state = {
                "plan": "tasks.json",
                "plan_contract": workflow.plan_contract(path),
            }
            task["status"] = "tests_passed"
            path.write_text(json.dumps([task]))
            workflow.verify_plan(state)
            task["target"] = "sandbox/other.py"
            path.write_text(json.dumps([task]))
            with self.assertRaises(RuntimeError):
                workflow.verify_plan(state)



    def test_explicit_retry_repeats_failed_design_generation(self):
        self.generator.side_effect = RuntimeError("model failed")
        first = self.run_flow()
        self.assertIn("error", first)
        self.generator.side_effect = self.generate_design
        result = self.run_flow(retry=True)
        self.assertEqual(result["stage"], "review_design")
        self.assertEqual(self.generator.call_count, 2)
        self.assertEqual(
            len(list(Path(result["record"]).glob("retry_before_*.json"))), 1
        )

    def test_retry_does_not_restart_reviewed_design(self):
        self.run_flow()
        with self.assertRaises(ValueError):
            self.run_flow(retry=True)
        self.assertEqual(self.generator.call_count, 1)

    def test_retry_cannot_be_combined_with_approval(self):
        with self.assertRaises(ValueError):
            self.run_flow(retry=True, approve="sha")
        self.generator.assert_not_called()



    def test_feedback_regenerates_candidate_without_installing(self):
        folder = self.root / "outputs" / "workflow_feedback"
        folder.mkdir(parents=True)
        old = self.root / "outputs" / "old_tests.json"
        old.write_text("old candidate")
        state = {
            "stage": "review_tests",
            "tests": "outputs/old_tests.json",
            "design": "outputs/design.json",
            "protected": {},
        }
        new = self.root / "outputs" / "new_tests.json"
        new.write_text(json.dumps({
            "tests": {"files": [{"filename": "test_health.py"}]}
        }))
        (new.parent / "test_health.py.txt").write_text("new candidate")
        with patch.object(
            workflow, "generate_candidate", return_value=new
        ) as generate, patch.object(
            workflow.implementation_link, "install_tests"
        ) as install:
            workflow.advance(
                state, folder / "state.json", Mock(),
                None, None, None, None, feedback="함수 목록 검사",
            )
        generate.assert_called_once()
        install.assert_not_called()
        self.assertEqual(state["stage"], "review_tests")
        self.assertEqual(state["previous_tests"], "outputs/old_tests.json")
        self.assertEqual(old.read_text(), "old candidate")
        self.assertEqual(state["tests"], "outputs/new_tests.json")

    def test_empty_feedback_is_rejected(self):
        with self.assertRaises(ValueError):
            self.run_flow(feedback=" ")
        self.generator.assert_not_called()



    def test_execution_summary_reports_current_work(self):
        path = self.root / "tasks.json"
        path.write_text(json.dumps([
            {"id": "001", "status": "tests_passed"},
            {"id": "002", "status": "running"},
            {"id": "003", "status": "pending"},
        ]))
        with patch.object(
            workflow.execute_plan, "resolve_plan", return_value=path
        ):
            result = workflow.execution_summary(path)
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["counts"]["tests_passed"], 1)
        self.assertEqual(result["counts"]["running"], 1)
        self.assertEqual(
            result["current"], [{"id": "002", "status": "running"}]
        )

    def test_summary_marks_interrupted_execution_recoverable(self):
        path = self.root / "tasks.json"
        path.write_text(json.dumps([
            {"id": "001", "status": "running"},
            {"id": "002", "status": "pending"},
        ]))
        state = {"stage": "execute", "plan": "tasks.json"}
        with patch.object(
            workflow.execute_plan, "resolve_plan", return_value=path
        ):
            result = workflow.summarize(state, self.root)
        self.assertEqual(result["execution"], "blocked")
        self.assertTrue(result["recovery_available"])
        self.assertEqual(result["next"], "--recover")

    def test_recovery_validates_before_resetting_running_task(self):
        path = self.root / "tasks.json"
        task = {
            "id": "001", "kind": "edit", "target": "sandbox/health.py",
            "test_module": "test_health", "prompt": "heal",
            "depends_on": [], "status": "running",
        }
        path.write_text(json.dumps([task]))
        state = {
            "stage": "execute",
            "plan": "tasks.json",
            "plan_contract": [{
                key: task.get(key, [] if key == "depends_on" else None)
                for key in (
                    "id", "kind", "target", "test_module",
                    "prompt", "depends_on"
                )
            }],
        }
        with patch.object(
            workflow, "installed_tests", return_value=[]
        ), patch.object(
            workflow.execute_plan, "resolve_plan", return_value=path
        ), patch.object(
            workflow.run_tasks, "prepare_file_task"
        ) as prepare:
            recovered = workflow.recover_interrupted_plan(state)
        prepare.assert_called_once()
        self.assertEqual(recovered, ["001"])
        self.assertEqual(json.loads(path.read_text())[0]["status"], "pending")

    def test_recovery_gate_failure_preserves_running_state(self):
        path = self.root / "tasks.json"
        task = {
            "id": "001", "kind": "edit", "target": "sandbox/health.py",
            "test_module": "test_health", "prompt": "heal",
            "depends_on": [], "status": "running",
        }
        path.write_text(json.dumps([task]))
        state = {
            "stage": "execute",
            "plan": "tasks.json",
            "plan_contract": [{
                key: task.get(key, [] if key == "depends_on" else None)
                for key in (
                    "id", "kind", "target", "test_module",
                    "prompt", "depends_on"
                )
            }],
        }
        with patch.object(
            workflow, "installed_tests", return_value=[]
        ), patch.object(
            workflow.execute_plan, "resolve_plan", return_value=path
        ), patch.object(
            workflow.run_tasks, "prepare_file_task",
            side_effect=RuntimeError("dirty target"),
        ):
            with self.assertRaisesRegex(RuntimeError, "dirty target"):
                workflow.recover_interrupted_plan(state)
        self.assertEqual(json.loads(path.read_text())[0]["status"], "running")

    def test_recovery_rejects_leftover_inner_lock(self):
        path = self.root / "tasks.json"
        path.write_text(json.dumps([{"id": "001", "status": "running"}]))
        (self.root / ".run_tasks.lock").write_text("stale")
        state = {"stage": "execute", "plan": "tasks.json"}
        with patch.object(workflow, "installed_tests", return_value=[]):
            with self.assertRaisesRegex(RuntimeError, "잠금"):
                workflow.recover_interrupted_plan(state)


if __name__ == "__main__":
    unittest.main()
