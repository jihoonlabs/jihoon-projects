import thumby
import time
from engine.camera import Camera
from entities.base import Entity
from entities.player import Player
from gfx.renderer import Renderer

thumby.display.setFPS(30)

COLOR_NPC = 0xF800
COLOR_WHITE = 0xFFFF

camera = Camera(world_width=512)
player = Player(x=40, y=80)
renderer = Renderer()

npc_dummy = Entity('npc_guard1', x=90, y=80, color=COLOR_NPC)
entities = [player, npc_dummy]

while True:
    # 1. Update Entities
    player.update(world_width=camera.world_width)
    npc_dummy.update_physics()

    # 2. Combat Hitbox Overlap Pipeline
    if player.is_attacking and player.hitbox:
        if player.hitbox.check_overlap(npc_dummy):
            player.hitbox.resolve_impact(npc_dummy)

    # 3. Update Camera
    camera.update(player.x)

    # 4. Render Scene
    renderer.render_scene(camera, entities)

    # Telemetry HUD
    thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)
    thumby.display.drawText(f"P04-FSM [{player.state_str}] HP:{player.hp}", 2, 2, COLOR_WHITE)
    thumby.display.drawText(f"DUMMY HP:{npc_dummy.hp} STUN:{npc_dummy.hitstun}", 2, 8, COLOR_WHITE)

    thumby.display.update()