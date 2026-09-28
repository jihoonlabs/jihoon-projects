import thumby
import time
from engine.camera import Camera
from entities.base import Entity
from entities.player import Player
from gfx.renderer import Renderer

thumby.display.setFPS(30)

COLOR_NPC = 0xF800
COLOR_WHITE = 0xFFFF

# Initializations
camera = Camera(world_width=512)
player = Player(x=40, y=80)
renderer = Renderer()

entities = [
    player,
    Entity('npc_guard1', x=120, y=70, color=COLOR_NPC),
    Entity('npc_guard2', x=230, y=95, color=COLOR_NPC),
]

while True:
    # 1. Update Entities
    player.update(world_width=camera.world_width)

    # 2. Update Camera
    camera.update(player.x)

    # 3. Render
    renderer.render_scene(camera, entities)

    # Telemetry HUD
    thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)
    thumby.display.drawText(f"P02-PHYSICS [{player.state_str}]", 2, 2, COLOR_WHITE)
    thumby.display.drawText(f"Z:{int(abs(player.z))} Y:{int(player.y)}", 2, 8, COLOR_WHITE)

    thumby.display.update()