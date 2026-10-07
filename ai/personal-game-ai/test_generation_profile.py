import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import generation_profile


class GenerationProfileTests(unittest.TestCase):
    def config(self, profile="thumby", edit_directory=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "target.json"
        config = {"generation_profile": profile}
        if edit_directory is not None:
            config["edit_directory"] = edit_directory
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def test_thumby_game_design_separates_rules_and_adapter(self):
        with patch.object(generation_profile, "CONFIG_PATH", self.config()):
            prompt = generation_profile.design_prompt("game")
        self.assertIn("게임 규칙", prompt)
        self.assertIn("엔트리 파일이 기기 어댑터 역할", prompt)
        self.assertIn("MicroPython", prompt)
        self.assertIn("import thumby", prompt)
        self.assertIn("게임 폴더와 정확히 같은 이름", prompt)
        self.assertIn("CPython 테스트 import", prompt)
        self.assertIn("sys.implementation.name", prompt)
        self.assertIn("Thumby Color", prompt)

    def test_thumby_design_requires_folder_named_entry(self):
        files = [{"filename": "rules.py"}]
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_design(
                    "game", files, Path("/tmp/ThumbyDodge")
                )

    def test_thumby_design_requires_separate_rules_dependency(self):
        entry_only = [{
            "id": "001", "filename": "ThumbyDodge.py", "depends_on": []
        }]
        disconnected = [
            {"id": "001", "filename": "rules.py", "depends_on": []},
            {"id": "002", "filename": "ThumbyDodge.py", "depends_on": []},
        ]
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            for files in (entry_only, disconnected):
                with self.subTest(files=files):
                    with self.assertRaises(ValueError):
                        generation_profile.validate_design(
                            "game", files, Path("/tmp/ThumbyDodge")
                        )

    def test_thumby_design_accepts_entry_depending_on_rules(self):
        files = [
            {"id": "001", "filename": "rules.py", "depends_on": []},
            {"id": "002", "filename": "ThumbyDodge.py", "depends_on": ["001"]},
        ]
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            generation_profile.validate_design(
                "game", files, Path("/tmp/ThumbyDodge")
            )

    def test_thumby_entry_test_requires_fake_module_before_import(self):
        design = {"files": [{"id": "001", "filename": "ThumbyDodge.py"}]}
        candidate = {"files": [{"id": "001", "code": (
            "import unittest\nfrom ThumbyDodge import run\n"
        )}]}
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_tests(
                    "game", candidate, design, Path("/tmp/ThumbyDodge")
                )

    def test_thumby_entry_test_requires_sys_import_before_fake(self):
        design = {"files": [{"id": "001", "filename": "ThumbyDodge.py"}]}
        candidate = {"files": [{"id": "001", "code": (
            "from unittest.mock import MagicMock\n"
            "sys.modules['thumby'] = MagicMock()\n"
            "from ThumbyDodge import run\n"
        )}]}
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_tests(
                    "game", candidate, design, Path("/tmp/ThumbyDodge")
                )

    def test_thumby_entry_test_rejects_none_fake_module(self):
        design = {"files": [{"id": "001", "filename": "ThumbyDodge.py"}]}
        candidates = [
            "import sys\nsys.modules['thumby'] = None\nfrom ThumbyDodge import run\n",
            "import sys\nsys.modules.setdefault('thumby')\nfrom ThumbyDodge import run\n",
            "import sys\nsys.modules.setdefault('thumby', None)\nfrom ThumbyDodge import run\n",
        ]
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            for code in candidates:
                with self.subTest(code=code):
                    with self.assertRaises(ValueError):
                        generation_profile.validate_tests(
                            "game", {"files": [{"id": "001", "code": code}]},
                            design, Path("/tmp/ThumbyDodge"),
                        )

    def test_thumby_entry_test_accepts_fake_module_before_import(self):
        design = {"files": [{"id": "001", "filename": "ThumbyDodge.py"}]}
        candidate = {"files": [{"id": "001", "code": (
            "import sys\nfrom unittest.mock import MagicMock\n"
            "sys.modules['thumby'] = MagicMock()\n"
            "from ThumbyDodge import run\n"
        )}]}
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            generation_profile.validate_tests(
                "game", candidate, design, Path("/tmp/ThumbyDodge")
            )

    def test_thumby_entry_test_accepts_setdefault_before_import(self):
        design = {"files": [{"id": "001", "filename": "ThumbyDodge.py"}]}
        candidate = {"files": [{"id": "001", "code": (
            "import sys\nfrom unittest.mock import MagicMock\n"
            "sys.modules.setdefault('thumby', MagicMock())\n"
            "from ThumbyDodge import run\n"
        )}]}
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            generation_profile.validate_tests(
                "game", candidate, design, Path("/tmp/ThumbyDodge")
            )

    def test_thumby_game_tests_mock_device_dependency(self):
        with patch.object(generation_profile, "CONFIG_PATH", self.config()):
            prompt = generation_profile.test_prompt("game")
        self.assertIn("sys.modules", prompt)
        self.assertIn("폴더명 엔트리", prompt)
        self.assertIn("좌우 이동 경계", prompt)
        self.assertIn("재시작", prompt)

    def test_sandbox_has_no_platform_prompt(self):
        with patch.object(generation_profile, "CONFIG_PATH", self.config()):
            self.assertEqual(generation_profile.design_prompt("sandbox"), "")
            self.assertEqual(generation_profile.test_prompt("sandbox"), "")
            self.assertEqual(
                generation_profile.implementation_prompt("sandbox", "game.py"), ""
            )

    def test_missing_profile_is_disabled(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "target.json"
        path.write_text("{}", encoding="utf-8")
        self.assertIsNone(generation_profile.current_profile(path))

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

    def test_thumby_implementation_prompt_requires_script_start(self):
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            prompt = generation_profile.implementation_prompt("game", "ThumbyDodge.py")
        self.assertIn("CPython import", prompt)
        self.assertIn("폴더명 엔트리 파일만 기기 어댑터", prompt)
        self.assertIn("sys.path", prompt)
        self.assertIn("/Games/<게임폴더명>", prompt)
        self.assertIn("sys.implementation.name", prompt)
        self.assertIn("Thumby 런처 import", prompt)
        self.assertIn("MicroPython", prompt)


    def test_thumby_code_without_filename_keeps_legacy_validation(self):
        code = "import thumby\nthumby.display.fill(0)\n"
        with patch.object(
            generation_profile, "CONFIG_PATH", self.config(),
        ):
            generation_profile.validate_code("game", code)

    def test_thumby_entry_code_requires_micropython_start_guard(self):
        code = "import sys\nimport thumby\n\ndef run():\n    pass\n"
        with patch.object(
            generation_profile, "CONFIG_PATH",
            self.config(edit_directory="micropython/ThumbyDodge"),
        ):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", code, "ThumbyDodge.py")

    def test_thumby_entry_code_accepts_micropython_start_guard(self):
        code = (
            "import sys\nimport thumby\n\ndef run():\n"
            "    while True:\n        break\n\n"
            "if sys.implementation.name == 'micropython':\n    run()\n"
        )
        with patch.object(
            generation_profile, "CONFIG_PATH",
            self.config(edit_directory="micropython/ThumbyDodge"),
        ):
            generation_profile.validate_code("game", code, "ThumbyDodge.py")

    def test_thumby_entry_code_rejects_start_call_outside_guard(self):
        code = (
            "import sys\nimport thumby\n\ndef run():\n"
            "    while True:\n        break\n\n"
            "if sys.implementation.name == 'micropython':\n    run()\n"
            "run()\n"
        )
        with patch.object(
            generation_profile, "CONFIG_PATH",
            self.config(edit_directory="micropython/ThumbyDodge"),
        ):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", code, "ThumbyDodge.py")

    def test_non_entry_code_rejects_thumby_import(self):
        code = "import thumby\n\ndef read_input():\n    return thumby.buttonL.pressed()\n"
        with patch.object(
            generation_profile, "CONFIG_PATH",
            self.config(edit_directory="micropython/ThumbyDodge"),
        ):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", code, "device.py")

    def test_non_entry_code_does_not_require_micropython_start_guard(self):
        code = "def step():\n    return 1\n"
        with patch.object(
            generation_profile, "CONFIG_PATH",
            self.config(edit_directory="micropython/ThumbyDodge"),
        ):
            generation_profile.validate_code("game", code, "rules.py")

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


    def test_sandbox_code_is_not_restricted_by_thumby_profile(self):
        code = "import thumbyColor\n\nwhile True:\n    break\n"
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            generation_profile.validate_code("sandbox", code)

    def test_game_code_without_profile_is_not_restricted(self):
        code = "import thumbyColor\n\nwhile True:\n    break\n"
        with patch.object(generation_profile, "current_profile", return_value=None):
            generation_profile.validate_code("game", code)

    def test_thumby_code_rejects_import_alias(self):
        code = "import thumby as device\n"
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", code)

    def test_thumby_code_rejects_from_import(self):
        code = "from thumby import display\n"
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", code)

    def test_thumby_code_rejects_unverified_submodule_import(self):
        code = "import thumby.audio\n"
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", code)

    def test_thumby_code_rejects_unverified_submodule_from_import(self):
        code = "from thumby.audio import play\n"
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", code)

    def test_thumby_code_rejects_color_from_import(self):
        code = "from thumbyColor import display\n"
        with patch.object(generation_profile, "current_profile", return_value="thumby"):
            with self.assertRaises(ValueError):
                generation_profile.validate_code("game", code)


if __name__ == "__main__":
    unittest.main()
