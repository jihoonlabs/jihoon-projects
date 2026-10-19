import importlib
import sys
import types
import unittest

from rules import create_units


class FakeDisplay:
    def __init__(self):
        self.text = []
        self.rectangles = []

    def fill(self, _color):
        self.text = []

    def drawText(self, text, x, y, _color=1):
        self.text.append((str(text), x, y))

    def drawFilledRectangle(self, *_args):
        pass

    def drawRectangle(self, *args):
        self.rectangles.append(args)

    def drawLine(self, *_args):
        pass

    def setPixel(self, *_args):
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

    def test_only_finisher_attacks_open_with_a_cut_in(self):
        game.units = create_units()
        game.selected_unit = game.units[0]
        target = game.units[-1]
        target["x"], target["y"] = 3, 2
        game.cursor_x, game.cursor_y = target["x"], target["y"]

        game.start_attack(game.selected_unit["weapons"][0])
        self.assertEqual(game.attack_phase, 1)
        self.assertFalse(game.attack_is_special)

        game.start_attack(game.selected_unit["weapons"][-1])
        self.assertEqual(game.attack_phase, 0)
        self.assertTrue(game.attack_is_special)

    def test_melee_attacker_advances_but_ranged_attacker_holds_position(self):
        game.selected_unit = create_units()[1]
        target = create_units()[-1]
        game.attack_target = target
        game.attack_phase = 1
        game.attack_weapon = game.selected_unit["weapons"][0]
        game.attack_timer = 0
        fake_display.rectangles = []
        game.draw_battle_units(game.selected_unit, target)
        melee_start = next(r[0] for r in fake_display.rectangles
                           if r[2:4] == (5, 4))
        game.attack_timer = 5
        fake_display.rectangles = []
        game.draw_battle_units(game.selected_unit, target)
        melee_lunge = next(r[0] for r in fake_display.rectangles
                           if r[2:4] == (5, 4))
        self.assertGreater(melee_lunge, melee_start)

        game.selected_unit = create_units()[0]
        game.attack_weapon = game.selected_unit["weapons"][0]
        game.attack_timer = 0
        fake_display.rectangles = []
        game.draw_battle_units(game.selected_unit, target)
        ranged_start = next(r[0] for r in fake_display.rectangles
                            if r[2:4] == (5, 4))
        game.attack_timer = 7
        fake_display.rectangles = []
        game.draw_battle_units(game.selected_unit, target)
        ranged_end = next(r[0] for r in fake_display.rectangles
                          if r[2:4] == (5, 4))
        self.assertEqual(ranged_start, ranged_end)

    def test_battle_header_has_hp_and_energy_gauges_for_both_units(self):
        units = create_units()
        game.attack_weapon = units[0]["weapons"][0]
        fake_display.text = []
        fake_display.rectangles = []
        game.draw_battle_units(units[0], units[-1])
        labels = [text for text, _x, _y in fake_display.text]
        self.assertEqual(labels.count("HP"), 2)
        self.assertEqual(labels.count("EN"), 2)
        gauge_bars = [r for r in fake_display.rectangles if r[3:4] == (3,)]
        self.assertEqual(len(gauge_bars), 4)

    def test_status_command_opens_and_returns_to_command_menu(self):
        game.selected_unit = create_units()[0]
        game.menu_index = 2
        game.state = game.STATE_COMMAND
        self.press("A", game.handle_command_input)
        self.assertEqual(game.state, game.STATE_STATUS)
        self.press("B", game.update)
        self.assertEqual(game.state, game.STATE_COMMAND)

    def test_idle_map_uses_full_width_without_status_text(self):
        game.units = create_units()
        game.state = game.STATE_MAP
        game.selected_unit = None
        game.cursor_x, game.cursor_y = 1, 2
        fake_display.text = []
        game.draw_map()
        self.assertEqual((game.VIEW_TILES_W, game.VIEW_TILES_H), (9, 5))
        self.assertEqual(game.camera_x, 0)
        self.assertEqual(fake_display.text, [])

    def test_selection_shows_commands_and_status_is_on_demand(self):
        game.selected_unit = create_units()[0]
        game.state = game.STATE_COMMAND
        fake_display.text = []
        game.draw_map()
        labels = {text for text, _x, _y in fake_display.text}
        self.assertTrue({"R1", "H50", "MOVE", "ATK", "STAT", "END"}.issubset(labels))
        self.assertNotIn("EN30", labels)


if __name__ == "__main__":
    unittest.main()
