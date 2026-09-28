import thumby
import time
from engine.camera import Camera
from engine.debug import DebugManager
from entities.player import Player
from entities.enemy import Enemy
from gfx.renderer import Renderer

# Phase 08 Modules
from data.stage_01 import STAGE_01_DATA
from engine.stage_manager import StageManager
from ui.go_indicator import GoIndicator
from ui.dialogue import DialogueUI

# Phase 09 Modules
from data.boss_spec import BOSS_GENERAL_01_SPEC
from entities.boss import Boss
from gfx.telegraph import TelegraphVisualizer

thumby.display.setFPS(30)

COLOR_WHITE = 0xFFFF
COLOR_GOLD = 0xFFE0
COLOR_RED = 0xF800

# 1. Engine & Entity Initialization
camera = Camera(world_width=STAGE_01_DATA["world_width"])
player = Player(x=40, y=80)
boss = Boss(spec=BOSS_GENERAL_01_SPEC, x=380, y=90) # Phase 09 Boss
renderer = Renderer()
debug_mgr = DebugManager()
telegraph_vis = TelegraphVisualizer()

# Entity Pool (Includes Player, Stage Enemies, and Boss)
entities = [player, boss]

def enemy_factory(e_type, spawn_x, spawn_y, direction):
    """Spawns standard wave enemies requested by StageManager."""
    enemy = Enemy(e_type, x=spawn_x, y=spawn_y)
    enemy.facing = direction
    entities.append(enemy)
    return enemy

# 2. Subsystems Setup
stage_mgr = StageManager(STAGE_01_DATA, camera, enemy_factory=enemy_factory)
go_indicator = GoIndicator(screen_width=128, screen_height=128)
dialogue_ui = DialogueUI(screen_width=128, screen_height=128)

hitstop_frames = 0

while True:
    debug_mgr.update_telemetry()

    if thumby.buttonSelect.justPressed():
        debug_mgr.toggle_level()

    # Dialogue Input Handling (Button A)
    if dialogue_ui.active:
        dialogue_ui.handle_input(thumby.buttonA.justPressed())

    # Hitstop Frame Lock
    if hitstop_frames > 0:
        hitstop_frames -= 1
    else:
        # A. Stage Manager Update
        world_enemies = [e for e in entities if (isinstance(e, Enemy) or isinstance(e, Boss))]
        stage_mgr.update(player, world_enemies)

        # Trigger Dialogue Queue
        if stage_mgr.current_dialogue and not dialogue_ui.active:
            dialogue_ui.start_dialogue(stage_mgr.current_dialogue)
            stage_mgr.current_dialogue = None

        # B. Gameplay Logic (Active when Dialogue is closed)
        if not dialogue_ui.active:
            player.update(world_width=camera.world_width, debug_mgr=debug_mgr)

            if thumby.buttonRight.pressed():
                stage_mgr.on_player_move_forward()

            # Update Standard Enemy AI
            for enemy in world_enemies:
                if isinstance(enemy, Enemy) and not isinstance(enemy, Boss):
                    if getattr(enemy, 'hp', 0) > 0:
                        enemy.update_ai(player, world_width=camera.world_width)

            # Update Phase 09 Boss Logic
            if getattr(boss, 'hp', 0) > 0:
                boss.update_boss_ai(player, world_width=camera.world_width)

            # C. Combat Impact Overlap Pipeline
            for enemy in world_enemies:
                if getattr(enemy, 'hp', 0) <= 0:
                    continue

                # Player -> Boss/Enemy Impact
                if player.is_attacking and player.hitbox:
                    if player.hitbox.check_overlap(enemy):
                        # Boss handles damage & Super Armor internal check
                        if isinstance(enemy, Boss):
                            enemy.take_damage(damage=10, knockback_x=2 if not enemy.super_armor else 0)
                        
                        stop_req = player.hitbox.resolve_impact(enemy, camera=camera)
                        hitstop_frames = max(hitstop_frames, stop_req)

                # Boss/Enemy -> Player Impact
                if getattr(enemy, 'is_attacking', False) and getattr(enemy, 'hitbox', None):
                    if enemy.hitbox.check_overlap(player):
                        stop_req = enemy.hitbox.resolve_impact(player, camera=camera)
                        hitstop_frames = max(hitstop_frames, stop_req)

    # D. Camera System Update
    camera.update(player.x)

    # E. UI Animations Update
    go_indicator.update(stage_mgr.show_go_indicator)
    dialogue_ui.update()

    # 3. Render World Scene
    renderer.render_scene(camera, entities, debug_mgr=debug_mgr)

    # Render Phase 09 Boss Telegraph Warning Area
    if not dialogue_ui.active and boss.hp > 0:
        telegraph_vis.draw_boss_telegraph(thumby.display, camera, boss)

    # 4. Render UI Overlays
    if stage_mgr.show_go_indicator:
        go_indicator.draw(thumby.display, is_active=True)

    if dialogue_ui.active:
        dialogue_ui.draw(thumby.display)

    # Telemetry HUD
    thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)

    if debug_mgr.level >= 1:
        god_str = "[GOD]" if debug_mgr.god_mode else ""
        boss_hp_pct = int((boss.hp / boss.max_hp) * 100) if boss.hp > 0 else 0
        arm_str = "[ARM]" if boss.super_armor else ""
        
        thumby.display.drawText(f"P09-BOSS {debug_mgr.fps:.0f}FPS {debug_mgr.free_mem_kb}KB {god_str}", 2, 2, COLOR_GOLD if debug_mgr.god_mode else COLOR_WHITE)
        thumby.display.drawText(f"BOSS HP:{boss_hp_pct}% P{boss.phase} {arm_str}", 2, 8, COLOR_RED if boss.phase == 2 else COLOR_WHITE)

    thumby.display.update()