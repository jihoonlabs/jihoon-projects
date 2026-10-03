import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import design_plan


class DesignRevisionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sandbox = self.root / "sandbox"
        self.sandbox.mkdir()
        self.proposal = {
            "files": [{
                "id": "001",
                "filename": "health.py",
                "functions": [{
                    "name": "heal",
                    "parameters": ["hp", "amount", "maximum"],
                    "behavior": "Return min(hp + amount, maximum).",
                }],
                "checks": [{
                    "requirement": "R1",
                    "case": "heal(8, 5, 10)",
                    "expected": "10",
                }],
                "depends_on": [],
            }],
        }
        for module, name, value in (
            (design_plan, "BASE_DIR", self.root),
            (design_plan, "read_context", Mock(return_value="CONTEXT")),
            (design_plan.edit_loop, "SANDBOX", self.sandbox),
            (design_plan.edit_loop, "check_directory", Mock()),
            (design_plan.edit_loop, "git_output", Mock(return_value="")),
        ):
            patcher = patch.object(module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.original = design_plan.generate_design(
            "Implement recovery.",
            ["Clamp recovery to maximum."],
            "sandbox",
            model=lambda prompt: json.dumps(self.proposal),
        )
        self.original_bytes = self.original.read_bytes()

    def model(self):
        proposal = copy.deepcopy(self.proposal)
        proposal["files"][0]["checks"][0]["case"] = "heal(9, 4, 10)"
        return Mock(return_value=json.dumps(proposal))

    def test_revision_preserves_input_source_and_feedback(self):
        feedback = "Add a recovery amount of four to the check."
        model = self.model()
        revised = design_plan.revise_design(self.original, feedback, model)
        old = json.loads(self.original_bytes)
        new = json.loads(revised.read_bytes())

        self.assertNotEqual(revised.parent, self.original.parent)
        self.assertEqual(new["request"], old["request"])
        self.assertEqual(new["context"], old["context"])
        self.assertEqual(new["revision"], {
            "source": str(self.original.relative_to(self.root)),
            "source_sha256": hashlib.sha256(self.original_bytes).hexdigest(),
            "feedback": feedback,
        })
        self.assertEqual(self.original.read_bytes(), self.original_bytes)
        self.assertEqual(
            json.loads(revised.with_name("revision.json").read_bytes()),
            new["revision"],
        )
        self.assertEqual(
            json.loads(revised.with_name("request.json").read_bytes()),
            old["request"],
        )
        prompt = model.call_args.args[0]
        self.assertIn(feedback, prompt)
        self.assertIn(json.dumps(old["design"], ensure_ascii=False), prompt)
        self.assertEqual(list(self.sandbox.iterdir()), [])
        self.assertFalse(revised.with_name("approval.json").exists())

    def test_original_approval_is_preserved_and_not_inherited(self):
        digest = hashlib.sha256(self.original_bytes).hexdigest()
        approval = design_plan.approve_design(self.original, digest)
        before = approval.read_bytes()
        revised = design_plan.revise_design(
            self.original, "Improve the check.", self.model()
        )
        self.assertEqual(approval.read_bytes(), before)
        self.assertFalse(revised.with_name("approval.json").exists())
        revised_digest = hashlib.sha256(revised.read_bytes()).hexdigest()
        self.assertTrue(
            design_plan.approve_design(revised, revised_digest).is_file()
        )

    def test_invalid_feedback_does_not_call_model(self):
        for feedback in ("", "   ", "x" * 4001, None, ["feedback"]):
            with self.subTest(feedback_type=type(feedback).__name__):
                model = self.model()
                with self.assertRaises(ValueError):
                    design_plan.revise_design(self.original, feedback, model)
                model.assert_not_called()

    def test_revision_uses_current_context_but_old_approval_is_blocked(self):
        design_plan.read_context.return_value = "UPDATED CONTEXT"
        original_digest = hashlib.sha256(self.original_bytes).hexdigest()
        with self.assertRaises(RuntimeError):
            design_plan.approve_design(self.original, original_digest)

        model = self.model()
        revised = design_plan.revise_design(
            self.original, "Fix the check.", model
        )
        envelope = json.loads(revised.read_bytes())
        self.assertEqual(envelope["context"], "UPDATED CONTEXT")
        self.assertEqual(
            envelope["request"], json.loads(self.original_bytes)["request"]
        )
        self.assertTrue(model.call_args.args[0].startswith("UPDATED CONTEXT"))
        self.assertEqual(self.original.read_bytes(), self.original_bytes)
        self.assertFalse(revised.with_name("approval.json").exists())
        digest = hashlib.sha256(revised.read_bytes()).hexdigest()
        self.assertTrue(design_plan.approve_design(revised, digest).is_file())

    def test_context_change_during_revision_stops(self):
        def model(prompt):
            design_plan.read_context.return_value = "CHANGED DURING REQUEST"
            return json.dumps(self.proposal)

        with self.assertRaises(RuntimeError):
            design_plan.revise_design(self.original, "Fix it.", model)
        self.assertEqual(self.original.read_bytes(), self.original_bytes)
        for folder in (self.root / "outputs").iterdir():
            if folder != self.original.parent:
                self.assertFalse((folder / "design.json").exists())

    def test_source_change_during_generation_stops(self):
        def model(prompt):
            self.original.write_bytes(self.original_bytes + b"\n")
            return json.dumps(self.proposal)

        with self.assertRaises(RuntimeError):
            design_plan.revise_design(self.original, "Fix it.", model)
        for folder in (self.root / "outputs").iterdir():
            if folder != self.original.parent:
                self.assertFalse((folder / "design.json").exists())

    def test_invalid_response_retries_with_review_feedback(self):
        model = Mock(side_effect=["invalid", json.dumps(self.proposal)])
        revised = design_plan.revise_design(
            self.original, "Check the boundary.", model
        )
        self.assertTrue(revised.is_file())
        self.assertEqual(model.call_count, 2)
        for call in model.call_args_list:
            self.assertIn("Check the boundary.", call.args[0])
        self.assertIn("이전 구조 검사", model.call_args_list[1].args[0])

    def test_failure_preserves_original_and_review_logs(self):
        model = Mock(return_value="invalid")
        with self.assertRaises(RuntimeError):
            design_plan.revise_design(self.original, "Fix the condition.", model)
        self.assertEqual(model.call_count, 3)
        self.assertEqual(self.original.read_bytes(), self.original_bytes)
        folders = [
            folder for folder in (self.root / "outputs").iterdir()
            if folder != self.original.parent
        ]
        self.assertEqual(len(folders), 1)
        self.assertTrue((folders[0] / "revision.json").is_file())
        self.assertTrue((folders[0] / "request.json").is_file())
        self.assertFalse((folders[0] / "design.json").exists())
        self.assertEqual(len(list(folders[0].glob("answer_*.txt"))), 3)

    def test_revised_design_can_be_revised_again(self):
        first = design_plan.revise_design(
            self.original, "First review.", self.model()
        )
        second = design_plan.revise_design(
            first, "Second review.", self.model()
        )
        envelope = json.loads(second.read_bytes())
        self.assertEqual(
            envelope["revision"]["source"],
            str(first.relative_to(self.root)),
        )
        self.assertEqual(
            envelope["revision"]["source_sha256"],
            hashlib.sha256(first.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            envelope["request"], json.loads(self.original_bytes)["request"]
        )

    def test_changed_original_requirements_are_rejected(self):
        model = self.model()
        with self.assertRaises(ValueError):
            design_plan.generate_design(
                "Implement recovery.",
                ["Different requirement."],
                "sandbox",
                model=model,
                previous=self.original,
                feedback="Change the requirement.",
            )
        model.assert_not_called()

    def test_revision_outside_outputs_is_rejected(self):
        model = self.model()
        with self.assertRaises(ValueError):
            design_plan.revise_design(
                self.root / "design.json", "Fix it.", model
            )
        model.assert_not_called()


if __name__ == "__main__":
    unittest.main()
