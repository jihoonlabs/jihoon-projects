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

thumby.display.setFPS(30)

COLOR_WHITE = 0xFFFF
COLOR_GOLD = 0xFFE0

# 1. Engine & Entity Initialization
camera = Camera(world_width=STAGE_01_DATA["world_width"])
player = Player(x=40, y=80)
renderer = Renderer()
debug_mgr = DebugManager()

# Dynamic Enemy Spawning Pool for StageManager
entities = [player]

def enemy_factory(e_type, spawn_x, spawn_y, direction):
    """Spawns enemies dynamically requested by StageManager wave specs."""
    enemy = Enemy(e_type, x=spawn_x, y=spawn_y)
    enemy.facing = direction
    entities.append(enemy)
    return enemy

# 2. Stage Manager & UI Subsystems
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
        # A. Update Stage State & Wave Lock Progress
        world_enemies = [e for e in entities if isinstance(e, Enemy)]
        stage_mgr.update(player, world_enemies)

        # Trigger Dialogue if StageManager queue has one
        if stage_mgr.current_dialogue and not dialogue_ui.active:
            dialogue_ui.start_dialogue(stage_mgr.current_dialogue)
            stage_mgr.current_dialogue = None

        # B. Update Physics & AI (Paused during Dialogue)
        if not dialogue_ui.active:
            player.update(world_width=camera.world_width, debug_mgr=debug_mgr)

            # Player forward movement clears GO! indicator
            if thumby.buttonRight.pressed():
                stage_mgr.on_player_move_forward()

            for enemy in world_enemies:
                if getattr(enemy, 'hp', 0) > 0:
                    enemy.update_ai(player, world_width=camera.world_width)

            # C. Combat Impact Overlap Pipeline
            for enemy in world_enemies:
                if getattr(enemy, 'hp', 0) <= 0:
                    continue

                # Player -> Enemy Impact
                if player.is_attacking and player.hitbox:
                    if player.hitbox.check_overlap(enemy):
                        stop_req = player.hitbox.resolve_impact(enemy, camera=camera)
                        hitstop_frames = max(hitstop_frames, stop_req)

                # Enemy -> Player Impact
                if enemy.is_attacking and enemy.hitbox:
                    if enemy.hitbox.check_overlap(player):
                        stop_req = enemy.hitbox.resolve_impact(player, camera=camera)
                        hitstop_frames = max(hitstop_frames, stop_req)

    # D. Camera Update with Stage Boundary Locking
    camera.update(player.x)

    # E. UI Animations Update
    go_indicator.update(stage_mgr.show_go_indicator)
    dialogue_ui.update()

    # 3. Render Scene Pipeline
    renderer.render_scene(camera, entities, debug_mgr=debug_mgr)

    # 4. Render UI Overlays
    if stage_mgr.show_go_indicator:
        go_indicator.draw(thumby.display, is_active=True)

    if dialogue_ui.active:
        dialogue_ui.draw(thumby.display)

    # Telemetry HUD
    thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)

    if debug_mgr.level >= 1:
        god_str = "[GOD]" if debug_mgr.god_mode else ""
        wave_str = f"WAVE:{stage_mgr.current_wave_index}"
        thumby.display.drawText(f"P08-STAGE {debug_mgr.fps:.0f}FPS {debug_mgr.free_mem_kb}KB {god_str}", 2, 2, COLOR_GOLD if debug_mgr.god_mode else COLOR_WHITE)
        thumby.display.drawText(f"{wave_str} STOP:{hitstop_frames} SHAKE:{camera.shake_intensity:.1f}", 2, 8, COLOR_WHITE)

    thumby.display.update()