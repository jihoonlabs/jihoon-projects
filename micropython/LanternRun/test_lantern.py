"""Host-only checks: python3 -B -m unittest discover -s <game folder> -v.

Uses the standard library only. This file is not needed on Thumby.
"""
import ast
import importlib.util
from pathlib import Path
import random
import sys
import types
import unittest

from lantern_core import (Game, LEFT, RIGHT, UP, DOWN, ATTACK, DODGE,
                          PLAY, WON, LOST, MAX_HP)


class RulesTests(unittest.TestCase):
    def solo(self):
        game = Game()
        for enemy in game.enemies:
            enemy.hp = 0
        return game

    def test_boundaries_and_camera(self):
        game = self.solo()
        for _ in range(200):
            game.step(LEFT | UP)
        self.assertEqual((game.player.x, game.player.y, game.camera()), (4, 22, 0))
        game.enemies[0].hp = 100
        game.enemies[0].stun = 1000
        for _ in range(200):
            game.step(RIGHT | DOWN)
        self.assertEqual((game.player.x, game.player.y, game.camera()), (107, 37, 40))
        self.assertEqual(game.room, 0)

    def test_attack_direction_lane_and_one_hit(self):
        game = Game()
        player = game.player
        for enemy, x, y in zip(game.enemies, (22, 5, 22), (30, 30, 37)):
            enemy.reset(x, y, 5, 0)
            enemy.stun = 100
        for _ in range(20):
            game.step(ATTACK)
        self.assertEqual([enemy.hp for enemy in game.enemies], [4, 5, 5])
        self.assertEqual(player.hp, MAX_HP)

    def test_combo_finisher_and_expiry(self):
        game = self.solo()
        enemy = game.enemies[0]
        for combo in (1, 2, 3):
            enemy.reset(game.player.x + 8, game.player.y, 5, 0)
            enemy.stun = 100
            game.step(ATTACK)
            while game.attack or game.hitstop:
                game.step(0)
            self.assertEqual(game.combo, combo)
            self.assertEqual(enemy.hp, 3 if combo == 3 else 4)
        for _ in range(25):
            game.step(0)
        game.step(ATTACK)
        self.assertEqual(game.combo, 1)

    def test_attack_buffer(self):
        game = self.solo()
        game.step(ATTACK)
        for _ in range(4):
            game.step(0)
        game.step(ATTACK)
        for _ in range(4):
            game.step(0)
        self.assertEqual(game.combo, 2)

    def test_enemy_telegraph_can_be_sidestepped(self):
        game = self.solo()
        enemy = game.enemies[0]
        enemy.reset(20, 30, 3, 0)
        game.step(0)
        self.assertEqual(enemy.wind, 10)
        for _ in range(10):
            game.step(UP)
        self.assertEqual(game.player.hp, MAX_HP)

    def test_damage_invulnerability_and_loss(self):
        game = self.solo()
        enemy = game.enemies[0]
        enemy.reset(20, 30, 3, 1)
        enemy.facing = -1
        enemy.wind = 1
        game.step(0)
        self.assertEqual(game.player.hp, MAX_HP - 2)
        game.hurt_player(enemy)
        self.assertEqual(game.player.hp, MAX_HP - 2)
        game.player.x = 12
        game.player.hp = 1
        game.invulnerable = 0
        game.hurt_player(enemy)
        self.assertEqual((game.state, game.player.hp), (LOST, 0))
        game.step(RIGHT | ATTACK)
        self.assertEqual(game.state, LOST)

    def test_dodge_cooldown_and_protection(self):
        game = self.solo()
        enemy = game.enemies[0]
        enemy.reset(20, 30, 3, 0)
        enemy.wind = 1
        game.step(DODGE | UP)
        self.assertEqual(game.player.hp, MAX_HP)
        self.assertEqual(game.dodge, 6)
        for _ in range(7):
            game.step(0)
        self.assertEqual(game.player.y, 22)
        game.step(DODGE)
        self.assertEqual(game.dodge, 0)

    def test_progression_victory_and_reset(self):
        game = self.solo()
        pool = tuple(id(enemy) for enemy in game.enemies)
        game.player.hp = 4
        for room in range(3):
            self.assertEqual(game.room, room)
            for enemy in game.enemies:
                enemy.hp = 0
            game.player.x = (room + 1) * 112 - 7
            game.step(0)
        self.assertEqual((game.state, game.player.hp), (WON, 8))
        game.reset()
        self.assertEqual(tuple(id(enemy) for enemy in game.enemies), pool)
        self.assertEqual((game.state, game.room, game.kills), (PLAY, 0, 0))
        self.assertEqual(game.player.hp, MAX_HP)
        self.assertEqual(game.remaining(), 2)

    def test_scripted_full_playthrough(self):
        # Drive public inputs, with no HP or enemy-state modifications.
        game = Game()
        previous_attack = False
        for tick in range(6000):
            if game.state != PLAY:
                break
            alive = [enemy for enemy in game.enemies if enemy.hp > 0]
            keys = 0
            if not alive:
                keys = RIGHT
            else:
                target = min(alive, key=lambda e: abs(e.x - game.player.x)
                             + 2 * abs(e.y - game.player.y))
                dx, dy = target.x - game.player.x, target.y - game.player.y
                if abs(dy) > 2:
                    keys |= DOWN if dy > 0 else UP
                if abs(dx) > 9:
                    keys |= RIGHT if dx > 0 else LEFT
                elif abs(dy) <= 4:
                    keys |= RIGHT if dx >= 0 else LEFT
                    if not previous_attack:
                        keys |= ATTACK
            previous_attack = bool(keys & ATTACK)
            game.step(keys)
        self.assertEqual(game.state, WON, (tick, game.room, game.player.hp))
        self.assertEqual(game.kills, 8)

    def test_long_random_runs_keep_bounded_state(self):
        rng = random.Random(413)
        game = Game()
        for _ in range(15000):
            if game.state != PLAY:
                game.reset()
            game.step(rng.randrange(64))
            self.assertEqual(len(game.enemies), 3)
            self.assertTrue(0 <= game.player.hp <= MAX_HP)
            for actor in [game.player] + game.enemies:
                if actor.hp:
                    self.assertTrue(game.room * 112 + 4 <= actor.x <= (game.room + 1) * 112 - 5)
                    self.assertTrue(22 <= actor.y <= 37)


class EndLoop(Exception):
    pass


class Display:
    """API-signature checking stub, not a hardware or framebuffer emulator."""
    def __init__(self, device):
        self.device = device
        self.labels = set()

    def setFPS(self, fps):
        assert fps == 30

    def setFont(self, path, width, height, spacing):
        assert (path, width, height, spacing) == ("/lib/font5x7.bin", 5, 7, 1)

    def fill(self, color):
        assert color in (0, 1)

    def drawText(self, text, x, y, color):
        assert isinstance(text, str)
        assert 0 <= x and x + len(text) * 6 - 1 <= 72
        assert 0 <= y and y + 7 <= 40
        self.labels.add(text)

    def drawLine(self, x1, y1, x2, y2, color):
        assert all(isinstance(v, int) for v in (x1, y1, x2, y2))
        assert color in (0, 1)

    def drawRectangle(self, x, y, width, height, color):
        assert all(isinstance(v, int) for v in (x, y, width, height))
        assert width >= 0 and height >= 0 and color in (0, 1)

    drawFilledRectangle = drawRectangle

    def setPixel(self, x, y, color):
        assert isinstance(x, int) and isinstance(y, int) and color in (0, 1)

    def update(self):
        self.device.tick += 1
        if self.device.tick >= len(self.device.inputs):
            raise EndLoop()


class DeviceTests(unittest.TestCase):
    def setUp(self):
        self.device = types.ModuleType("thumby")
        self.device.tick = 0
        self.device.inputs = [0]
        self.device.display = Display(self.device)
        self.device.audio = types.SimpleNamespace(play=lambda hz, ms: None, stop=lambda: None)
        self.device.reset = lambda: None
        for name, bit in (("L", LEFT), ("R", RIGHT), ("U", UP),
                          ("D", DOWN), ("A", ATTACK), ("B", DODGE)):
            setattr(self.device, "button" + name, types.SimpleNamespace(
                pressed=lambda bit=bit: bool(self.device.inputs[self.device.tick] & bit)))
        self.old_device = sys.modules.get("thumby")
        self.old_path = sys.path[:]
        sys.modules["thumby"] = self.device
        spec = importlib.util.spec_from_file_location("LanternRun", Path(__file__).with_name("LanternRun.py"))
        self.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.app)

    def tearDown(self):
        sys.path[:] = self.old_path
        if self.old_device is None:
            del sys.modules["thumby"]
        else:
            sys.modules["thumby"] = self.old_device

    def test_menu_pause_resume_and_title(self):
        both = ATTACK | DODGE
        self.device.inputs = ([0, ATTACK, 0] + [RIGHT] * 12 + [both] * 18
                              + [0] + [both] * 18 + [0] + [both] * 18
                              + [0, DOWN, 0])
        with self.assertRaises(EndLoop):
            self.app.main()
        self.assertIn("LANTERN RUN", self.device.display.labels)
        self.assertIn("PAUSED", self.device.display.labels)
        self.assertIn("1/3", self.device.display.labels)

    def test_render_every_room_and_combat_pose(self):
        game = Game()
        order = [game.player] + game.enemies
        for room in range(3):
            game.room = room
            game.load_room()
            for x in (room * 112 + 4, room * 112 + 60, room * 112 + 107):
                game.player.x = x
                for frame in range(30):
                    game.frame = frame
                    game.attack = frame % 8
                    game.combo = frame % 3 + 1
                    game.dodge = frame % 6
                    game.enemies[0].wind = 8
                    self.app.draw_game(self.device.display, game, order)
        self.assertIn("3/3", self.device.display.labels)

    def test_end_screens_retry_and_title(self):
        real_game = Game
        for state, label in ((WON, "DELIVERED!"), (LOST, "TRY AGAIN!")):
            class FinishedGame(real_game):
                def step(self, keys):
                    self.state = state
            self.app.Game = FinishedGame
            self.device.tick = 0
            self.device.inputs = [0, ATTACK, 0, 0, ATTACK, 0, 0, DODGE, 0]
            with self.assertRaises(EndLoop):
                self.app.main()
            self.assertIn(label, self.device.display.labels)

    def test_runtime_imports_are_builtin_or_local(self):
        for name in ("LanternRun.py", "lantern_core.py"):
            source = Path(__file__).with_name(name).read_text()
            tree = ast.parse(source, filename=name)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertTrue(all(alias.name in ("gc", "sys", "thumby") for alias in node.names))
                if isinstance(node, ast.ImportFrom):
                    self.assertEqual(node.module, "lantern_core")


if __name__ == "__main__":
    unittest.main()
