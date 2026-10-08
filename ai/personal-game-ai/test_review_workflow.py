import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import review_workflow
import workflow
import execute_plan
import edit_loop


class ReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.base = self.root / "ai" / "personal-game-ai"
        self.game = self.root / "micropython" / "ThumbyDodge"
        self.base.mkdir(parents=True)
        self.game.mkdir(parents=True)
        self.config = self.base / "target.json"
        self.config.write_text(json.dumps({
            "repository_root": "../..", "edit_directory": "micropython/ThumbyDodge",
        }))
        self.git("init", "-q")
        self.fixed = self.game / "test_rules.py"
        self.fixed.write_text("# fixed test fixture\n")
        self.git("add", "micropython/ThumbyDodge/test_rules.py")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
        self.target = self.game / "rules.py"
        self.target.write_text("def step():\n    return 1\n")
        self.record = self.base / "outputs" / "workflow_fixture"
        self.record.mkdir(parents=True)
        self.plan = self.base / "outputs" / "plan_fixture" / "tasks.json"
        self.plan.parent.mkdir()
        self.request = self.base / "request.json"
        payload = {"area": "game", "goal": "Game fixture", "requirements": ["Step"]}
        self.request.write_text(json.dumps(payload))
        self.context = Mock(return_value="CONTEXT")
        self.model = Mock(side_effect=AssertionError("Model must not run"))
        self.runner = Mock(side_effect=AssertionError("Docker must not run"))
        for owner, name, value in (
            (workflow, "BASE_DIR", self.base), (execute_plan, "BASE_DIR", self.base),
            (edit_loop, "BASE_DIR", self.base), (edit_loop, "CONFIG_PATH", self.config),
            (edit_loop, "read_context", self.context), (edit_loop, "ask_model", self.model),
            (edit_loop, "run_test", self.runner),
        ):
            patcher = patch.object(owner, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.task = {
            "id": "001", "kind": "create", "target": "game/rules.py",
            "test_module": "test_rules", "prompt": "Implement step.",
            "depends_on": [], "status": "tests_passed",
        }
        self.task["artifact"] = execute_plan.capture_artifact(self.task)
        self.plan.write_text(json.dumps([self.task]))
        self.state = {
            "request_path": str(self.request), "request_sha256": workflow.digest(self.request.read_bytes()),
            "request": payload, "context": "CONTEXT", "stage": "completed", "protected": {},
            "installed": {os.path.relpath(self.fixed, self.base): workflow.digest(self.fixed.read_bytes())},
            "plan": str(self.plan.relative_to(self.base)), "plan_contract": workflow.plan_contract(self.plan),
        }
        self.save()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True, text=True)

    def save(self):
        (self.record / "state.json").write_text(json.dumps(self.state))

    def inspect(self):
        before = {str(p): p.read_bytes() for p in self.base.rglob("*") if p.is_file()}
        result = review_workflow.review(self.request, self.record)
        after = {str(p): p.read_bytes() for p in self.base.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.model.assert_not_called()
        self.runner.assert_not_called()
        return result

    def test_completed_record_checks_real_git_and_artifact_without_writes(self):
        result = self.inspect()
        self.assertEqual(result["result"], "reviewed")
        self.assertEqual(result["tasks"][0]["artifact"], "unchanged")
        self.assertEqual(result["commit_required"], [])

    def test_context_mismatch_does_not_recommend_resume(self):
        self.context.return_value = "CHANGED"
        result = self.inspect()
        self.assertEqual(result["result"], "blocked")
        self.assertFalse(result["matches"]["context"])
        self.assertIn("자동 재개하지", result["next"])

    def test_lock_is_preserved_and_stops_inspection(self):
        lock = self.base / ".workflow.lock"
        lock.write_text("existing")
        self.assertEqual(self.inspect()["result"], "blocked")
        self.assertEqual(lock.read_text(), "existing")

    def test_changed_generated_code_blocks_completed_result(self):
        self.target.write_text("def step():\n    return 2\n")
        self.assertEqual(self.inspect()["result"], "blocked")

    def test_changed_fixed_test_blocks_result(self):
        self.fixed.write_text("# changed\n")
        self.assertEqual(self.inspect()["result"], "blocked")

    def test_completed_with_pending_task_is_not_reported_complete(self):
        self.task["status"] = "pending"
        self.plan.write_text(json.dumps([self.task]))
        self.assertEqual(self.inspect()["result"], "blocked")

    def test_pending_request_length_is_reported_without_running_model(self):
        self.task["status"] = "pending"
        self.plan.write_text(json.dumps([self.task]))
        self.state["stage"] = "execute"
        self.save()
        result = self.inspect()
        self.assertEqual(result["result"], "reviewed")
        self.assertEqual(result["tasks"][0]["request_chars"], len(self.task["prompt"]))

    def test_plan_contract_change_is_rejected(self):
        self.task["prompt"] = "Different contract"
        self.plan.write_text(json.dumps([self.task]))
        self.assertEqual(self.inspect()["result"], "blocked")

    def test_review_stage_without_candidate_is_blocked(self):
        for stage in ("review_design", "review_tests"):
            with self.subTest(stage=stage):
                self.state["stage"] = stage
                self.save()
                self.assertEqual(self.inspect()["result"], "blocked")

    def test_plan_status_change_during_final_context_check_is_blocked(self):
        def context():
            if self.context.call_count == 2:
                changed = {**self.task, "status": "failed", "error": "external change"}
                self.plan.write_text(json.dumps([changed]))
            return "CONTEXT"
        self.context.side_effect = context
        result = review_workflow.review(self.request, self.record)
        self.assertEqual(result["result"], "blocked")
        self.model.assert_not_called()
        self.runner.assert_not_called()

    def test_review_stage_exposes_protected_candidate_without_approving(self):
        candidate = self.base / "outputs" / "design_fixture" / "design.json"
        candidate.parent.mkdir()
        candidate.write_text('{"fixture": true}')
        relative = str(candidate.relative_to(self.base))
        sha = workflow.digest(candidate.read_bytes())
        self.state.update(stage="review_design", design=relative, design_sha256=sha)
        self.state["protected"][relative] = sha
        self.save()
        result = self.inspect()
        self.assertEqual(result["result"], "reviewed")
        self.assertEqual(result["review_file"], str(candidate))
        self.assertEqual(result["review_sha256"], sha)
        self.assertFalse(candidate.with_name("approval.json").exists())

    def test_completed_record_with_untracked_fixed_test_is_blocked(self):
        self.git("rm", "--cached", "micropython/ThumbyDodge/test_rules.py")
        result = self.inspect()
        self.assertEqual(result["result"], "blocked")
        self.assertEqual(result["commit_required"], ["micropython/ThumbyDodge/test_rules.py"])

    def test_oversized_pending_request_is_blocked_without_model(self):
        self.task.update(status="pending", prompt="x" * 4001)
        self.plan.write_text(json.dumps([self.task]))
        self.state.update(stage="execute", plan_contract=workflow.plan_contract(self.plan))
        self.save()
        result = self.inspect()
        self.assertEqual(result["result"], "blocked")
        self.assertIn("4000", " ".join(result["issues"]))

    def test_record_symlink_and_missing_record_do_not_create_files(self):
        link = self.record.with_name("workflow_link")
        link.symlink_to(self.record, target_is_directory=True)
        self.assertEqual(review_workflow.review(self.request, link)["result"], "blocked")
        missing = self.record.with_name("workflow_missing")
        self.assertEqual(review_workflow.review(self.request, missing)["result"], "blocked")
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
