import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import design_plan


class DesignPlanTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.sandbox = self.root / "sandbox"
        self.sandbox.mkdir()
        self.requirements = ["Clamp the returned value."]
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
                    "case": "hp=8, amount=5, maximum=10",
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

    def validate(self, proposal=None):
        return design_plan.validate_design(
            self.proposal if proposal is None else proposal,
            self.requirements,
            "sandbox",
        )

    def generate(self, model=None):
        return design_plan.generate_design(
            "Implement health recovery.",
            self.requirements,
            "sandbox",
            model=model or (lambda prompt: json.dumps(self.proposal)),
        )

    def sha256(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_thumby_target_structure_follows_generic_example_on_retry(self):
        game = self.root / "ThumbyGrowth"
        game.mkdir()
        config = self.root / "target.json"
        config.write_text(json.dumps({"generation_profile": "thumby",
                                      "edit_directory": "micropython/ThumbyGrowth"}))
        requirements = ["Return state.", "Use a finite device frame."]
        valid = copy.deepcopy(self.proposal)
        valid["files"][0]["checks"].append({"requirement": "R2", "case": "state", "expected": "state"})
        valid["files"].append({"id": "002", "filename": "ThumbyGrowth.py",
            "functions": [{"name": "main_loop", "parameters": [], "behavior": "Runtime loop."},
                          {"name": "step_frame", "parameters": ["state"], "behavior": "Finite frame."}],
            "checks": [{"requirement": "R2", "case": "fake input", "expected": "state"}],
            "depends_on": ["001"]})
        captured = []

        def model(prompt):
            captured.append(prompt)
            return json.dumps(self.proposal if len(captured) == 1 else valid)

        with patch.object(design_plan.edit_loop, "game_location", return_value=(game, self.root)), \
                patch.object(design_plan.generation_profile, "CONFIG_PATH", config):
            path = design_plan.generate_design("Game", requirements, "game", model=model)
        self.assertEqual(len(captured), 2)
        for prompt in captured:
            self.assertGreater(prompt.index("# 실제 대상에 맞는 필수 설계 구조"), prompt.index('"filename":"module.py"'))
            self.assertIn("엔트리는 정확히 ThumbyGrowth.py", prompt)
            self.assertIn('["R1", "R2"]', prompt)
            self.assertIn("숨겨진 변경 가능한 전역 상태", prompt)
            self.assertIn("순수 규칙은 기기 저장", prompt)
        self.assertIn("폴더명과 같은 엔트리", captured[1])
        self.assertEqual(json.loads(path.read_text())["design"], valid)
        self.assertFalse(list(game.iterdir()))

    def test_non_thumby_structure_guidance_is_empty(self):
        self.assertEqual(design_plan.generation_profile.design_structure("sandbox", self.sandbox, self.requirements), "")
        with patch.object(design_plan.generation_profile, "current_profile", return_value=None):
            self.assertEqual(design_plan.generation_profile.design_structure("game", self.sandbox, self.requirements), "")

    def test_valid_design_and_original_input_are_saved(self):
        path = self.generate()
        envelope = json.loads(path.read_text())
        self.assertEqual(
            envelope["request"]["requirements"],
            {"R1": self.requirements[0]},
        )
        self.assertEqual(envelope["design"], self.proposal)
        self.assertEqual(list(self.sandbox.iterdir()), [])

    def test_missing_requirement_is_rejected(self):
        self.requirements.append("Keep inventory unchanged when full.")
        with self.assertRaises(ValueError):
            self.validate()

    def test_unknown_requirement_is_rejected(self):
        self.proposal["files"][0]["checks"][0]["requirement"] = "R99"
        with self.assertRaises(ValueError):
            self.validate()

    def test_unsafe_filenames_are_rejected(self):
        for name in (
            "../health.py", "/tmp/health.py", "nested/health.py",
            "test_health.py", "health.txt", "bad-name.py",
        ):
            with self.subTest(name=name):
                proposal = copy.deepcopy(self.proposal)
                proposal["files"][0]["filename"] = name
                with self.assertRaises(ValueError):
                    self.validate(proposal)

    def test_existing_file_is_preserved(self):
        path = self.sandbox / "health.py"
        path.write_text("# existing\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.validate()
        self.assertEqual(path.read_text(), "# existing\n")

    def test_symlink_target_is_rejected(self):
        (self.sandbox / "health.py").symlink_to(
            self.root / "missing.py"
        )
        with self.assertRaises(ValueError):
            self.validate()

    def test_deleted_tracked_file_is_rejected(self):
        design_plan.edit_loop.git_output.return_value = "health.py"
        with self.assertRaises(ValueError):
            self.validate()

    def test_duplicate_filename_is_rejected(self):
        second = copy.deepcopy(self.proposal["files"][0])
        second["id"] = "002"
        self.proposal["files"].append(second)
        with self.assertRaises(ValueError):
            self.validate()

    def test_invalid_dependencies_are_rejected(self):
        for dependencies in (["missing"], ["001"]):
            with self.subTest(dependencies=dependencies):
                self.proposal["files"][0]["depends_on"] = dependencies
                with self.assertRaises(ValueError):
                    self.validate()

    def test_dependency_order_is_normalized(self):
        first = self.proposal["files"][0]
        second = copy.deepcopy(first)
        second.update(
            id="002", filename="item.py", depends_on=["001"]
        )
        proposal = {"files": [second, first]}
        result = self.validate(proposal)
        self.assertEqual(
            [item["id"] for item in result["files"]], ["001", "002"]
        )

    def test_generation_profile_design_validation_is_applied(self):
        with patch.object(
            design_plan.generation_profile, "validate_design"
        ) as profile:
            self.validate()
        profile.assert_called_once_with(
            "sandbox", self.proposal["files"], self.sandbox
        )

    def test_generation_profile_prompt_is_included(self):
        model = Mock(return_value=json.dumps(self.proposal))
        with patch.object(
            design_plan.generation_profile,
            "design_prompt",
            return_value="PROFILE DESIGN",
        ):
            self.generate(model)
        self.assertIn("PROFILE DESIGN", model.call_args.args[0])

    def test_invalid_json_retries(self):
        model = Mock(side_effect=["invalid", json.dumps(self.proposal)])
        self.assertTrue(self.generate(model).is_file())
        self.assertEqual(model.call_count, 2)

    def test_failed_generation_keeps_logs_without_design(self):
        with self.assertRaises(RuntimeError):
            self.generate(lambda prompt: "invalid")
        folders = list((self.root / "outputs").glob("design_*"))
        self.assertEqual(len(folders), 1)
        self.assertFalse((folders[0] / "design.json").exists())
        self.assertEqual(len(list(folders[0].glob("answer_*.txt"))), 2)

    def test_length_failure_keeps_partial_response_and_prompt(self):
        from ask_ai import ModelLengthError
        result = {"done_reason": "length", "message": {"content": '{"files":['}}
        model = Mock(side_effect=ModelLengthError(result))
        with self.assertRaisesRegex(RuntimeError, "출력 한도 중단"):
            self.generate(model)
        folder = next((self.root / "outputs").glob("design_*"))
        self.assertEqual(model.call_count, 1)
        self.assertEqual(json.loads((folder / "response_1.json").read_text()), result)
        self.assertTrue((folder / "prompt_1.txt").is_file())
        self.assertEqual((folder / "context.txt").read_text(), "CONTEXT")
        self.assertEqual(json.loads((folder / "attempt_1.json").read_text())["status"], "output_limit")
        self.assertFalse((folder / "design.json").exists())
        self.assertFalse((folder / "approval.json").exists())

    def test_different_invalid_responses_retain_three_attempt_bound(self):
        model = Mock(side_effect=["bad one", "bad two", "bad three"])
        with self.assertRaisesRegex(RuntimeError, "설계 생성 실패"):
            self.generate(model)
        self.assertEqual(model.call_count, 3)
        self.assertIn("Expecting value", model.call_args_list[1].args[0])

    def test_model_error_is_recorded_without_automatic_retry(self):
        model = Mock(side_effect=RuntimeError("connection failed"))
        with self.assertRaisesRegex(RuntimeError, "connection failed"):
            self.generate(model)
        folder = next((self.root / "outputs").glob("design_*"))
        self.assertEqual(model.call_count, 1)
        record = json.loads((folder / "attempt_1.json").read_text())
        self.assertEqual(record["status"], "model_error")
        self.assertFalse(record["automatic_approval"])

    def test_directory_change_during_generation_stops(self):
        def model(prompt):
            (self.sandbox / "external.py").write_text("# external\n")
            return json.dumps(self.proposal)

        with self.assertRaises(RuntimeError):
            self.generate(model)
        self.assertTrue((self.sandbox / "external.py").exists())

    def test_approval_records_exact_digest(self):
        path = self.generate()
        expected = self.sha256(path)
        approval = design_plan.approve_design(path, expected)
        self.assertEqual(
            json.loads(approval.read_text())["design_sha256"], expected
        )
        self.assertEqual(list(self.sandbox.iterdir()), [])

    def test_changed_design_cannot_be_approved_with_old_digest(self):
        path = self.generate()
        expected = self.sha256(path)
        path.write_text(path.read_text() + "\n")
        with self.assertRaises(RuntimeError):
            design_plan.approve_design(path, expected)
        self.assertFalse(path.with_name("approval.json").exists())

    def test_changed_context_blocks_approval(self):
        path = self.generate()
        expected = self.sha256(path)
        design_plan.read_context.return_value = "OTHER"
        with self.assertRaises(RuntimeError):
            design_plan.approve_design(path, expected)

    def test_existing_approval_is_not_overwritten(self):
        path = self.generate()
        expected = self.sha256(path)
        approval = design_plan.approve_design(path, expected)
        before = approval.read_bytes()
        with self.assertRaises(FileExistsError):
            design_plan.approve_design(path, expected)
        self.assertEqual(approval.read_bytes(), before)

    def test_approval_outside_output_is_rejected(self):
        with self.assertRaises(ValueError):
            design_plan.approve_design(
                self.root / "design.json", "unused"
            )


if __name__ == "__main__":
    unittest.main()

