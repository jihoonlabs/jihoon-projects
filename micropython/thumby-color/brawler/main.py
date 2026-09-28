import thumby
import time

# Display Settings (128x128 RGB565)
thumby.display.setFPS(30)

# Color Palette (RGB565 - Generic Oriental Period Style)
COLOR_SKY = 0x18A3
COLOR_BG_BUILDING = 0x3165
COLOR_WALL = 0x52AA
COLOR_STREET = 0x4A49
COLOR_TILE_LINE = 0x2965
COLOR_PLAYER = 0x07E0
COLOR_NPC = 0xF800
COLOR_WHITE = 0xFFFF

# World Map Specifications
WORLD_WIDTH = 512   # Extended Stage Map
WORLD_HEIGHT = 128
DEADZONE_LEFT = 48  # Camera deadzone margins
DEADZONE_RIGHT = 80

# State Management
player_x, player_y = 40, 80
PLAYER_SPEED = 1.8
cam_x = 0.0

# Entities Array
entities = [
    {'id': 'player', 'x': player_x, 'y': player_y, 'w': 12, 'h': 16, 'color': COLOR_PLAYER},
    {'id': 'npc_guard1', 'x': 110, 'y': 70, 'w': 12, 'h': 16, 'color': COLOR_NPC},
    {'id': 'npc_guard2', 'x': 210, 'y': 95, 'w': 12, 'h': 16, 'color': COLOR_NPC},
    {'id': 'npc_merchant', 'x': 340, 'y': 75, 'w': 12, 'h': 16, 'color': COLOR_NPC},
    {'id': 'npc_boss_gate', 'x': 460, 'y': 85, 'w': 14, 'h': 18, 'color': COLOR_WHITE},
]

last_tick = time.ticks_ms()
fps_counter = 0
current_fps = 30
fps_timer = time.ticks_ms()

while True:
    # 1. 30 FPS Sync & Frame Time Delta
    now = time.ticks_ms()
    delta = time.ticks_diff(now, last_tick) / 1000.0
    last_tick = now

    # Real-time FPS Calculation
    fps_counter += 1
    if time.ticks_diff(now, fps_timer) >= 1000:
        current_fps = fps_counter
        fps_counter = 0
        fps_timer = now

    # 2. Input Logic
    move_x = 0
    move_y = 0
    if thumby.buttonL.pressed(): move_x -= 1
    if thumby.buttonR.pressed(): move_x += 1
    if thumby.buttonU.pressed(): move_y -= 1
    if thumby.buttonD.pressed(): move_y += 1

    # Apply Velocity
    player_x += move_x * PLAYER_SPEED
    player_y += move_y * (PLAYER_SPEED * 0.65) # Y-depth movement is slower for perspective

    # Stage Boundaries
    player_x = max(8, min(WORLD_WIDTH - 16, player_x))
    player_y = max(58, min(112, player_y))

    # Update Entity Entry
    entities[0]['x'] = player_x
    entities[0]['y'] = player_y

    # 3. Camera Deadzone Logic
    screen_player_x = player_x - cam_x
    if screen_player_x > DEADZONE_RIGHT:
        cam_x += (screen_player_x - DEADZONE_RIGHT)
    elif screen_player_x < DEADZONE_LEFT:
        cam_x -= (DEADZONE_LEFT - screen_player_x)

    # Clamp Camera to World Edge
    cam_x = max(0, min(WORLD_WIDTH - 128, cam_x))

    # 4. Multi-Layer Background Rendering (Screen Offset Aware)
    thumby.display.fill(COLOR_SKY)

    # Parallax Distant Buildings/Tiles
    bg_offset = int(cam_x * 0.4)
    for bx in range(- (bg_offset % 32), 128, 32):
        thumby.display.drawRectangle(bx, 15, 28, 30, COLOR_BG_BUILDING)

    # Main Wall & Street Floor
    int_cam = int(cam_x)
    thumby.display.drawRectangle(0, 45, 128, 12, COLOR_WALL)
    thumby.display.drawRectangle(0, 57, 128, 71, COLOR_STREET)

    # Tile Grid Details on Street
    for tx in range(- (int_cam % 24), 128, 24):
        thumby.display.drawLine(tx, 57, tx, 128, COLOR_TILE_LINE)

    # 5. Y-Sorting & Screen Culling Pipeline
    # Sort entities based on Y position (Depth Order)
    sorted_entities = sorted(entities, key=lambda ent: ent['y'])

    visible_count = 0
    for ent in sorted_entities:
        ex = int(ent['x'] - int_cam)
        ey = int(ent['y'])
        ew = ent['w']
        eh = ent['h']

        # Culling Check: Only process and render if inside screen boundary + margin
        if -ew <= ex <= 128 + ew and -eh <= ey <= 128 + eh:
            visible_count += 1
            # Ground Contact Shadow
            thumby.display.drawLine(ex + 2, ey + eh - 1, ex + ew - 2, ey + eh - 1, 0x0000)
            # Entity Body Placeholder
            thumby.display.drawRectangle(ex, ey, ew, eh, ent['color'])

    # 6. Engine Telemetry & Debug HUD
    thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)
    thumby.display.drawText(f"P01-ENGINE FPS:{current_fps}", 2, 2, COLOR_WHITE)
    thumby.display.drawText(f"CAM:{int(cam_x)} VIS:{visible_count}/{len(entities)}", 2, 8, COLOR_WHITE)

    thumby.display.update()