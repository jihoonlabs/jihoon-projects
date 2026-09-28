import thumby
import time

# Display Settings (128x128 RGB565)
thumby.display.setFPS(30)

# Color Palette (RGB565)
COLOR_SKY = 0x18A3
COLOR_BG_BUILDING = 0x3165
COLOR_WALL = 0x52AA
COLOR_STREET = 0x4A49
COLOR_TILE_LINE = 0x2965
COLOR_PLAYER = 0x07E0
COLOR_PLAYER_DASH = 0xFFE0
COLOR_NPC = 0xF800
COLOR_WHITE = 0xFFFF
COLOR_SHADOW = 0x10A2

# World Specifications
WORLD_WIDTH = 512
DEADZONE_LEFT = 48
DEADZONE_RIGHT = 80

# Player State & Physics Parameters
player_x = 40.0
player_y = 80.0
player_z = 0.0          # Height off ground
player_vz = 0.0         # Vertical jump velocity

WALK_SPEED = 1.6
DASH_SPEED = 2.8
GRAVITY = 0.38
JUMP_FORCE = -4.2

is_jumping = False
is_dashing = False

# Double-Tap Dash Detector
last_press_time = 0
last_pressed_btn = None
DOUBLE_TAP_GAP = 300  # ms window for double-tap

cam_x = 0.0

# Entities
entities = [
    {'id': 'player', 'x': player_x, 'y': player_y, 'z': player_z, 'w': 12, 'h': 16, 'color': COLOR_PLAYER},
    {'id': 'npc_guard1', 'x': 120, 'y': 70, 'z': 0, 'w': 12, 'h': 16, 'color': COLOR_NPC},
    {'id': 'npc_guard2', 'x': 230, 'y': 95, 'z': 0, 'w': 12, 'h': 16, 'color': COLOR_NPC},
]

last_tick = time.ticks_ms()

def check_double_tap(btn_name):
    global last_press_time, last_pressed_btn
    now = time.ticks_ms()
    is_double = (last_pressed_btn == btn_name) and (time.ticks_diff(now, last_press_time) < DOUBLE_TAP_GAP)
    last_press_time = now
    last_pressed_btn = btn_name
    return is_double

while True:
    now = time.ticks_ms()
    delta = time.ticks_diff(now, last_tick) / 1000.0
    last_tick = now

    # 1. Dash Input Detection
    if thumby.buttonL.justPressed():
        if check_double_tap('L'): is_dashing = True
    elif thumby.buttonR.justPressed():
        if check_double_tap('R'): is_dashing = True

    # Reset Dash if no directional buttons pressed
    if not (thumby.buttonL.pressed() or thumby.buttonR.pressed() or thumby.buttonU.pressed() or thumby.buttonD.pressed()):
        is_dashing = False

    # 2. Movement Calculation
    move_x, move_y = 0, 0
    if thumby.buttonL.pressed(): move_x -= 1
    if thumby.buttonR.pressed(): move_x += 1
    if thumby.buttonU.pressed(): move_y -= 1
    if thumby.buttonD.pressed(): move_y += 1

    curr_speed = DASH_SPEED if is_dashing else WALK_SPEED
    player_x += move_x * curr_speed
    player_y += move_y * (curr_speed * 0.65)

    # World Boundaries
    player_x = max(8, min(WORLD_WIDTH - 16, player_x))
    player_y = max(58, min(112, player_y))

    # 3. Z-Axis Jump Physics
    if thumby.buttonB.justPressed() and not is_jumping:
        is_jumping = True
        player_vz = JUMP_FORCE

    if is_jumping:
        player_z += player_vz
        player_vz += GRAVITY

        # Ground Collision Check
        if player_z >= 0:
            player_z = 0.0
            player_vz = 0.0
            is_jumping = False

    # Update Player Entity State
    entities[0]['x'] = player_x
    entities[0]['y'] = player_y
    entities[0]['z'] = player_z
    entities[0]['color'] = COLOR_PLAYER_DASH if is_dashing else COLOR_PLAYER

    # 4. Camera Deadzone
    screen_player_x = player_x - cam_x
    if screen_player_x > DEADZONE_RIGHT:
        cam_x += (screen_player_x - DEADZONE_RIGHT)
    elif screen_player_x < DEADZONE_LEFT:
        cam_x -= (DEADZONE_LEFT - screen_player_x)
    cam_x = max(0, min(WORLD_WIDTH - 128, cam_x))

    # 5. Render Scene
    thumby.display.fill(COLOR_SKY)

    # Background Layers
    bg_offset = int(cam_x * 0.4)
    for bx in range(- (bg_offset % 32), 128, 32):
        thumby.display.drawRectangle(bx, 15, 28, 30, COLOR_BG_BUILDING)

    int_cam = int(cam_x)
    thumby.display.drawRectangle(0, 45, 128, 12, COLOR_WALL)
    thumby.display.drawRectangle(0, 57, 128, 71, COLOR_STREET)

    for tx in range(- (int_cam % 24), 128, 24):
        thumby.display.drawLine(tx, 57, tx, 128, COLOR_TILE_LINE)

    # 6. Y-Sorting & Depth Rendering
    sorted_entities = sorted(entities, key=lambda ent: ent['y'])

    for ent in sorted_entities:
        ex = int(ent['x'] - int_cam)
        ey = int(ent['y'])
        ez = int(ent['z'])  # Negative Z moves sprite upward on screen
        ew, eh = ent['w'], ent['h']

        if -ew <= ex <= 128 + ew:
            # Shadow Remains Grounded at (ex, ey)
            shadow_w = max(4, ew - int(abs(ez) * 0.4))  # Shadow shrinks slightly when jumping high
            thumby.display.drawLine(ex + (ew - shadow_w) // 2, ey + eh - 1, ex + (ew + shadow_w) // 2, ey + eh - 1, COLOR_SHADOW)

            # Sprite Lifted by Z Offset: (ey + ez)
            draw_y = ey + ez
            thumby.display.drawRectangle(ex, draw_y, ew, eh, ent['color'])

    # Telemetry HUD
    state_str = "JUMP" if is_jumping else ("DASH" if is_dashing else "WALK")
    thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)
    thumby.display.drawText(f"P02-PHYSICS [{state_str}]", 2, 2, COLOR_WHITE)
    thumby.display.drawText(f"Z:{int(abs(player_z))} Y:{int(player_y)}", 2, 8, COLOR_WHITE)

    thumby.display.update()