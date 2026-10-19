import unittest

from assets import (ENEMY_BATTLE, REAL_BATTLE, REAL_CUTIN, SHIP_BATTLE,
                    SHIP_CUTIN, SUPER_BATTLE, SUPER_CUTIN)
from rules import (BASE_MAX_HP, BASE_TILE, alive_units, create_units,
                   in_range, mission_result, reachable_tiles, resolve_attack,
                   resolve_base_attack, tile_is_open)


class SRPGRulesTests(unittest.TestCase):
    def setUp(self):
        self.units = create_units()

    def test_roster_has_six_mechs_a_ship_and_eight_enemies(self):
        allies = alive_units(self.units, "ally")
        enemies = alive_units(self.units, "enemy")
        self.assertEqual((len(allies), len(enemies)), (7, 8))
        mechs = [unit for unit in allies if unit["kind"] != "SHIP"]
        self.assertEqual({unit["kind"] for unit in mechs}, {"REAL", "SUPER"})
        self.assertEqual(sum(unit["kind"] == "REAL" for unit in allies), 3)
        self.assertEqual(sum(unit["kind"] == "SUPER" for unit in allies), 3)
        ship = next(unit for unit in allies if unit["kind"] == "SHIP")
        self.assertEqual((ship["x"], ship["y"], ship["hp"], ship["attack"],
                          ship["move"], ship["range"]), (0, 0, 100, 26, 0, 5))
        positions = {(unit["x"], unit["y"]) for unit in self.units}
        self.assertEqual(len(positions), len(self.units))

    def test_map_bounds_terrain_and_occupied_tiles_block_movement(self):
        unit = self.units[0]
        self.assertFalse(tile_is_open(-1, 0, self.units, unit))
        self.assertFalse(tile_is_open(2, 1, self.units, unit))
        self.assertFalse(tile_is_open(1, 4, self.units, unit))
        self.assertFalse(tile_is_open(BASE_TILE[0], BASE_TILE[1], self.units, unit))
        self.assertTrue(tile_is_open(1, 1, self.units, unit))

    def test_reachable_tiles_respect_move_limit_and_obstacles(self):
        unit = self.units[0]
        reached = reachable_tiles(unit, self.units)
        self.assertEqual(reached[(1, 2)], 0)
        self.assertIn((1, 1), reached)
        self.assertNotIn((5, 2), reached)
        self.assertNotIn((2, 1), reached)

    def test_attack_range_uses_manhattan_distance(self):
        attacker = self.units[0]
        target = self.units[3]
        self.assertFalse(in_range(attacker, target))
        target["x"], target["y"] = 3, 2
        self.assertTrue(in_range(attacker, target))

    def test_normal_and_special_damage_reduce_hp_and_mark_action(self):
        attacker, defender = self.units[0], self.units[3]
        self.assertEqual(resolve_attack(attacker, defender), 15)
        self.assertEqual(defender["hp"], 35)
        self.assertTrue(attacker["acted"])
        attacker["acted"] = False
        self.assertEqual(resolve_attack(attacker, defender, special=True), 25)
        self.assertEqual(defender["hp"], 10)

    def test_mission_result_distinguishes_victory_defeat_and_ongoing(self):
        self.assertIsNone(mission_result(self.units))
        for unit in self.units:
            if unit["team"] == "enemy":
                unit["hp"] = 0
        self.assertEqual(mission_result(self.units), "victory")
        self.assertEqual(mission_result(self.units, base_hp=0), "defeat")

    def test_ship_loss_is_defeat_even_if_base_counter_is_positive(self):
        ship = next(unit for unit in self.units if unit["kind"] == "SHIP")
        ship["hp"] = 0
        self.assertEqual(mission_result(self.units), "defeat")

    def test_enemy_base_strike_reduces_but_never_underflows_base_hp(self):
        attacker = self.units[-1]
        self.assertEqual(resolve_base_attack(attacker, BASE_MAX_HP), 85)
        self.assertEqual(resolve_base_attack(attacker, 5), 0)


class SpriteAssetTests(unittest.TestCase):
    def test_battle_silhouettes_fit_the_16_by_16_cut_in_canvas(self):
        for sprite in (REAL_BATTLE, SUPER_BATTLE, ENEMY_BATTLE, SHIP_BATTLE):
            self.assertEqual(len(sprite), 16)
            self.assertTrue(all(len(row) == 16 for row in sprite))

    def test_full_screen_cutins_use_the_thumby_72_by_40_vlsb_size(self):
        self.assertEqual((len(REAL_CUTIN), len(SUPER_CUTIN), len(SHIP_CUTIN)),
                         (360, 360, 360))


if __name__ == "__main__":
    unittest.main()
