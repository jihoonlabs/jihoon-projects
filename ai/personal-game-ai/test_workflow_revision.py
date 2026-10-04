import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import workflow


class WorkflowRevisionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.folder = self.root / "outputs" / "workflow_fixture"
        self.folder.mkdir(parents=True)
        self.old = self.root / "outputs" / "design_old" / "design.json"
        self.old.parent.mkdir()
        self.old.write_bytes(b"old")
        self.new = self.root / "outputs" / "design_new" / "design.json"
        self.new.parent.mkdir()
        self.new.write_bytes(b"new")
        self.state = {
            "stage": "review_design",
            "request": {"goal": "goal", "requirements": ["rule"], "area": "sandbox"},
            "context": "CONTEXT",
            "design": "outputs/design_old/design.json",
            "design_sha256": workflow.digest(b"old"),
            "protected": {"outputs/design_old/design.json": workflow.digest(b"old")},
        }
        self.envelope = {
            "request": {"goal": "goal", "requirements": {"R1": "rule"}, "area": "sandbox"},
            "context": "CONTEXT",
            "revision": {
                "source": self.state["design"],
                "source_sha256": self.state["design_sha256"],
            },
        }
        patcher = patch.object(workflow, "BASE_DIR", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def connect(self):
        with patch.object(
            workflow.design_plan, "read_design",
            return_value=(self.new, b"new", self.envelope),
        ):
            workflow.connect_reviewed_design(
                self.state, self.folder / "state.json", self.new
            )

    def test_connection_preserves_old_artifact_and_requires_new_approval(self):
        self.connect()
        self.assertEqual(self.state["stage"], "review_design")
        self.assertEqual(self.state["design"], "outputs/design_new/design.json")
        self.assertIn("outputs/design_old/design.json", self.state["protected"])
        self.assertEqual(self.old.read_bytes(), b"old")
        self.assertFalse(self.new.with_name("approval.json").exists())
        self.assertEqual(len(list(self.folder.glob("design_before_*.json"))), 1)

    def test_wrong_revision_is_rejected_without_state_change(self):
        before = copy.deepcopy(self.state)
        self.envelope["revision"]["source_sha256"] = "wrong"
        with self.assertRaises(RuntimeError):
            self.connect()
        self.assertEqual(self.state, before)
        self.assertFalse((self.folder / "state.json").exists())

    def test_changed_goal_is_rejected(self):
        self.envelope["request"]["goal"] = "other"
        with self.assertRaises(RuntimeError):
            self.connect()

    def test_connection_after_review_is_rejected(self):
        self.state["stage"] = "review_tests"
        with self.assertRaises(ValueError):
            self.connect()


if __name__ == "__main__":
    unittest.main()
