import importlib
import sys
import types
import unittest

from rules import create_units


class FakeDisplay:
    def __init__(self):
        self.text = []
        self.rectangles = []
        self.pixels = []

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

    def setPixel(self, *args):
        self.pixels.append(args)

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
        self.assertEqual(shown, {"RV REAL", "HP 50/50", "EN 30/30",
                                 "ARM 5", "MOB 24", "MOVE 3", "B:BK"})
        self.assertTrue(all(x + len(text) * 6 <= 72
                            for text, x, _y in fake_display.text))

    def test_weapon_selection_uses_selected_range_and_power_in_combat(self):
        game.units = create_units()
        game.selected_unit = game.units[1]
        target = game.units[-1]
        target["x"], target["y"] = 3, 4
        game.cursor_x, game.cursor_y = game.selected_unit["x"], game.selected_unit["y"]
        game.menu_index = 1
        game.weapon_index = 0
        game.state = game.STATE_COMMAND
        self.press("A", game.handle_command_input)
        self.assertEqual(game.state, game.STATE_WEAPONS)
        for _ in range(4):
            self.press("D", game.handle_weapon_input)
        self.press("A", game.handle_weapon_input)
        finisher_name = game.selected_unit["weapons"][-1]["name"]
        self.assertEqual((game.state, game.selected_weapon["name"]),
                         (game.STATE_TARGET, finisher_name))
        game.move_cursor(1, 0)
        self.press("A", game.handle_target_input)
        self.assertEqual((game.state, game.attack_weapon["name"]),
                         (game.STATE_ATTACK, finisher_name))
        for _ in range(50):
            if game.state != game.STATE_ATTACK:
                break
            game.update_attack()
        self.assertEqual(target["hp"], 15)

    def test_only_finisher_attacks_open_with_a_cut_in(self):
        game.units = create_units()
        game.selected_unit = game.units[0]
        target = game.units[-1]
        target["x"], target["y"] = 3, 2
        game.cursor_x, game.cursor_y = target["x"], target["y"]

        game.start_attack(game.selected_unit["weapons"][0])
        self.assertEqual(game.attack_phase, 0)
        self.assertFalse(game.attack_is_special)
        for _ in range(10):
            game.update_attack()
        self.assertEqual(game.attack_phase, 2)

        game.start_attack(game.selected_unit["weapons"][-1])
        self.assertEqual(game.attack_phase, 0)
        self.assertTrue(game.attack_is_special)
        for _ in range(10):
            game.update_attack()
        self.assertEqual(game.attack_phase, 1)

    def test_melee_lunges_and_ranged_fire_recoils(self):
        game.selected_unit = create_units()[0]
        target = create_units()[-1]
        game.attack_target = target
        game.attack_phase = 2
        game.attack_weapon = game.selected_unit["weapons"][1]
        game.attack_timer = 0
        fake_display.pixels = []
        game.draw_battle_units(game.selected_unit, target)
        melee_start = min(x for x, y, _color in fake_display.pixels
                          if y == 7 and x < 50)
        game.attack_timer = 5
        fake_display.pixels = []
        game.draw_battle_units(game.selected_unit, target)
        melee_lunge = min(x for x, y, _color in fake_display.pixels
                          if y == 7 and x < 50)
        self.assertGreater(melee_lunge, melee_start)

        game.selected_unit = create_units()[1]
        game.attack_weapon = game.selected_unit["weapons"][0]
        game.attack_timer = 0
        fake_display.pixels = []
        game.draw_battle_units(game.selected_unit, target)
        fist_start = min(x for x, y, _color in fake_display.pixels
                         if y == 7 and x < 50)
        game.attack_timer = 5
        fake_display.pixels = []
        game.draw_battle_units(game.selected_unit, target)
        fist_lunge = min(x for x, y, _color in fake_display.pixels
                         if y == 7 and x < 50)
        self.assertGreater(fist_lunge, fist_start)

        game.selected_unit = create_units()[0]
        game.attack_weapon = game.selected_unit["weapons"][0]
        game.attack_timer = 0
        fake_display.pixels = []
        game.draw_battle_units(game.selected_unit, target)
        ranged_start = min(x for x, y, _color in fake_display.pixels
                           if y == 8 and x < 50)
        game.attack_timer = 2
        fake_display.pixels = []
        game.draw_battle_units(game.selected_unit, target)
        ranged_recoil = min(x for x, y, _color in fake_display.pixels
                            if y == 8 and x < 50)
        self.assertLess(ranged_recoil, ranged_start)
        game.attack_timer = 7
        fake_display.pixels = []
        game.draw_battle_units(game.selected_unit, target)
        ranged_end = min(x for x, y, _color in fake_display.pixels
                         if y == 8 and x < 50)
        self.assertEqual(ranged_start, ranged_end)

    def test_status_is_shown_before_and_after_battle_but_hidden_during_action(self):
        units = create_units()
        game.attack_weapon = units[0]["weapons"][0]
        fake_display.text = []
        fake_display.rectangles = []
        game.draw_combat_status(units[0], units[-1])
        labels = [text for text, _x, _y in fake_display.text]
        self.assertEqual(labels.count("HP"), 2)
        self.assertIn("EN30", labels)
        self.assertIn("EN20", labels)
        hp_bars = [r for r in fake_display.rectangles if r[3:4] == (3,)]
        self.assertEqual(len(hp_bars), 2)

        fake_display.text = []
        fake_display.rectangles = []
        for phase in (2, 3):
            fake_display.text = []
            game.attack_phase = phase
            game.draw_battle_units(units[0], units[-1], impact=phase == 3)
            during_text = [text for text, _x, _y in fake_display.text]
            self.assertNotIn("HP", during_text)
            self.assertFalse(any(text.startswith("EN") for text in during_text))

        fake_display.text = []
        game.attack_damage = 13
        game.draw_combat_status(units[0], units[-1], result=True)
        result_text = [text for text, _x, _y in fake_display.text]
        self.assertIn("-13", result_text)

    def test_custom_unit_sprite_is_used_and_mirrored_for_the_opponent(self):
        unit = create_units()[0]
        rows = ("#" + "." * 15,) + ("." * 16,) * 15
        previous = game.CUSTOM_BATTLE.get(unit["id"])
        game.CUSTOM_BATTLE[unit["id"]] = rows
        try:
            fake_display.pixels = []
            game.draw_combat_mech(fake_display, unit, 4, 7)
            self.assertIn((4, 7, 0), fake_display.pixels)
            fake_display.pixels = []
            game.draw_combat_mech(fake_display, unit, 4, 7, facing=-1)
            self.assertIn((19, 7, 0), fake_display.pixels)
        finally:
            if previous is None:
                del game.CUSTOM_BATTLE[unit["id"]]
            else:
                game.CUSTOM_BATTLE[unit["id"]] = previous

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
        self.assertTrue({"RV", "H50", "MOVE", "ATK", "STAT", "END"}.issubset(labels))
        self.assertNotIn("EN30", labels)


if __name__ == "__main__":
    unittest.main()
