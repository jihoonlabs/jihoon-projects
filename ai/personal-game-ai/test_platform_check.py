import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import create_loop
import edit_loop
import platform_check
import test_thumby_connection

STAND_IN = platform_check.PLATFORM_DIR / "thumby" / "thumby.py"


def load_stand_in():
    # 本物のthumbyと混同しないよう、別名でファイルから読み込む。
    spec = importlib.util.spec_from_file_location("thumby_stand_in", STAND_IN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ThumbyStandInTests(unittest.TestCase):
    def setUp(self):
        self.thumby = load_stand_in()
        self.thumby._reset_for_test()
        self.display = self.thumby.display
        self.sim = self.thumby.sim

    def test_screen_size_and_pixels(self):
        self.assertEqual((self.display.width, self.display.height), (72, 40))
        self.display.setPixel(71, 39, 1)
        self.assertEqual(self.display.getPixel(71, 39), 1)
        self.assertEqual(self.sim.out_of_bounds, 0)
        self.display.setPixel(72, 0, 1)
        self.display.setPixel(0, -1, 1)
        self.assertEqual(self.sim.out_of_bounds, 2)
        self.assertEqual(self.display.getPixel(72, 0), 0)

    def test_fill_and_rectangles(self):
        self.display.fill(1)
        self.assertEqual(self.display.getPixel(30, 20), 1)
        self.display.fill(0)
        self.display.drawRectangle(1, 1, 4, 3, 1)
        self.assertEqual(self.display.getPixel(1, 1), 1)
        self.assertEqual(self.display.getPixel(4, 3), 1)
        self.assertEqual(self.display.getPixel(2, 2), 0)
        self.display.drawFilledRectangle(10, 10, 2, 2, 1)
        self.assertEqual(self.display.getPixel(11, 11), 1)
        self.display.drawLine(0, 30, 5, 30, 1)
        self.assertEqual(self.display.getPixel(5, 30), 1)

    def test_text_box_and_overlap(self):
        self.display.drawText("E10", 42, 0, 1)
        self.display.drawFilledRectangle(56, 0, 10, 3, 1)
        self.assertEqual(self.sim.text_boxes[0][:5], ("E10", 42, 0, 17, 7))
        self.display.drawText("HP", 50, 2, 1)
        self.assertEqual(self.sim.text_overlaps(), [("E10", "HP")])
        self.display.update()
        self.display.drawText("OK", 50, 2, 1)
        self.assertEqual(self.sim.text_overlaps(), [])

    def test_text_past_right_edge_counts_out_of_bounds(self):
        self.display.drawText("LONGTEXT", 40, 0, 1)
        self.assertEqual(self.sim.out_of_bounds, 1)

    def test_blit_uses_vlsb_key_and_mirror(self):
        # 2列x9行: 1列目は上端(bit0)と9行目(2ページ目のbit0)だけ点灯。
        data = bytearray([0b00000001, 0, 0b00000001, 0])
        self.display.blit(data, 0, 0, 2, 9, -1, 0, 0)
        self.assertEqual(self.display.getPixel(0, 0), 1)
        self.assertEqual(self.display.getPixel(0, 8), 1)
        self.assertEqual(self.display.getPixel(1, 0), 0)

        self.display.fill(1)
        self.display.blit(data, 0, 0, 2, 9, 0, 0, 0)
        self.assertEqual(self.display.getPixel(1, 0), 1)

        self.display.fill(0)
        self.display.blit(data, 10, 0, 2, 9, -1, 1, 0)
        self.assertEqual(self.display.getPixel(11, 0), 1)
        self.assertEqual(self.display.getPixel(10, 0), 0)

    def test_short_bitmap_is_rejected(self):
        with self.assertRaises(ValueError):
            self.display.blit(bytearray(1), 0, 0, 2, 8, -1, 0, 0)

    def test_sprite_frames_wrap_and_draw(self):
        frames = bytearray([0b1, 0b0, 0b0, 0b1])
        sprite = self.thumby.Sprite(2, 8, frames, 3, 4)
        self.assertEqual(sprite.frameCount, 2)
        sprite.setFrame(3)
        self.assertEqual(sprite.getFrame(), 1)
        self.display.drawSprite(sprite)
        self.assertEqual(self.display.getPixel(4, 4), 1)
        self.assertEqual(self.display.getPixel(3, 4), 0)

    def test_buttons_pressed_and_just_pressed(self):
        self.sim.press("A", "L")
        self.assertTrue(self.thumby.buttonA.pressed())
        self.assertTrue(self.thumby.buttonA.justPressed())
        self.assertFalse(self.thumby.buttonA.justPressed())
        self.assertTrue(self.thumby.dpadPressed())
        self.assertFalse(self.thumby.buttonB.pressed())
        self.sim.release_all()
        self.assertFalse(self.thumby.buttonA.justPressed())
        self.sim.press("A")
        self.assertTrue(self.thumby.buttonA.justPressed())
        with self.assertRaises(ValueError):
            self.sim.press("X")

    def test_group_just_pressed_updates_every_button(self):
        self.sim.press("U", "D")
        self.assertTrue(self.thumby.dpadJustPressed())
        self.assertFalse(self.thumby.buttonD.justPressed())

    def test_save_data_needs_name_and_snapshot(self):
        save = self.thumby.saveData
        with self.assertRaises(RuntimeError):
            save.setItem("level", 1)
        save.setName("SRPG")
        save.setItem("level", 2)
        self.assertTrue(save.hasItem("level"))
        self.assertEqual(save.saved, {})
        save.save()
        self.assertEqual(save.saved, {"level": 2})
        save.delItem("level")
        self.assertFalse(save.hasItem("level"))

    def test_audio_link_and_reset(self):
        self.thumby.audio.play(440, 100)
        self.assertEqual(self.sim.sounds, [(440, 100)])
        self.thumby.link.send(b"hi")
        self.assertEqual(self.sim.link_outbox, [b"hi"])
        self.assertIsNone(self.thumby.link.receive())
        with self.assertRaises(SystemExit):
            self.thumby.reset()

    def test_frames_and_screen_text(self):
        self.display.setFPS(30)
        self.display.update()
        self.assertEqual((self.sim.fps, self.sim.frames), (30, 1))
        self.display.setPixel(0, 0, 1)
        lines = self.sim.screen_text().splitlines()
        self.assertEqual(len(lines), 40)
        self.assertTrue(lines[0].startswith("#."))


class StaticCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def check(self):
        return platform_check.check_directory_source("thumby", self.dir)

    def test_allowed_imports_and_sibling_module_pass(self):
        self.write("units.py", "import math\nfrom random import randint\n")
        self.write(
            "game.py",
            "import thumby, time\nimport units\nfrom units import *\n",
        )
        self.assertEqual(self.check(), [])

    def test_cpython_only_imports_are_rejected(self):
        self.write("game.py", "import os\nfrom dataclasses import field\n")
        errors = self.check()
        self.assertEqual(len(errors), 2)
        self.assertIn("game.py:1", errors[0])
        self.assertIn("os", errors[0])
        self.assertIn("dataclasses", errors[1])

    def test_relative_import_is_rejected(self):
        self.write("game.py", "from . import units\n")
        errors = self.check()
        self.assertTrue(any("상대 import" in e for e in errors))

    def test_match_is_rejected(self):
        # Python < 3.10 hosts cannot parse match and report a syntax error;
        # newer hosts parse it and report the unsupported node.
        self.write(
            "game.py",
            "def f(v):\n    match v:\n        case 1:\n            return 1\n",
        )
        errors = self.check()
        expected = "Match" if sys.version_info >= (3, 10) else "문법 오류"
        self.assertTrue(errors)
        self.assertTrue(any(expected in e for e in errors), errors)

    def test_syntax_error_is_reported_without_execution(self):
        marker = self.dir / "executed.txt"
        self.write(
            "game.py",
            f"open({str(marker)!r}, 'w').write('x')\nif True\n",
        )
        errors = self.check()
        self.assertEqual(len(errors), 1)
        self.assertIn("문법 오류", errors[0])
        self.assertFalse(marker.exists())

    def test_test_files_are_not_checked(self):
        self.write("test_game.py", "import unittest\nimport os\n")
        self.assertEqual(self.check(), [])

    def test_symlink_is_reported(self):
        real = self.write("real.txt", "import os\n")
        (self.dir / "link.py").symlink_to(real)
        errors = self.check()
        self.assertEqual(len(errors), 1)
        self.assertIn("심볼릭 링크", errors[0])

    def test_no_platform_means_no_check(self):
        self.write("game.py", "import os\n")
        self.assertEqual(
            platform_check.check_directory_source(None, self.dir), []
        )


class ConfigTests(unittest.TestCase):
    def config(self, **values):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "target.json"
        path.write_text(json.dumps(values), encoding="utf-8")
        return path

    def test_missing_platform_is_none(self):
        self.assertIsNone(platform_check.configured_platform(self.config()))

    def test_thumby_with_edit_directory(self):
        path = self.config(platform="thumby", edit_directory="micropython/x")
        self.assertEqual(platform_check.configured_platform(path), "thumby")

    def test_thumby_without_edit_directory_is_rejected(self):
        with self.assertRaises(ValueError):
            platform_check.configured_platform(self.config(platform="thumby"))

    def test_unknown_platform_is_rejected(self):
        path = self.config(platform="nes", edit_directory="x")
        with self.assertRaises(ValueError):
            platform_check.configured_platform(path)

    def test_current_tool_config_has_no_platform(self):
        self.assertIsNone(platform_check.configured_platform())

    def test_sandbox_never_uses_platform(self):
        with patch.object(platform_check, "configured_platform",
                          side_effect=AssertionError("not expected")):
            self.assertIsNone(
                platform_check.target_platform("sandbox/clamp.py")
            )

    def test_prompt_note(self):
        self.assertEqual(platform_check.prompt_note(None), "")
        note = platform_check.prompt_note("thumby")
        self.assertIn("72x40", note)
        self.assertIn("thumby", note)

    def test_docker_options(self):
        self.assertEqual(platform_check.docker_options(None), [])
        options = platform_check.docker_options("thumby")
        self.assertIn("PYTHONPATH=/platform", options)
        mount = options[options.index("--mount") + 1]
        self.assertTrue(mount.endswith("target=/platform,readonly"))


class RunTestPlatformTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.game = Path(temp.name)
        self.log = self.game / "log.txt"
        for target, kwargs in (
            ("check_directory", {}),
            ("platform_check.configured_platform",
             {"return_value": "thumby"}),
        ):
            owner = edit_loop
            name = target
            if "." in target:
                module, name = target.split(".")
                owner = getattr(edit_loop, module)
            patcher = patch.object(owner, name, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.run_patch = patch.object(edit_loop.subprocess, "run")
        self.subprocess_run = self.run_patch.start()
        self.addCleanup(self.run_patch.stop)

    def test_static_failure_skips_docker(self):
        (self.game / "game.py").write_text("import os\n", encoding="utf-8")
        passed, feedback = edit_loop.run_test(
            self.log, "test_game", work_dir=self.game
        )
        self.assertFalse(passed)
        self.assertIn("thumby 호환 검사 실패", feedback)
        self.assertIn("os", self.log.read_text(encoding="utf-8"))
        self.subprocess_run.assert_not_called()

    def test_pass_mounts_stand_in_before_image(self):
        (self.game / "game.py").write_text("import thumby\n",
                                          encoding="utf-8")
        self.subprocess_run.return_value.returncode = 0
        passed, _ = edit_loop.run_test(
            self.log, "test_game", work_dir=self.game
        )
        self.assertTrue(passed)
        command = self.subprocess_run.call_args.args[0]
        image = command.index("python:3.11-slim")
        self.assertLess(command.index("PYTHONPATH=/platform"), image)
        self.assertIn("--network", command)
        self.assertEqual(command[command.index("--network") + 1], "none")
        mounts = [command[i + 1] for i, part in enumerate(command)
                  if part == "--mount"]
        self.assertEqual(len(mounts), 2)
        self.assertTrue(all(m.endswith(",readonly") for m in mounts))

    def test_sandbox_is_unchanged(self):
        edit_loop.platform_check.configured_platform.side_effect = (
            AssertionError("not expected")
        )
        self.subprocess_run.return_value.returncode = 0
        edit_loop.run_test(self.log, "test_clamp")
        command = self.subprocess_run.call_args.args[0]
        self.assertNotIn("PYTHONPATH=/platform", command)


class PromptNoteTests(unittest.TestCase):
    setUp = test_thumby_connection.ThumbyConnectionTests.setUp
    git = test_thumby_connection.ThumbyConnectionTests.git
    mock = test_thumby_connection.ThumbyConnectionTests.mock
    proposal = test_thumby_connection.ThumbyConnectionTests.proposal

    def use_platform(self, value):
        patcher = patch.object(platform_check, "configured_platform",
                               return_value=value)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_edit_prompt_has_note_for_thumby_game(self):
        self.use_platform("thumby")
        self.model.return_value = self.proposal("def move(x, d):\n    return x\n")
        self.runner.return_value = (True, "passed")
        edit_loop.run_edit("game/movement.py", "Implement.", "test_movement")
        self.assertIn("원래 Thumby", self.model.call_args.args[0])

    def test_edit_prompt_has_no_note_without_platform(self):
        self.use_platform(None)
        self.model.return_value = self.proposal("def move(x, d):\n    return x\n")
        self.runner.return_value = (True, "passed")
        edit_loop.run_edit("game/movement.py", "Implement.", "test_movement")
        self.assertNotIn("원래 Thumby", self.model.call_args.args[0])

    def test_create_prompt_has_note_for_thumby_game(self):
        self.use_platform("thumby")
        self.model.return_value = json.dumps(
            {"action": "create", "code": "value = 1\n"}
        )
        self.runner.return_value = (True, "passed")
        result = create_loop.run_create(
            "game/new_rules.py", "Create.", "test_movement"
        )
        self.assertEqual(result["status"], "tests_passed")
        self.assertIn("원래 Thumby", self.model.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
