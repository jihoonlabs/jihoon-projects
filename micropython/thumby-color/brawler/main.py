import thumby
import time

# Display Settings (128x128 RGB565)
thumby.display.setFPS(30)

# Color Palette (RGB565)
COLOR_SKY = 0x2104
COLOR_WALL = 0x4208
COLOR_ROAD = 0x31A6
COLOR_ROAD_LINE = 0x630C
COLOR_PLAYER = 0x07E0
COLOR_NPC = 0xF800
COLOR_WHITE = 0xFFFF

# World & Camera State
WORLD_WIDTH = 384  # 3 Screens wide (128 * 3)
cam_x = 0

# Player State
player_x = 30
player_y = 80
PLAYER_SPEED = 2.0

# Entities for Depth Sorting Test
entities = [
    {'id': 'player', 'x': player_x, 'y': player_y, 'color': COLOR_PLAYER},
    {'id': 'npc1', 'x': 80, 'y': 65, 'color': COLOR_NPC},
    {'id': 'npc2', 'x': 140, 'y': 95, 'color': COLOR_NPC},
    {'id': 'npc3', 'x': 220, 'y': 75, 'color': COLOR_NPC},
]

last_tick = time.ticks_ms()

while True:
    # 1. 30 FPS Frame Timing Control
    current_tick = time.ticks_ms()
    delta_time = time.ticks_diff(current_tick, last_tick)
    last_tick = current_tick

    # 2. Input Processing (8-Way Movement Test)
    if thumby.buttonL.pressed():
        player_x -= PLAYER_SPEED
    if thumby.buttonR.pressed():
        player_x += PLAYER_SPEED
    if thumby.buttonU.pressed():
        player_y -= PLAYER_SPEED * 0.75
    if thumby.buttonD.pressed():
        player_y += PLAYER_SPEED * 0.75

    # World Boundaries (Y-axis Depth Area)
    player_x = max(8, min(WORLD_WIDTH - 16, player_x))
    player_y = max(55, min(110, player_y))

    # Update Player Entity Position
    entities[0]['x'] = player_x
    entities[0]['y'] = player_y

    # 3. Camera Tracking with Deadzone
    # Keep player centered when moving right/left
    target_cam_x = player_x - 64 + 6
    cam_x = max(0, min(WORLD_WIDTH - 128, target_cam_x))

    # 4. Render Background & World
    thumby.display.fill(COLOR_SKY)

    # Render Screen-relative Wall & Road
    thumby.display.drawRectangle(0 - int(cam_x), 20, WORLD_WIDTH, 30, COLOR_WALL)
    thumby.display.drawRectangle(0 - int(cam_x), 50, WORLD_WIDTH, 70, COLOR_ROAD)

    # Road Markings (Period Action Street Detail)
    for rx in range(0, WORLD_WIDTH, 32):
        screen_rx = rx - int(cam_x)
        if -10 <= screen_rx <= 128:
            thumby.display.drawLine(screen_rx, 52, screen_rx + 16, 52, COLOR_ROAD_LINE)

    # 5. Y-Sorting Depth Rendering
    # Sort entities by Y-coordinate so lower entities draw over higher ones
    sorted_entities = sorted(entities, key=lambda e: e['y'])

    for e in sorted_entities:
        screen_x = int(e['x'] - cam_x)
        screen_y = int(e['y'])

        # Culling: Only draw if visible on the 128x128 screen
        if -16 <= screen_x <= 128:
            # Shadow
            thumby.display.drawLine(screen_x + 2, screen_y + 12, screen_x + 10, screen_y + 12, 0x0000)
            # Body Rectangle (Placeholders for Sprites)
            thumby.display.drawRectangle(screen_x, screen_y, 12, 14, e['color'])

    # 6. Debug HUD
    thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)
    thumby.display.drawText(f"P1 CORE CAM:{int(cam_x)} Y:{int(player_y)}", 2, 2, COLOR_WHITE)

    thumby.display.update()