import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import generation_profile


class GenerationProfileTests(unittest.TestCase):
    def config(self, profile="thumby"):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "target.json"
        path.write_text(json.dumps({"generation_profile": profile}), encoding="utf-8")
        return path

    def test_thumby_game_design_separates_rules_and_adapter(self):
        with patch.object(generation_profile, "CONFIG_PATH", self.config()):
            prompt = generation_profile.design_prompt("game")
        self.assertIn("게임 규칙", prompt)
        self.assertIn("import thumby", prompt)
        self.assertIn("무한 게임 루프", prompt)
        self.assertIn("Thumby Color", prompt)

    def test_thumby_game_tests_mock_device_dependency(self):
        with patch.object(generation_profile, "CONFIG_PATH", self.config()):
            prompt = generation_profile.test_prompt("game")
        self.assertIn("sys.modules", prompt)
        self.assertIn("좌우 이동 경계", prompt)
        self.assertIn("재시작", prompt)

    def test_sandbox_has_no_platform_prompt(self):
        with patch.object(generation_profile, "CONFIG_PATH", self.config()):
            self.assertEqual(generation_profile.design_prompt("sandbox"), "")
            self.assertEqual(generation_profile.test_prompt("sandbox"), "")
            self.assertEqual(
                generation_profile.implementation_prompt("sandbox", "game.py"), ""
            )

    def test_unknown_profile_is_rejected(self):
        with self.assertRaises(ValueError):
            generation_profile.current_profile(self.config("unknown"))


    def test_thumby_code_rejects_color_import(self):
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", "import thumbyColor\n")

    def test_thumby_code_rejects_top_level_infinite_loop(self):
        code = "def run():\n    while True:\n        break\n\nwhile True:\n    break\n"
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", code)

    def test_thumby_code_allows_loop_inside_entry_function(self):
        code = "import thumby\n\ndef run():\n    while True:\n        break\n"
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            generation_profile.validate_code("game", code)


    def test_thumby_code_rejects_unverified_api(self):
        code = "import thumby\n\ndef draw():\n    thumby.display.blit(None, 0, 0)\n"
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", code)

    def test_thumby_code_rejects_unverified_button_api(self):
        code = "import thumby\n\ndef read():\n    return thumby.buttonL.justPressed()\n"
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", code)

    def test_thumby_code_allows_verified_first_game_api(self):
        code = (
            "import thumby\n\ndef draw():\n"
            "    if thumby.buttonL.pressed() or thumby.buttonR.pressed():\n"
            "        thumby.display.fill(0)\n"
            "        thumby.display.drawFilledRectangle(0, 0, 2, 2, 1)\n"
            "        thumby.display.drawText('1', 0, 0, 1)\n"
            "        thumby.display.update()\n"
            "        thumby.display.setFPS(30)\n"
        )
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            generation_profile.validate_code("game", code)


if __name__ == "__main__":
    unittest.main()
