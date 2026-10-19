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


class FakeButton:
    def __init__(self):
        self.edge = False

    def justPressed(self):
        return self.edge


fake_display = FakeDisplay()
fake_thumby = types.ModuleType("thumby")
fake_thumby.display = fake_display
for button_name in ("U", "D", "L", "R", "A", "B"):
    setattr(fake_thumby, "button" + button_name, FakeButton())
sys.modules["thumby"] = fake_thumby
game = importlib.import_module("ThumbySRPG")


class SRPGMenuTests(unittest.TestCase):
    def press(self, button_name, callback):
        for name in ("U", "D", "L", "R", "A", "B"):
            getattr(fake_thumby, "button" + name).edge = name == button_name
        callback()
        for name in ("U", "D", "L", "R", "A", "B"):
            getattr(fake_thumby, "button" + name).edge = False

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

    def test_weapon_selection_uses_selected_range_and_power_in_combat(self):
        game.units = create_units()
        game.selected_unit = game.units[1]
        target = game.units[-1]
        target["x"], target["y"] = 4, 4
        game.cursor_x, game.cursor_y = game.selected_unit["x"], game.selected_unit["y"]
        game.menu_index = 1
        game.weapon_index = 0
        game.state = game.STATE_COMMAND
        self.press("A", game.handle_command_input)
        self.assertEqual(game.state, game.STATE_WEAPONS)
        for _ in range(4):
            self.press("D", game.handle_weapon_input)
        self.press("A", game.handle_weapon_input)
        self.assertEqual((game.state, game.selected_weapon["name"]),
                         (game.STATE_TARGET, "FINAL"))
        game.move_cursor(1, 0)
        game.move_cursor(1, 0)
        self.press("A", game.handle_target_input)
        self.assertEqual((game.state, game.attack_weapon["name"]),
                         (game.STATE_ATTACK, "FINAL"))
        for _ in range(20):
            game.update_attack()
        self.assertEqual(target["hp"], 15)

    def test_status_command_opens_and_returns_to_command_menu(self):
        game.selected_unit = create_units()[0]
        game.menu_index = 2
        game.state = game.STATE_COMMAND
        self.press("A", game.handle_command_input)
        self.assertEqual(game.state, game.STATE_STATUS)
        self.press("B", game.update)
        self.assertEqual(game.state, game.STATE_COMMAND)


if __name__ == "__main__":
    unittest.main()
