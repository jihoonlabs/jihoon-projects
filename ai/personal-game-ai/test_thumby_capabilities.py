import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import generation_profile
import thumby_capabilities


class ThumbyCapabilitiesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.config = Path(temporary.name) / "target.json"
        self.set_features(["controls", "save_data"])
        context = patch.object(generation_profile, "CONFIG_PATH", self.config)
        context.start()
        self.addCleanup(context.stop)

    def set_features(self, features, profile="thumby"):
        self.config.write_text(json.dumps({"generation_profile": profile,
            "edit_directory": "micropython/Rpg", "thumby_features": features}))

    def entry(self, body):
        return "import sys\nimport thumby\ndef main_loop():\n" + body + "\nif sys.implementation.name == 'micropython':\n    main_loop()\n"

    def test_enabled_buttons_and_save_methods_pass(self):
        for button in ("L", "R", "U", "D", "A", "B"):
            for method in ("pressed", "justPressed"):
                generation_profile.validate_code("game", self.entry(
                    "    thumby.button" + button + "." + method + "()"), "Rpg.py")
        for method, args in (("setName", "'Rpg'"), ("setItem", "'gold', 40"),
                             ("getItem", "'gold'"), ("hasItem", "'gold'"), ("save", "")):
            generation_profile.validate_code("game", self.entry(
                "    thumby.saveData." + method + "(" + args + ")"), "Rpg.py")

    def test_default_keeps_existing_api_restrictions(self):
        self.set_features([])
        for code in ("thumby.buttonA.pressed()", "thumby.buttonU.pressed()",
                     "thumby.buttonL.justPressed()", "thumby.saveData.save()"):
            with self.subTest(code=code), self.assertRaises(ValueError):
                generation_profile.validate_code("game", code)
        generation_profile.validate_code("game", "thumby.buttonL.pressed()")

    def test_features_do_not_enable_each_other(self):
        self.set_features(["controls"])
        with self.assertRaises(ValueError):
            generation_profile.validate_code("game", "thumby.saveData.save()")
        self.set_features(["save_data"])
        with self.assertRaises(ValueError):
            generation_profile.validate_code("game", "thumby.buttonA.pressed()")

    def test_unknown_method_and_deep_attribute_are_rejected(self):
        for code in ("thumby.buttonA.wasPressed()", "thumby.saveData.load()",
                     "thumby.saveData.delItem('gold')", "thumby.saveData.save.unknown()",
                     "thumby.buttonStart.pressed()", "thumby.display.drawSprite(None)"):
            with self.subTest(code=code), self.assertRaises(ValueError):
                generation_profile.validate_code("game", code)

    def test_invalid_feature_settings_block_profile(self):
        for features in ("controls", ["controls", "controls"], ["unknown"], [None], [True]):
            self.set_features(features)
            with self.subTest(features=features), self.assertRaises(ValueError):
                generation_profile.current_profile()
        self.set_features(["controls"], profile=None)
        with self.assertRaises(ValueError): generation_profile.current_profile()

    def test_expanded_profile_still_rejects_color_and_device_rules_import(self):
        for code, filename in (("import thumbyColor", None), ("import thumby", "rules.py"),
                               ("from thumby import saveData", None), ("import thumby as t", None)):
            with self.subTest(code=code), self.assertRaises(ValueError):
                generation_profile.validate_code("game", code, filename)

    def test_import_path_direct_save_io_is_rejected_including_else(self):
        for method in thumby_capabilities.SAVE:
            code = self.entry("    pass") + "thumby.saveData." + method + "()\n"
            with self.subTest(method=method), self.assertRaisesRegex(ValueError, "저장 I/O"):
                generation_profile.validate_code("game", code, "Rpg.py")
        code = self.entry("    pass") + "else:\n    thumby.saveData.save()\n"
        with self.assertRaisesRegex(ValueError, "저장 I/O"):
            generation_profile.validate_code("game", code, "Rpg.py")

    def test_micropython_save_initialization_is_allowed(self):
        code = self.entry("    pass").replace("    main_loop()", "    thumby.saveData.setName('Rpg')\n    main_loop()")
        generation_profile.validate_code("game", code, "Rpg.py")

    def test_fake_prefix_supports_finite_adapter_without_hardware(self):
        config = json.loads(self.config.read_text())
        code = thumby_capabilities.fake_prefix(config)
        sentinel = sys.modules.get("thumby")
        self.addCleanup(lambda: sys.modules.pop("thumby", None) if sentinel is None
                        else sys.modules.__setitem__("thumby", sentinel))
        namespace = {}
        exec(code, namespace)
        device = namespace["fake_thumby"]
        self.assertFalse(device.buttonA.justPressed())
        self.assertFalse(device.saveData.hasItem("gold"))
        with self.assertRaises(KeyError): device.saveData.getItem("gold")
        values = {}
        device.saveData.setItem.side_effect = lambda key, value: values.__setitem__(key, value)
        device.saveData.getItem.side_effect = lambda key: values[key]
        device.saveData.hasItem.side_effect = lambda key: key in values
        device.saveData.setItem("gold", 40)
        device.saveData.save()
        self.assertTrue(device.saveData.hasItem("gold"))
        self.assertEqual(device.saveData.getItem("gold"), 40)
        device.saveData.save.assert_called_once_with()
        device.saveData.save.side_effect = OSError("fixture write failure")
        with self.assertRaises(OSError): device.saveData.save()

    def test_prompt_records_constraints_and_adapter_only_apis(self):
        design = generation_profile.design_prompt("game")
        self.assertIn("72x40", design)
        self.assertIn("Start", design)
        self.assertIn("saveData", design)
        prompt = generation_profile.test_prompt("game")
        self.assertIn("fake_thumby.buttonA", prompt)
        self.assertIn("fake_thumby.saveData", prompt)
        self.assertIn("대상 import보다 앞", prompt)
        self.assertIn("저장 I/O 금지", generation_profile.implementation_prompt("game", "Rpg.py"))
        self.assertNotIn("saveData", generation_profile.implementation_prompt("game", "rules.py"))
        self.assertEqual(generation_profile.design_prompt("sandbox"), "")


if __name__ == "__main__":
    unittest.main()
