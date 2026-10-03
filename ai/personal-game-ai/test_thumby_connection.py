import json
import subprocess
import unittest
from unittest.mock import patch

import edit_loop
import test_edit_loop

REAL_RUN_TEST = edit_loop.run_test


class ThumbyConnectionTests(unittest.TestCase):
    git = test_edit_loop.EditLoopTests.git
    mock = test_edit_loop.EditLoopTests.mock
    proposal = test_edit_loop.EditLoopTests.proposal

    def setUp(self):
        test_edit_loop.EditLoopTests.setUp(self)
        self.game = self.root / "micropython" / "street_rpg"
        self.game.mkdir(parents=True)
        self.game_target = self.game / "movement.py"
        self.game_test = self.game / "test_movement.py"
        self.game_original = (
            "def move(x, direction):\n"
            "    raise NotImplementedError\n"
        )
        self.game_target.write_text(self.game_original, encoding="utf-8")
        self.game_test.write_text("# fixed game test\n", encoding="utf-8")
        self.mock("GAME_DIR", new=self.game)
        self.git("add", "micropython/street_rpg")
        self.git(
            "-c", "user.name=Test",
            "-c", "user.email=test@example.invalid",
            "-c", "commit.gpgsign=false",
            "commit", "-m", "game fixture",
        )

    def run_game(self):
        return edit_loop.run_edit(
            "game/movement.py", "Implement move.", "test_movement"
        )

    def test_game_edit_uses_game_test_directory(self):
        code = "def move(x, direction):\n    return x + direction\n"
        self.model.return_value = self.proposal(code)
        self.runner.return_value = (True, "passed")
        result = self.run_game()

        self.assertEqual(result["status"], "tests_passed")
        self.assertEqual(self.game_target.read_text(), code)
        self.assertEqual(self.game_test.read_text(), "# fixed game test\n")
        self.assertEqual(self.target.read_text(), self.original)
        self.runner.assert_called_once_with(
            self.root / result["output"] / "test_1.txt",
            "test_movement",
            work_dir=self.game,
        )
        self.assertFalse((self.root / ".edit_loop.lock").exists())

    def test_game_question_restores_and_can_resume(self):
        code = "def move(x, direction):\n    return x + direction\n"
        self.model.side_effect = [
            self.proposal(code),
            json.dumps({"action": "question", "question": "Choose?"}),
            self.proposal(code),
        ]
        self.runner.side_effect = [(False, "FAILED"), (True, "passed")]

        result = self.run_game()
        self.assertEqual(result["status"], "waiting_for_user")
        self.assertEqual(self.game_target.read_text(), self.game_original)
        edit_loop.prepare_edit(
            "game/movement.py", "Resume.", "test_movement"
        )

        resumed = self.run_game()
        self.assertEqual(resumed["status"], "tests_passed")
        self.assertEqual(self.game_target.read_text(), code)
        self.assertEqual(self.game_test.read_text(), "# fixed game test\n")

    def test_dirty_game_target_blocks_model(self):
        self.game_target.write_text("# existing change\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.run_game()
        self.model.assert_not_called()
        self.assertEqual(self.game_target.read_text(), "# existing change\n")

    def test_staged_game_test_blocks_model(self):
        self.game_test.write_text("# changed test\n", encoding="utf-8")
        self.git("add", "micropython/street_rpg/test_movement.py")
        with self.assertRaises(RuntimeError):
            self.run_game()
        self.model.assert_not_called()

    def test_untracked_game_target_is_rejected(self):
        (self.game / "other.py").write_text("value = 1\n", encoding="utf-8")
        with self.assertRaises(subprocess.CalledProcessError):
            edit_loop.run_edit(
                "game/other.py", "Implement.", "test_movement"
            )
        self.model.assert_not_called()

    def test_invalid_game_paths_are_rejected(self):
        for target in (
            "game/../movement.py",
            "game/nested/movement.py",
            "game/test_movement.py",
            "other/movement.py",
            str(self.game_target),
        ):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    edit_loop.run_edit(
                        target, "Implement.", "test_movement"
                    )
        self.model.assert_not_called()

    def test_symlink_game_file_is_rejected(self):
        original = self.game / "original.py"
        self.game_target.rename(original)
        self.game_target.symlink_to(original)
        with self.assertRaises(ValueError):
            self.run_game()
        self.model.assert_not_called()

    def test_symlink_game_test_is_rejected(self):
        original = self.game / "original_test.py"
        self.game_test.rename(original)
        self.game_test.symlink_to(original)
        with self.assertRaises(ValueError):
            self.run_game()
        self.model.assert_not_called()

    def test_symlink_intermediate_directory_is_rejected(self):
        parent = self.game.parent
        original = parent.with_name("original_micropython")
        parent.rename(original)
        parent.symlink_to(original, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_game()
        self.model.assert_not_called()

    def test_external_game_change_is_preserved(self):
        def model(prompt):
            self.game_target.write_text("# user edit\n", encoding="utf-8")
            return self.proposal("value = 1\n")

        self.model.side_effect = model
        with self.assertRaises(RuntimeError):
            self.run_game()
        self.assertEqual(self.game_target.read_text(), "# user edit\n")
        self.runner.assert_not_called()

    def test_docker_mounts_only_selected_game_directory(self):
        # setUpで差し替える前の関数でDockerコマンドを検査する。
        with patch.object(edit_loop.subprocess, "run") as docker:
            docker.return_value.returncode = 0
            passed, _ = REAL_RUN_TEST(
                self.root / "docker.txt",
                "test_movement",
                work_dir=self.game,
            )
            command = docker.call_args.args[0]

        self.assertTrue(passed)
        self.assertEqual(
            command[command.index("--mount") + 1],
            f"type=bind,source={self.game.resolve()},target=/work,readonly",
        )
        self.assertEqual(command[command.index("--network") + 1], "none")
        self.assertIn("--read-only", command)
        self.assertEqual(command[-1], "test_movement")

    def test_docker_rejects_unapproved_directory(self):
        with patch.object(edit_loop.subprocess, "run") as docker:
            with self.assertRaises(ValueError):
                REAL_RUN_TEST(
                    self.root / "docker.txt",
                    "test_movement",
                    work_dir=self.root,
                )
            docker.assert_not_called()


if __name__ == "__main__":
    unittest.main()