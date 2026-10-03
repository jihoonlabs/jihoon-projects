import json
import unittest

import edit_loop
import test_thumby_connection


class GameConfigTests(unittest.TestCase):
    git = test_thumby_connection.ThumbyConnectionTests.git
    mock = test_thumby_connection.ThumbyConnectionTests.mock
    proposal = test_thumby_connection.ThumbyConnectionTests.proposal
    run_game = test_thumby_connection.ThumbyConnectionTests.run_game

    def setUp(self):
        test_thumby_connection.ThumbyConnectionTests.setUp(self)
        self.config = self.root / "target.json"
        self.mock("GAME_DIR", new=None)
        self.mock("CONFIG_PATH", new=self.config)
        self.write_config("micropython/street_rpg")

    def write_config(self, directory):
        config = {"repository_root": "."}
        if directory is not None:
            config["edit_directory"] = directory
        self.config.write_text(json.dumps(config), encoding="utf-8")

    def test_config_selects_game_directory(self):
        target, test = edit_loop.resolve_files(
            "game/movement.py", "test_movement"
        )
        self.assertEqual(target, self.game_target.resolve())
        self.assertEqual(test, self.game_test.resolve())

    def test_missing_game_setting_blocks_model(self):
        self.write_config(None)
        with self.assertRaises(ValueError):
            self.run_game()
        self.model.assert_not_called()

    def test_invalid_settings_are_rejected(self):
        for directory in (
            "",
            ".",
            "../outside",
            str(self.game),
            123,
            [],
        ):
            with self.subTest(directory=directory):
                self.write_config(directory)
                with self.assertRaises(ValueError):
                    edit_loop.resolve_files(
                        "game/movement.py", "test_movement"
                    )
        self.model.assert_not_called()

    def test_repository_root_must_be_git_root(self):
        self.config.write_text(
            json.dumps({
                "repository_root": "micropython/street_rpg",
                "edit_directory": "other",
            }),
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            edit_loop.resolve_files("game/movement.py", "test_movement")

    def test_another_game_can_be_selected(self):
        other = self.root / "micropython" / "thumby" / "other_game"
        other.mkdir(parents=True)
        (other / "movement.py").write_text("value = 1\n", encoding="utf-8")
        (other / "test_movement.py").write_text(
            "# fixed test\n", encoding="utf-8"
        )
        self.write_config("micropython/thumby/other_game")

        target, test = edit_loop.resolve_files(
            "game/movement.py", "test_movement"
        )
        self.assertEqual(target, (other / "movement.py").resolve())
        self.assertEqual(test, (other / "test_movement.py").resolve())

    def test_configured_symlink_directory_is_rejected(self):
        link = self.root / "linked_game"
        link.symlink_to(self.game, target_is_directory=True)
        self.write_config("linked_game")
        with self.assertRaises(ValueError):
            self.run_game()
        self.model.assert_not_called()

    def test_configured_untracked_target_is_rejected(self):
        other = self.game / "other.py"
        other.write_text("value = 1\n", encoding="utf-8")
        import subprocess

        with self.assertRaises(subprocess.CalledProcessError):
            edit_loop.run_edit(
                "game/other.py", "Implement.", "test_movement"
            )
        self.model.assert_not_called()

    def test_game_setting_change_during_model_call_stops(self):
        other = self.root / "micropython" / "other_game"
        other.mkdir(parents=True)
        (other / "movement.py").write_text("value = 1\n", encoding="utf-8")
        (other / "test_movement.py").write_text(
            "# fixed test\n", encoding="utf-8"
        )

        def model(prompt):
            self.write_config("micropython/other_game")
            return self.proposal("value = 2\n")

        self.model.side_effect = model
        with self.assertRaises(RuntimeError):
            self.run_game()
        self.assertEqual(self.game_target.read_text(), self.game_original)
        self.assertEqual((other / "movement.py").read_text(), "value = 1\n")
        self.runner.assert_not_called()

    def test_sandbox_works_without_game_setting(self):
        self.write_config(None)
        target, test = edit_loop.resolve_files(
            "sandbox/clamp.py", "test_clamp"
        )
        self.assertEqual(target, self.target)
        self.assertEqual(test, self.test)


if __name__ == "__main__":
    unittest.main()