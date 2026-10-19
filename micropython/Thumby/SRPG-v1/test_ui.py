import importlib
import sys
import types
import unittest

from rules import create_units


class FakeDisplay:
    def __init__(self):
        self.text = []

    def fill(self, _color):
        self.text = []

    def drawText(self, text, x, y, _color=1):
        self.text.append((str(text), x, y))

    def drawFilledRectangle(self, *_args):
        pass

    def setFPS(self, _fps):
        pass


fake_display = FakeDisplay()
fake_thumby = types.ModuleType("thumby")
fake_thumby.display = fake_display
for button_name in ("U", "D", "L", "R", "A", "B"):
    button = types.SimpleNamespace(justPressed=lambda: False)
    setattr(fake_thumby, "button" + button_name, button)
sys.modules["thumby"] = fake_thumby
game = importlib.import_module("ThumbySRPG")


class SRPGMenuTests(unittest.TestCase):
    def test_weapon_menu_fits_every_loadout_inside_the_72_pixel_screen(self):
        for unit in create_units()[:7]:
            game.selected_unit = unit
            game.weapon_index = 0
            fake_display.text = []
            game.draw_weapon_menu()
            weapon_rows = [row for row in fake_display.text
                           if row[1] == 2 and row[2] >= 6]
            self.assertEqual(len(weapon_rows), len(unit["weapons"]))
            self.assertTrue(all(x + len(text) * 6 <= 72
                                for text, x, _y in weapon_rows))

    def test_status_screen_contains_only_the_compact_core_stats(self):
        unit = create_units()[0]
        fake_display.text = []
        game.draw_status_screen(unit)
        shown = {text for text, _x, _y in fake_display.text}
        self.assertEqual(shown, {"R1 REAL", "HP 50/50", "EN 30/30",
                                 "ARM 5", "MOB 24", "MOVE 3", "B:BK"})
        self.assertTrue(all(x + len(text) * 6 <= 72
                            for text, x, _y in fake_display.text))


if __name__ == "__main__":
    unittest.main()
