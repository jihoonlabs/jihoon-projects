import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import game_brief


class GameBriefTests(unittest.TestCase):
    def test_color_does_not_become_generation_ready(self):
        result = game_brief.prepare("thumby-color", {"genre": "격투", "experience": "거리 싸움"})
        self.assertEqual(result["stage"], "needs_research")
        self.assertEqual(result["device"]["id"], "thumby-color")
        self.assertFalse(result["specification_approved"])
        self.assertNotIn("request", result)

    def test_only_missing_question(self):
        result = game_brief.prepare("thumby", {"genre": "리듬"})
        self.assertEqual([q["id"] for q in result["questions"]], ["experience"])

    def test_invalid_input(self):
        for device, settings in [("pc", {}), ("thumby", {"genre": " "}), ("thumby", {"genre": "x" * 1001}), ("thumby", {"approved": True})]:
            with self.subTest(device=device, settings=settings):
                with self.assertRaises(ValueError):
                    game_brief.prepare(device, settings)

    def test_interactive_saves_original_input_and_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "brief.json"
            with patch("builtins.input", side_effect=["탐험 RPG", "능력 획득 후 재탐험"]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(game_brief.main(["--device", "thumby", "--interactive", "--output", str(target)]), 0)
            result = json.loads(target.read_text())
            self.assertEqual(result["settings"]["experience"], "능력 획득 후 재탐험")
            self.assertFalse(result["policy"]["copy_source_game"])
            self.assertEqual(result["research"]["hardware"], [])

    def test_existing_file_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "brief.json"
            target.write_text("keep")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                game_brief.main(["--device", "thumby", "--genre", "格闘", "--experience", "対戦", "--output", str(target)])
            self.assertEqual(target.read_text(), "keep")

    def test_incomplete_input_is_not_saved(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "brief.json"
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                game_brief.main(["--device", "thumby", "--output", str(target)])
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
