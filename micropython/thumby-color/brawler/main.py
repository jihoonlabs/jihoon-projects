import thumby
import time
from engine.camera import Camera
from engine.debug import DebugManager
from entities.base import Entity
from entities.player import Player
from gfx.renderer import Renderer

thumby.display.setFPS(30)

COLOR_NPC = 0xF800
COLOR_WHITE = 0xFFFF
COLOR_GOLD = 0xFFE0

camera = Camera(world_width=512)
player = Player(x=40, y=80)
renderer = Renderer()
debug_mgr = DebugManager()

npc_dummy = Entity('npc_guard1', x=90, y=80, color=COLOR_NPC)
entities = [player, npc_dummy]

# Track button state for SELECT debug toggle
last_menu_pressed = False

while True:
    debug_mgr.update_telemetry()

    # SELECT Button Debug Level Toggle
    if thumby.buttonSelect.justPressed():
        debug_mgr.toggle_level()

    # 1. Update Entities
    player.update(world_width=camera.world_width, debug_mgr=debug_mgr)
    npc_dummy.update_physics()

    # 2. Combat Overlap Check
    if player.is_attacking and player.hitbox:
        if player.hitbox.check_overlap(npc_dummy):
            player.hitbox.resolve_impact(npc_dummy)

    # 3. Update Camera
    camera.update(player.x)

    # 4. Render
    renderer.render_scene(camera, entities, debug_mgr=debug_mgr)

    # HUD & Debug Overlay Rendering
    thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)

    if debug_mgr.level >= 1:
        # Telemetry Bar
        god_str = "[GOD]" if debug_mgr.god_mode else ""
        thumby.display.drawText(f"P05-DBG {debug_mgr.fps:.0f}FPS {debug_mgr.free_mem_kb}KB {god_str}", 2, 2, COLOR_GOLD if debug_mgr.god_mode else COLOR_WHITE)
        thumby.display.drawText(f"PLR [{player.state_str}] HP:{player.hp} Y:{int(player.y)}", 2, 8, COLOR_WHITE)
        thumby.display.drawText(f"DUMMY HP:{npc_dummy.hp} STUN:{npc_dummy.hitstun}", 2, 14, COLOR_WHITE)

    thumby.display.update()