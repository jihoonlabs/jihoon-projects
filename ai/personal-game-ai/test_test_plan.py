import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import test_plan


class TestPlanTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        folder = self.root / "outputs" / "design_fixture"
        folder.mkdir(parents=True)
        self.source = folder / "design.json"
        self.source.write_bytes(b"original design")
        self.approval = folder / "approval.json"
        self.approval.write_text(json.dumps({
            "design_sha256": hashlib.sha256(b"original design").hexdigest(),
            "approved_at": "2026-10-04",
        }))
        self.envelope = {
            "context": "CONTEXT",
            "request": {
                "goal": "Recover health.",
                "requirements": {"R1": "Return bounded recovery."},
                "area": "sandbox",
            },
            "design": {"files": [{
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
            }]},
        }
        self.proposal = {"files": [{
            "id": "001",
            "filename": "test_health.py",
            "code": (
                "import unittest\n"
                "from health import heal\n\n"
                "class HealthTests(unittest.TestCase):\n"
                "    def test_limit(self):\n"
                "        self.assertEqual(heal(8, 5, 10), 10)\n"
            ),
            "covers": [{"check": 1, "method": "test_limit"}],
        }]}
        for module, name, value in (
            (test_plan, "BASE_DIR", self.root),
            (test_plan, "read_context", Mock(return_value="CONTEXT")),
        ):
            patcher = patch.object(module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        def read_design(path):
            path = Path(path)
            return path, path.read_bytes(), copy.deepcopy(self.envelope)

        patcher = patch.object(
            test_plan.design_plan, "read_design", side_effect=read_design
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def generate(self, model=None):
        return test_plan.generate_tests(
            self.source,
            model=model if model is not None else Mock(
                return_value=json.dumps(self.proposal)
            ),
        )

    def validate(self):
        return test_plan.validate_candidate(
            self.proposal, self.envelope["design"]
        )

    def confirm(self, path):
        return test_plan.confirm_tests(
            path, hashlib.sha256(path.read_bytes()).hexdigest()
        )

    def test_generation_preserves_source_and_does_not_save_executable_file(self):
        before = self.source.read_bytes()
        path = self.generate()
        record = json.loads(path.read_bytes())
        self.assertEqual(record["tests"], self.proposal)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(list(path.parent.glob("*.py")), [])
        self.assertTrue((path.parent / "test_health.py.txt").is_file())
        self.assertFalse(path.with_name("confirmation.json").exists())

    def test_missing_approval_blocks_model(self):
        self.approval.unlink()
        model = Mock()
        with self.assertRaises(FileNotFoundError):
            self.generate(model)
        model.assert_not_called()

    def test_wrong_approval_blocks_model(self):
        self.approval.write_text('{"design_sha256":"wrong"}')
        model = Mock()
        with self.assertRaises(ValueError):
            self.generate(model)
        model.assert_not_called()

    def test_generation_profile_candidate_validation_is_applied(self):
        with patch.object(
            test_plan.generation_profile, "validate_tests"
        ) as profile:
            self.generate()
        profile.assert_called_once()
        args = profile.call_args.args
        self.assertEqual(args[0], "sandbox")
        self.assertEqual(args[1], self.proposal)
        self.assertEqual(args[2], self.envelope["design"])
        self.assertEqual(len(args), 3)

    def test_generation_profile_prompt_is_included(self):
        model = Mock(return_value=json.dumps(self.proposal))
        with patch.object(
            test_plan.generation_profile,
            "test_prompt",
            return_value="PROFILE TEST",
        ):
            self.generate(model)
        self.assertIn("PROFILE TEST", model.call_args.args[0])

    def test_invalid_response_retries(self):
        model = Mock(side_effect=["invalid", json.dumps(self.proposal)])
        self.assertTrue(self.generate(model).is_file())
        self.assertEqual(model.call_count, 2)

    def test_failure_keeps_logs_without_manifest(self):
        with self.assertRaises(RuntimeError):
            self.generate(Mock(return_value="invalid"))
        folders = list((self.root / "outputs").glob("test_plan_*"))
        self.assertEqual(len(folders), 1)
        self.assertEqual(len(list(folders[0].glob("answer_*.txt"))), 3)
        self.assertFalse((folders[0] / "tests.json").exists())

    def test_invalid_filename_is_rejected(self):
        self.proposal["files"][0]["filename"] = "../test_health.py"
        with self.assertRaises(ValueError):
            self.validate()

    def test_syntax_error_is_rejected(self):
        self.proposal["files"][0]["code"] = "invalid python!"
        with self.assertRaises(ValueError):
            self.validate()

    def test_missing_assertion_is_rejected(self):
        self.proposal["files"][0]["code"] = (
            "import unittest\nfrom health import heal\n"
            "class Tests(unittest.TestCase):\n"
            "    def test_limit(self):\n        pass\n"
        )
        with self.assertRaises(ValueError):
            self.validate()

    def test_skip_decorator_is_rejected(self):
        self.proposal["files"][0]["code"] = (
            "import unittest\nfrom health import heal\n"
            "class Tests(unittest.TestCase):\n"
            "    @unittest.skip('skip')\n"
            "    def test_limit(self):\n"
            "        self.assertEqual(heal(8, 5, 10), 10)\n"
        )
        with self.assertRaises(ValueError):
            self.validate()

    def test_missing_case_link_is_rejected(self):
        self.proposal["files"][0]["covers"] = []
        with self.assertRaises(ValueError):
            self.validate()

    def test_unknown_method_is_rejected(self):
        self.proposal["files"][0]["covers"][0]["method"] = "test_missing"
        with self.assertRaises(ValueError):
            self.validate()

    def test_source_change_during_generation_stops(self):
        def model(prompt):
            self.source.write_bytes(b"external change")
            return json.dumps(self.proposal)

        with self.assertRaises(ValueError):
            self.generate(model)
        self.assertEqual(self.source.read_bytes(), b"external change")

    def test_context_change_during_generation_stops(self):
        def model(prompt):
            test_plan.read_context.return_value = "OTHER"
            return json.dumps(self.proposal)

        with self.assertRaises(RuntimeError):
            self.generate(model)

    def test_confirmation_records_digest(self):
        path = self.generate()
        confirmation = self.confirm(path)
        self.assertEqual(
            json.loads(confirmation.read_bytes())["tests_sha256"],
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )

    def test_old_digest_cannot_confirm_changed_manifest(self):
        path = self.generate()
        old = hashlib.sha256(path.read_bytes()).hexdigest()
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaises(RuntimeError):
            test_plan.confirm_tests(path, old)

    def test_changed_candidate_copy_blocks_confirmation(self):
        path = self.generate()
        (path.parent / "test_health.py.txt").write_text("# changed\n")
        with self.assertRaises(RuntimeError):
            self.confirm(path)

    def test_changed_context_blocks_confirmation(self):
        path = self.generate()
        test_plan.read_context.return_value = "OTHER"
        with self.assertRaises(RuntimeError):
            self.confirm(path)

    def test_existing_confirmation_is_preserved(self):
        path = self.generate()
        confirmation = self.confirm(path)
        before = confirmation.read_bytes()
        with self.assertRaises(FileExistsError):
            self.confirm(path)
        self.assertEqual(confirmation.read_bytes(), before)

    def test_confirmation_outside_outputs_is_rejected(self):
        with self.assertRaises(ValueError):
            test_plan.confirm_tests(self.root / "tests.json", "unused")


if __name__ == "__main__":
    unittest.main()
