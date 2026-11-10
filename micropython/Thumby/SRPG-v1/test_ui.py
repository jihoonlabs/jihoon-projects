import importlib
import sys
import types
import unittest

from rules import create_units


class FakeDisplay:
    def __init__(self):
        self.text = []
        self.placed = []
        self.rectangles = []
        self.pixels = []
        # Thumby starts with the 5x7 font and 1 px spacing.
        self.font = (5, 7, 1)
        self.font_calls = 0

    def fill(self, _color):
        self.text = []
        self.placed = []

    def setFont(self, _path, width, height, space):
        self.font = (width, height, space)
        self.font_calls += 1

    def drawText(self, text, x, y, _color=1):
        self.text.append((str(text), x, y))
        # Keep the font each string was drawn with for layout checks.
        self.placed.append((str(text), x, y, self.font))

    def update(self):
        pass

    def blit(self, *_args):
        pass

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
        self.down = False

    def justPressed(self):
        return self.edge

    def pressed(self):
        return self.down or self.edge


fake_display = FakeDisplay()
fake_thumby = types.ModuleType("thumby")
fake_thumby.display = fake_display
for button_name in ("U", "D", "L", "R", "A", "B"):
    setattr(fake_thumby, "button" + button_name, FakeButton())
sys.modules["thumby"] = fake_thumby
game = importlib.import_module("ThumbySRPG")


def assert_text_fits(test, where):
    """Every string drawn since the last fill stays on the 72x40 screen and
    no two strings overlap, using the font each one was drawn with."""
    boxes = []
    for text, x, y, (width, height, space) in fake_display.placed:
        right = x + len(text) * (width + space) - space
        test.assertGreaterEqual(x, 0, (where, text))
        test.assertGreaterEqual(y, 0, (where, text))
        test.assertLessEqual(right, 72, (where, text))
        test.assertLessEqual(y + height, 40, (where, text))
        boxes.append((x, y, right, y + height, text))
    for index, a in enumerate(boxes):
        for b in boxes[index + 1:]:
            apart = a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]
            test.assertTrue(apart, (where, a[4], b[4]))


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
            self.assertEqual([row[0] for row in weapon_rows],
                             [weapon["name"] for weapon in unit["weapons"]])
            assert_text_fits(self, "weapons " + unit["id"])

    def test_status_screen_contains_only_the_compact_core_stats(self):
        unit = create_units()[0]
        game.status_page = 0
        fake_display.fill(0)
        game.draw_status_screen(unit)
        shown = {text for text, _x, _y in fake_display.text}
        # Agreed vocabulary: HP, EN, MOB, ARM and weapons; no movement row.
        self.assertEqual(shown, {"RV REAL", "1/2", "HP", "50/50", "EN",
                                 "30/30", "MOB", "24", "ARM", "5",
                                 "<> WEAPONS"})
        assert_text_fits(self, "status page 1")
        game.status_page = 1
        fake_display.fill(0)
        game.draw_status_screen(unit)
        shown = [text for text, _x, _y in fake_display.text]
        for weapon in unit["weapons"]:
            self.assertIn(weapon["name"], shown)
            self.assertIn("R" + str(weapon["range"]), shown)
        assert_text_fits(self, "status page 2")
        game.status_page = 0

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
        self.assertEqual(labels.count("EN"), 2)
        self.assertIn("30", labels)
        self.assertIn("20", labels)
        hp_bars = [r for r in fake_display.rectangles if r[3:4] == (4,)]
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
        self.assertTrue({"RV", "MOVE", "ATK", "STAT", "END"}.issubset(labels))
        # EN belongs to STATUS, not the command overlay ("END" is a command).
        self.assertFalse(any(label.startswith("EN") and label != "END"
                             for label in labels))
        assert_text_fits(self, "command overlay")



class SRPGLayoutTests(unittest.TestCase):
    """72x40 readability with real Thumby font metrics (5x7 and 3x5)."""

    def setUp(self):
        game.units = create_units()
        game.selected_unit = None
        game.selected_weapon = None
        game.move_tiles = None
        game.message = "A:OK"

    def render(self, where):
        fake_display.fill(0)
        game.draw_frame(force=True)
        assert_text_fits(self, where)
        return [text for text, _x, _y in fake_display.text]

    def test_every_screen_fits_for_every_unit(self):
        for state in (game.STATE_TITLE, game.STATE_MAP, game.STATE_VICTORY,
                      game.STATE_DEFEAT):
            game.state = state
            self.render("state %d" % state)
        enemy = game.units[-1]
        for unit in game.units[:7]:
            game.selected_unit = unit
            game.cursor_x, game.cursor_y = unit["x"], unit["y"]
            for state in (game.STATE_COMMAND, game.STATE_WEAPONS,
                          game.STATE_STATUS, game.STATE_MOVE,
                          game.STATE_TARGET):
                game.state = state
                game.selected_weapon = unit["weapons"][-1]
                for message in ("A:OK", "NO TARGET", "OUT RANGE"):
                    game.message = message
                    self.render("%s state %d" % (unit["id"], state))
            game.state = game.STATE_ATTACK
            game.attack_target = enemy
            game.attack_damage = 99
            for weapon in unit["weapons"]:
                game.attack_weapon = weapon
                for phase in range(5):
                    game.attack_phase = phase
                    game.attack_timer = 3
                    self.render("%s %s phase %d" % (unit["id"], weapon["name"], phase))

    def test_font_is_loaded_only_when_it_changes(self):
        game.state = game.STATE_TITLE
        game.draw_frame()
        # The title mixes two fonts, so it is drawn once and then kept.
        calls = fake_display.font_calls
        fake_display.text = []
        for _ in range(5):
            game.draw_frame()
        self.assertEqual((fake_display.font_calls, fake_display.text), (calls, []))
        game.state = game.STATE_WEAPONS
        game.selected_unit = game.units[1]
        game.draw_frame()
        calls = fake_display.font_calls
        for _ in range(5):
            game.draw_frame()
        self.assertEqual(fake_display.font_calls, calls)

    def test_move_range_is_cached_while_choosing_a_tile(self):
        unit = game.units[1]
        game.selected_unit = unit
        game.menu_index = 0
        game.state = game.STATE_COMMAND
        SRPGMenuTests.press(self, "A", game.handle_command_input)
        self.assertEqual(game.state, game.STATE_MOVE)
        self.assertEqual(game.move_tiles, game.reachable_tiles(unit, game.units))
        cached = game.move_tiles
        game.draw_frame()
        self.assertIs(game.move_tiles, cached)
        SRPGMenuTests.press(self, "B", game.handle_move_input)
        self.assertIsNone(game.move_tiles)
        SRPGMenuTests.press(self, "A", game.handle_command_input)
        game.cursor_x += 1
        SRPGMenuTests.press(self, "A", game.handle_move_input)
        self.assertEqual((unit["x"], game.state), (game.cursor_x, game.STATE_COMMAND))
        self.assertIsNone(game.move_tiles)

    def test_status_pages_switch_with_left_and_right(self):
        game.selected_unit = game.units[0]
        game.menu_index = 2
        game.state = game.STATE_COMMAND
        game.status_page = 1
        SRPGMenuTests.press(self, "A", game.handle_command_input)
        self.assertEqual((game.state, game.status_page), (game.STATE_STATUS, 0))
        SRPGMenuTests.press(self, "R", game.update)
        self.assertEqual(game.status_page, 1)
        SRPGMenuTests.press(self, "L", game.update)
        self.assertEqual(game.status_page, 0)
        SRPGMenuTests.press(self, "A", game.update)
        self.assertEqual(game.state, game.STATE_COMMAND)

    def test_mode_strip_avoids_the_cursor_row(self):
        unit = game.units[1]
        game.selected_unit = unit
        game.move_tiles = game.reachable_tiles(unit, game.units)
        game.state = game.STATE_MOVE
        game.cursor_x, game.cursor_y = 1, 0
        self.render("strip top cursor")
        label_y = [y for text, _x, y in fake_display.text if text.startswith("MOVE")]
        self.assertGreaterEqual(label_y[0], 33)
        game.cursor_y = 9
        self.render("strip bottom cursor")
        label_y = [y for text, _x, y in fake_display.text if text.startswith("MOVE")]
        self.assertLess(label_y[0], 6)

    def test_benchmark_runs_from_title_and_restores_the_board(self):
        before = [(u["id"], u["x"], u["y"], u["hp"]) for u in game.units]
        game.state = game.STATE_TITLE
        fake_thumby.buttonB.down = True
        try:
            SRPGMenuTests.press(self, "A", game.update)
        finally:
            fake_thumby.buttonB.down = False
        self.assertEqual(game.state, game.STATE_BENCH)
        results, _show, _free_before, _free_after = game.bench_results
        self.assertEqual([r[0] for r in results],
                         ["MAP", "MOVE", "MENU", "FIGHT", "CUTIN"])
        self.assertTrue(all(r[1] >= 0 and r[2] >= r[1] for r in results))
        self.assertEqual([(u["id"], u["x"], u["y"], u["hp"]) for u in game.units],
                         before)
        self.assertIsNone(game.selected_unit)
        self.render("bench")
        SRPGMenuTests.press(self, "B", game.update)
        self.assertEqual(game.state, game.STATE_TITLE)

    def test_plain_a_on_title_starts_the_map(self):
        game.state = game.STATE_TITLE
        SRPGMenuTests.press(self, "A", game.update)
        self.assertEqual(game.state, game.STATE_MAP)


if __name__ == "__main__":
    unittest.main()
