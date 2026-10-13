import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import edit_loop
import game_chat
import generation_profile


class GameChatTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.base = self.root / "ai" / "personal-game-ai"
        self.game = self.root / "micropython" / "Thumby" / "ThumbyGrowth"
        self.base.mkdir(parents=True)
        self.game.mkdir(parents=True)
        (self.root / "AGENTS.md").write_text("Keep game goal and fixed tests.\n")
        self.document = self.root / "docs" / "game.md"
        self.document.parent.mkdir()
        self.document.write_text("Make Thumby game.\n")
        self.config = self.base / "target.json"
        self.config.write_text(json.dumps({
            "repository_root": "../..", "expected_branch": "test-epic",
            "branch_document": "docs/game.md", "code_files": [],
            "max_context_chars": 12000, "generation_profile": "thumby",
            "edit_directory": "micropython/Thumby/ThumbyGrowth",
        }))
        self.target = self.game / "rules.py"
        self.original = "def step():\n    return 1\n"
        self.target.write_text(self.original)
        (self.game / "ThumbyGrowth.py").write_text("def frame():\n    return 1\n")
        self.fixed = self.game / "test_floor_movement.py"
        self.fixed.write_text("# fixed tests\n")
        self.git("init", "-q")
        self.git("checkout", "-qb", "test-epic")
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
        self.model = Mock(side_effect=AssertionError("Unexpected model call"))
        self.runner = Mock(return_value=(True, "17 tests passed"))
        self.docker = Mock()
        for owner, name, value in (
            (edit_loop, "BASE_DIR", self.base), (edit_loop, "CONFIG_PATH", self.config),
            (edit_loop, "read_context", lambda: game_chat.read_context(self.config)),
            (edit_loop, "run_test", self.runner),
            (game_chat, "docker_ready", self.docker),
            (generation_profile, "CONFIG_PATH", self.config),
        ):
            patcher = patch.object(owner, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.chat = game_chat.GameChat(self.base, model=self.model)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              capture_output=True, text=True)

    def proposal(self, code):
        return json.dumps({"action": "edit", "code": code})

    def edit_request(self):
        return json.dumps({"action": "edit", "target": "rules.py",
                           "instruction": "step의 반환값을 2로 바꿔줘."})

    def test_status_uses_actual_git_without_model_or_tests(self):
        self.target.write_text(self.original + "# local change\n")
        result = self.chat.turn("/status")
        self.assertEqual(result["status"], "inspected")
        self.assertEqual(result["branch"], "test-epic")
        self.assertIn("rules.py", result["git_changes"])
        self.model.assert_not_called()
        self.runner.assert_not_called()
        self.docker.assert_not_called()

    def test_natural_language_routes_without_claiming_model_execution(self):
        self.model.side_effect = None
        self.model.return_value = '{"action":"status"}'
        result = self.chat.turn("현재 게임 상태 확인해줘")
        self.assertEqual(result["status"], "inspected")
        self.assertIn(game_chat.GOAL, self.model.call_args.args[0])
        self.runner.assert_not_called()

    def test_read_is_actual_source_not_model_generated(self):
        result = self.chat.turn("/read rules.py")
        self.assertEqual(result["code"], self.original)
        self.model.assert_not_called()

    def test_rejects_commands_paths_tests_and_extra_fields(self):
        for proposal in (
            {"action": "shell", "command": "rm -rf ."},
            {"action": "read", "target": "../AGENTS.md"},
            {"action": "edit", "target": "test_floor_movement.py", "instruction": "skip"},
            {"action": "test", "command": "anything"},
            {"action": ["status"]},
        ):
            with self.subTest(proposal=proposal):
                with self.assertRaises(ValueError):
                    game_chat.validate_action(proposal, ("rules.py", "ThumbyGrowth.py"))

    def test_wrong_branch_blocks_before_model_or_record(self):
        self.git("checkout", "-qb", "other")
        with self.assertRaises(RuntimeError):
            self.chat.turn("수정해줘")
        self.model.assert_not_called()
        self.assertIsNone(self.chat.folder)

    def test_symlink_target_is_rejected(self):
        outside = self.root / "outside.py"
        outside.write_text(self.original)
        self.target.unlink()
        self.target.symlink_to(outside)
        with self.assertRaises(ValueError):
            self.chat.turn("/read rules.py")
        self.model.assert_not_called()

    def test_fixed_test_action_uses_existing_isolated_runner(self):
        result = self.chat.turn("/test")
        self.assertEqual(result["status"], "tests_passed")
        self.assertEqual(self.runner.call_args.args[1], "test_floor_movement")
        self.assertEqual(self.runner.call_args.kwargs["work_dir"], self.game)
        self.assertEqual(self.fixed.read_text(), "# fixed tests\n")

    def test_edit_connects_router_real_engine_and_fixed_tests(self):
        code = "def step():\n    return 2\n"
        self.model.side_effect = [self.edit_request(), self.proposal(code)]
        result = self.chat.turn("step의 반환값을 2로 바꿔줘")
        self.assertEqual(result["status"], "tests_passed")
        self.assertEqual(self.target.read_text(), code)
        self.assertEqual(self.runner.call_count, 2)
        self.assertEqual(self.fixed.read_text(), "# fixed tests\n")
        self.assertIn("rules.py", self.git("status", "--short").stdout)
        self.assertFalse((self.base / ".game_chat.lock").exists())

    def test_failed_candidates_restore_original(self):
        code = "def step():\n    return 0\n"
        self.model.side_effect = [self.edit_request()] + [self.proposal(code)] * 3
        self.runner.side_effect = [(True, "baseline passed")] + [(False, "failed")] * 3
        result = self.chat.turn("step의 반환값을 2로 바꿔줘")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.target.read_text(), self.original)
        self.assertEqual(self.fixed.read_text(), "# fixed tests\n")

    def test_external_changes_are_never_rolled_back(self):
        code = "def step():\n    return 2\n"
        self.model.side_effect = [self.edit_request(), self.proposal(code)]
        count = 0
        def checker(*args, **kwargs):
            nonlocal count
            count += 1
            if count == 2:
                self.target.write_text("# external editor\n")
            return True, "passed"
        self.runner.side_effect = checker
        with self.assertRaisesRegex(RuntimeError, "외부 변경"):
            self.chat.turn("step의 반환값을 2로 바꿔줘")
        self.assertEqual(self.target.read_text(), "# external editor\n")

    def test_baseline_failure_blocks_code_generation(self):
        self.model.side_effect = [self.edit_request()]
        self.runner.return_value = False, "baseline failed"
        result = self.chat.turn("step의 반환값을 2로 바꿔줘")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.model.call_count, 1)
        self.assertEqual(self.target.read_text(), self.original)

    def test_dirty_target_blocks_before_docker(self):
        self.target.write_text(self.original + "# dirty\n")
        self.model.side_effect = [self.edit_request()]
        with self.assertRaises(RuntimeError):
            self.chat.turn("step의 반환값을 2로 바꿔줘")
        self.docker.assert_not_called()
        self.runner.assert_not_called()

    def test_docker_unavailable_blocks_before_code_generation(self):
        self.model.side_effect = [self.edit_request()]
        self.docker.side_effect = RuntimeError("Docker unavailable")
        with self.assertRaises(RuntimeError):
            self.chat.turn("step의 반환값을 2로 바꿔줘")
        self.assertEqual(self.model.call_count, 1)
        self.assertEqual(self.target.read_text(), self.original)

    def test_question_answer_resumes_same_edit_instruction(self):
        self.model.side_effect = [self.edit_request(),
                                 '{"action":"question","question":"정수 2가 맞나요?"}',
                                 self.proposal("def step():\n    return 2\n")]
        first = self.chat.turn("step의 반환값을 2로 바꿔줘")
        self.assertEqual(first["status"], "waiting_for_user")
        self.assertEqual(self.target.read_text(), self.original)
        second = self.chat.turn("응 정수 2로")
        self.assertEqual(second["status"], "tests_passed")
        self.assertIn("정수 2가 맞나요?", self.model.call_args.args[0])
        self.assertIn("응 정수 2로", self.model.call_args.args[0])
        self.assertIsNone(self.chat.pending)

    def test_cancel_does_not_treat_next_message_as_previous_answer(self):
        self.chat.pending = {"target": "rules.py", "instruction": "edit", "question": "why?"}
        self.chat.turn("/cancel")
        self.assertIsNone(self.chat.pending)
        self.model.assert_not_called()

    def test_invalid_thumby_api_is_blocked_before_writing(self):
        self.model.side_effect = [self.edit_request(), self.proposal("import thumbyColor\n")]
        with self.assertRaises(ValueError):
            self.chat.turn("step의 반환값을 2로 바꿔줘")
        self.assertEqual(self.target.read_text(), self.original)
        self.assertEqual(self.runner.call_count, 1)

    def test_model_json_errors_release_lock(self):
        self.model.side_effect = None
        self.model.return_value = "I executed it!"
        with self.assertRaises(ValueError):
            self.chat.turn("현재 상태")
        self.assertFalse((self.base / ".game_chat.lock").exists())
        self.assertEqual(self.target.read_text(), self.original)
        records = [json.loads(line) for line in (self.chat.folder / "turns.jsonl").read_text().splitlines()]
        self.assertEqual(records[-1]["result"]["status"], "blocked")

    def test_changed_context_during_routing_blocks_action(self):
        def route(prompt):
            self.document.write_text("changed context")
            return '{"action":"test"}'
        self.model.side_effect = route
        with self.assertRaises(RuntimeError):
            self.chat.turn("검사해줘")
        self.runner.assert_not_called()

    def test_existing_session_lock_is_preserved(self):
        lock = self.base / ".game_chat.lock"
        lock.write_text("other session")
        with self.assertRaises(RuntimeError):
            self.chat.turn("/status")
        self.assertEqual(lock.read_text(), "other session")
        self.assertIsNone(self.chat.folder)


if __name__ == "__main__":
    unittest.main()
