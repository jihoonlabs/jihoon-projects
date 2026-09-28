import thumby
import time
from engine.camera import Camera
from engine.debug import DebugManager
from entities.player import Player
from entities.enemy import Enemy
from gfx.renderer import Renderer

thumby.display.setFPS(30)

COLOR_WHITE = 0xFFFF
COLOR_GOLD = 0xFFE0

camera = Camera(world_width=512)
player = Player(x=40, y=80)
enemy_guard = Enemy('guard_01', x=140, y=80)
renderer = Renderer()
debug_mgr = DebugManager()

entities = [player, enemy_guard]

while True:
    debug_mgr.update_telemetry()

    if thumby.buttonSelect.justPressed():
        debug_mgr.toggle_level()

    # 1. Update Player & Enemy AI
    player.update(world_width=camera.world_width, debug_mgr=debug_mgr)
    enemy_guard.update_ai(player, world_width=camera.world_width)

    # 2. Player -> Enemy Attack Impact
    if player.is_attacking and player.hitbox:
        if player.hitbox.check_overlap(enemy_guard):
            player.hitbox.resolve_impact(enemy_guard)

    # 3. Enemy -> Player Attack Impact
    if enemy_guard.is_attacking and enemy_guard.hitbox:
        if enemy_guard.hitbox.check_overlap(player):
            enemy_guard.hitbox.resolve_impact(player)

    # 4. Camera Tracking
    camera.update(player.x)

    # 5. Scene Render
    renderer.render_scene(camera, entities, debug_mgr=debug_mgr)

    # Telemetry HUD
    thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)

    if debug_mgr.level >= 1:
        god_str = "[GOD]" if debug_mgr.god_mode else ""
        thumby.display.drawText(f"P06-AI {debug_mgr.fps:.0f}FPS {debug_mgr.free_mem_kb}KB {god_str}", 2, 2, COLOR_GOLD if debug_mgr.god_mode else COLOR_WHITE)
        thumby.display.drawText(f"PLR [{player.state_str}] HP:{player.hp}", 2, 8, COLOR_WHITE)
        thumby.display.drawText(f"ENM [{enemy_guard.state}] HP:{enemy_guard.hp} STUN:{enemy_guard.hitstun}", 2, 14, COLOR_WHITE)

    thumby.display.update()