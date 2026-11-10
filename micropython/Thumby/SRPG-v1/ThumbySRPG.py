"""Playable first-pass tactical SRPG for the standard monochrome Thumby."""

import gc
import sys
import time

import thumby

# The device launcher need not put the game folder on the module path;
# add it before importing sibling modules (same pattern as ThumbyBrawlBase).
if sys.implementation.name == "micropython":
    sys.path.append("/Games/SRPG-v1")

from assets import (ENEMY_BATTLE, ENEMY_ICON, REAL_BATTLE, REAL_CUTIN,
                    REAL_ICON, SHIP_BATTLE, SHIP_CUTIN, SHIP_ICON,
                    SUPER_BATTLE, SUPER_CUTIN, SUPER_ICON, CUSTOM_BATTLE)
from assets import draw_bitmap
from rules import (BASE_MAX_HP, BASE_TILE, MAP_HEIGHT, MAP_TERRAIN,
                   MAP_WIDTH, alive_units,
                   create_units, in_range, mission_result, reachable_tiles,
                   resolve_attack, resolve_base_attack, reset_turn, unit_at)

SCREEN_W = 72
SCREEN_H = 40
TILE = 8
VIEW_TILES_W = SCREEN_W // TILE
VIEW_TILES_H = SCREEN_H // TILE

STATE_TITLE = 0
STATE_MAP = 1
STATE_COMMAND = 2
STATE_MOVE = 3
STATE_TARGET = 4
STATE_ATTACK = 5
STATE_VICTORY = 6
STATE_DEFEAT = 7
STATE_WEAPONS = 8
STATE_STATUS = 9
STATE_BENCH = 10

FPS = 20
# Built-in Thumby fonts: (path, width, height, spacing). 5x7 is the default.
FONT_BIG = ("/lib/font5x7.bin", 5, 7, 1)
FONT_SMALL = ("/lib/font3x5.bin", 3, 5, 1)

COMMANDS = ("MOVE", "ATTACK", "STATUS", "END")
COMMAND_LABELS = ("MOVE", "ATK", "STAT", "END")

units = create_units()
mission_index = 0
cursor_x = 1
cursor_y = 2
camera_x = 0
camera_y = 0
selected_unit = None
menu_index = 0
attack_target = None
attack_is_special = False
selected_weapon = None
attack_weapon = None
weapon_index = 0
attack_damage = 0
attack_timer = 0
attack_phase = 0
message = "SELECT UNIT"
base_hp = BASE_MAX_HP
state = STATE_TITLE
current_font = None
move_tiles = None
status_page = 0
bench_results = None
# Static screens are drawn once on entry; the buffer keeps them afterwards.
STATIC_STATES = (STATE_TITLE, STATE_VICTORY, STATE_DEFEAT, STATE_BENCH)
last_static = None

thumby.display.setFPS(FPS)


def use_font(font):
    """Switch fonts only when needed; setFont reloads the font file."""
    global current_font
    if font is not current_font:
        thumby.display.setFont(*font)
        current_font = font


def text_width(text, font=None):
    font = font or current_font or FONT_BIG
    return len(text) * (font[1] + font[3])


def draw_text(text, x, y, color=1):
    thumby.display.drawText(text, x, y, color)


def draw_text_right(text, right, y, color=1):
    draw_text(text, right - text_width(text) + 1, y, color)


def draw_text_center(text, y, color=1):
    draw_text(text, (SCREEN_W - text_width(text) + 1) // 2, y, color)


def move_cursor(dx, dy):
    global cursor_x, cursor_y
    cursor_x = max(0, min(MAP_WIDTH - 1, cursor_x + dx))
    cursor_y = max(0, min(MAP_HEIGHT - 1, cursor_y + dy))


def update_camera():
    global camera_x, camera_y
    camera_x = max(0, min(MAP_WIDTH - VIEW_TILES_W,
                          cursor_x - VIEW_TILES_W // 2))
    camera_y = max(0, min(MAP_HEIGHT - VIEW_TILES_H,
                          cursor_y - VIEW_TILES_H // 2))


def draw_hangar_background():
    display = thumby.display
    display.fill(0)
    # Sparse girders and dither preserve a readable one-bit industrial backdrop.
    display.drawLine(0, 8, 71, 4, 1)
    display.drawLine(0, 12, 71, 8, 1)
    display.drawLine(4, 13, 4, 25, 1)
    display.drawLine(67, 9, 67, 24, 1)
    display.drawLine(0, 27, 71, 27, 1)
    display.drawLine(0, 34, 71, 34, 1)
    display.drawLine(0, 39, 71, 31, 1)
    display.drawLine(20, 39, 35, 28, 1)
    display.drawLine(51, 39, 37, 28, 1)
    for y in range(2, 10, 3):
        for x in range((y % 4), 70, 7):
            display.setPixel(x, y, 1)
    for x in range(5, 71, 8):
        display.setPixel(x, 30 + ((x // 8) % 3), 1)


def draw_weapon_rows(weapons, highlight=None, top=7):
    """One 6 px row per weapon: full name, power and range."""
    display = thumby.display
    for index, weapon in enumerate(weapons):
        y = top + index * 6
        color = 1
        if index == highlight:
            display.drawFilledRectangle(0, y - 1, SCREEN_W, 7, 1)
            color = 0
        draw_text(weapon["name"], 2, y, color)
        draw_text_right(str(weapon["power"]), 57, y, color)
        draw_text_right("R" + str(weapon["range"]), 70, y, color)


def draw_weapon_menu():
    display = thumby.display
    display.fill(0)
    use_font(FONT_SMALL)
    draw_text(selected_unit["id"] + " WEAPON", 2, 0)
    draw_text_right("POW RNG", 70, 0)
    display.drawLine(0, 5, SCREEN_W - 1, 5, 1)
    draw_weapon_rows(selected_unit["weapons"], weapon_index)


def draw_status_screen(unit):
    """Compact STATUS: page 0 core stats, page 1 weapons (LEFT/RIGHT)."""
    display = thumby.display
    display.fill(0)
    use_font(FONT_SMALL)
    draw_text(unit["id"] + " " + unit["kind"], 2, 0)
    draw_text_right(str(status_page + 1) + "/2", 70, 0)
    display.drawLine(0, 5, SCREEN_W - 1, 5, 1)
    if status_page == 1:
        draw_weapon_rows(unit["weapons"])
        return
    rows = (("HP", str(unit["hp"]) + "/" + str(unit["max_hp"])),
            ("EN", str(unit["en"]) + "/" + str(unit["max_en"])),
            ("MOB", str(unit["mobility"])),
            ("ARM", str(unit["armor"])))
    for index, (label, value) in enumerate(rows):
        y = 8 + index * 7
        draw_text(label, 2, y)
        draw_text_right(value, 46, y)
    # HP and EN bars beside their numbers.
    for index, (now, top) in enumerate(((unit["hp"], unit["max_hp"]),
                                        (unit["en"], unit["max_en"]))):
        y = 9 + index * 7
        display.drawRectangle(50, y, 20, 3, 1)
        width = max(0, min(18, now * 18 // max(1, top)))
        if width:
            display.drawLine(51, y + 1, 50 + width, y + 1, 1)
    draw_text("<> WEAPONS", 2, 35)


def draw_map():
    display = thumby.display
    if state == STATE_WEAPONS:
        draw_weapon_menu()
        return
    if state == STATE_STATUS:
        draw_status_screen(selected_unit)
        return
    display.fill(0)
    update_camera()
    movement_tiles = move_tiles if state == STATE_MOVE and move_tiles else ()
    # One lookup table per frame instead of scanning every unit per tile.
    occupied = {}
    for unit in units:
        if unit["hp"] > 0:
            occupied[unit["y"] * MAP_WIDTH + unit["x"]] = unit
    # Keep the map full-screen while idle; details appear only after selection.
    for vy in range(VIEW_TILES_H):
        for vx in range(VIEW_TILES_W):
            wx = camera_x + vx
            wy = camera_y + vy
            x = vx * TILE
            y = vy * TILE
            terrain = MAP_TERRAIN[wy][wx]
            display.drawRectangle(x, y, TILE, TILE, 1)
            if terrain == "#":
                display.drawFilledRectangle(x + 1, y + 1, TILE - 2, TILE - 2, 1)
                display.setPixel(x + 3, y + 3, 0)
                display.setPixel(x + 5, y + 5, 0)
            elif (wx + wy) % 4 == 0:
                display.setPixel(x + 3, y + 4, 1)
            if (wx, wy) == BASE_TILE:
                display.drawRectangle(x + 1, y + 1, 6, 6, 1)
                display.drawLine(x + 2, y + 3, x + 5, y + 3, 1)
                display.drawFilledRectangle(x + 3, y + 4, 2, 2, 1)
            if selected_unit is not None and state == STATE_MOVE:
                if (wx, wy) in movement_tiles:
                    display.setPixel(x + 1, y + 1, 1)
                    display.setPixel(x + 2, y + 1, 1)
            elif selected_unit is not None and state == STATE_TARGET:
                weapon_range = (selected_weapon["range"] if selected_weapon
                                else selected_unit["range"])
                if (abs(wx - selected_unit["x"]) + abs(wy - selected_unit["y"])
                        <= weapon_range):
                    display.setPixel(x + 1, y + 6, 1)
            unit = occupied.get(wy * MAP_WIDTH + wx)
            if unit is not None:
                if unit["team"] == "enemy":
                    icon = ENEMY_ICON
                elif unit["kind"] == "SHIP":
                    icon = SHIP_ICON
                else:
                    icon = REAL_ICON if unit["kind"] == "REAL" else SUPER_ICON
                draw_bitmap(display, x, y, icon)
                if unit["team"] == "enemy":
                    display.setPixel(x + 6, y + 1, 1)
            if selected_unit is unit and unit is not None:
                display.drawRectangle(x, y, TILE, TILE, 1)
    cx = (cursor_x - camera_x) * TILE
    cy = (cursor_y - camera_y) * TILE
    display.drawRectangle(cx + 1, cy + 1, TILE - 2, TILE - 2, 1)
    if state == STATE_COMMAND:
        draw_command_overlay(display)
    elif state in (STATE_MOVE, STATE_TARGET):
        draw_mode_strip(display, cy)


def draw_command_overlay(display):
    # The command overlay is contextual and appears only after A.
    use_font(FONT_BIG)
    overlay_x = 41
    display.drawFilledRectangle(overlay_x, 0, SCREEN_W - overlay_x, SCREEN_H, 0)
    display.drawRectangle(overlay_x, 0, SCREEN_W - overlay_x, SCREEN_H, 1)
    draw_text(selected_unit["id"], overlay_x + 3, 1)
    hp_width = max(0, min(10, selected_unit["hp"] * 10 // selected_unit["max_hp"]))
    display.drawRectangle(overlay_x + 17, 3, 12, 4, 1)
    if hp_width:
        display.drawFilledRectangle(overlay_x + 18, 4, hp_width, 2, 1)
    # 8 px rows leave a 1 px gap between the 7 px tall labels.
    for index, command in enumerate(COMMANDS):
        y = 9 + index * 8
        label = COMMAND_LABELS[index]
        if command == "MOVE" and (selected_unit["moved"] or selected_unit["move"] == 0):
            label = "MOV-"
        if command == "ATTACK" and selected_unit["acted"]:
            label = "ATK-"
        if index == menu_index:
            display.drawFilledRectangle(overlay_x + 1, y - 1, 29, 8, 1)
            draw_text(label, overlay_x + 3, y, 0)
        else:
            draw_text(label, overlay_x + 3, y, 1)


def draw_mode_strip(display, cursor_screen_y):
    """MOVE/TARGET label on a black strip, kept away from the cursor row."""
    use_font(FONT_SMALL)
    y = 33 if cursor_screen_y < 16 else 0
    display.drawFilledRectangle(0, y, SCREEN_W, 7, 0)
    display.drawLine(0, y + 6 if y == 0 else y, SCREEN_W - 1,
                     y + 6 if y == 0 else y, 1)
    if state == STATE_MOVE:
        label = "MOVE " + str(selected_unit["move"])
    else:
        weapon = selected_weapon or {"short": "ATK", "range": selected_unit["range"]}
        label = weapon["short"] + " R" + str(weapon["range"])
    text_y = y + 1 if y == 0 else y + 2
    draw_text(label, 2, text_y)
    # Short hints only, so they never run into the label.
    hint = {"NO TARGET": "NO TGT", "OUT RANGE": "OUT RNG"}.get(message, "A:OK")
    draw_text_right(hint, 70, text_y)


def draw_title():
    display = thumby.display
    draw_hangar_background()
    display.drawFilledRectangle(4, 5, 64, 29, 0)
    display.drawRectangle(3, 4, 66, 31, 1)
    use_font(FONT_BIG)
    draw_text_center("SRPG-V1", 8)
    use_font(FONT_SMALL)
    draw_text_center("MONO TACTICS", 19)
    draw_text_center("A:START", 27)


def draw_battle_units(attacker, defender, impact=False):
    display = thumby.display
    # Hide all HP/EN text during the action; the combat panel stays uncluttered.
    display.fill(1)
    display.drawLine(0, 32, 71, 32, 0)
    melee = attack_weapon is not None and attack_weapon["style"] in ("blade", "fist")
    attacker_x = 5
    attacker_y = 7
    attacker_pose = "idle"
    defender_x = 51
    defender_pose = "idle"
    if melee and attack_phase == 2:
        # Move into range, then strike. The figure advances instead of only
        # drawing a slash across the gap.
        attacker_x += min(24, attack_timer * 3)
        attacker_pose = "walk" if attack_timer < 5 else "strike"
    elif melee and attack_phase == 3:
        attacker_x += max(0, 24 - attack_timer * 3)
        attacker_pose = "recover"
        if attack_timer < 5:
            defender_x += 3
            defender_pose = "recoil"
    elif not melee and attack_phase == 2:
        # Recoil and settle around the launch frame so ranged attacks also move.
        attacker_pose = "fire"
        if attack_timer in (0, 1):
            attacker_y = 6
        elif attack_timer in (2, 3):
            attacker_x = 3
    elif attack_phase == 3 and attack_timer < 5:
        defender_x += 2
        defender_pose = "recoil"
    draw_combat_mech(display, attacker, attacker_x, attacker_y, facing=1,
                     pose=attacker_pose, weapon=attack_weapon)
    draw_combat_mech(display, defender, defender_x, 7, facing=-1,
                     pose=defender_pose)

    # Sparse manga speed lines frame the moving figures.
    if melee and attack_phase == 2 and attack_timer >= 4:
        display.drawLine(0, 11, 7, 11, 0)
        display.drawLine(0, 22, 10, 22, 0)
    elif not melee and attack_phase == 2 and attack_timer < 2:
        display.drawLine(0, 11, 5, 11, 0)
        display.drawLine(0, 22, 5, 22, 0)

    shot_x = min(52, 23 + attack_timer * 4)
    if melee:
        if attack_phase == 2 and attack_timer >= 5:
            if attack_weapon["style"] == "fist":
                display.drawLine(attacker_x + 11, 16, attacker_x + 18, 16, 0)
                display.drawFilledRectangle(attacker_x + 17, 14, 3, 4, 0)
            else:
                display.drawLine(attacker_x + 11, 14, attacker_x + 17, 8, 0)
                display.drawLine(attacker_x + 12, 15, attacker_x + 18, 9, 0)
    elif attack_phase == 2:
        if attack_weapon is not None and attack_weapon["style"] == "beam":
            display.drawLine(20, 14, shot_x, 14, 0)
            display.drawLine(20, 16, shot_x, 16, 0)
        else:
            display.drawLine(max(20, shot_x - 5), 15, shot_x, 15, 0)
            display.drawFilledRectangle(shot_x, 14, 2, 2, 0)

    use_font(FONT_SMALL)
    if impact:
        for x, y in ((47, 12), (50, 9), (53, 15), (48, 19), (56, 11), (58, 18)):
            display.setPixel(x, y, 0)
        draw_text_right("-" + str(attack_damage), 70, 25, 0)
    draw_text(attack_name(attacker), 2, 34, 0)


def draw_battle_gauges(display, unit, left, width):
    """HP bar with its number, and a numeric EN value, for one fighter."""
    hp = max(0, min(unit["max_hp"], unit["hp"]))
    en = max(0, min(unit.get("max_en", 0), unit.get("en", 0)))
    max_hp = max(1, unit["max_hp"])
    draw_text("HP", left, 9, 0)
    draw_text_right(str(hp), left + width - 1, 9, 0)
    display.drawRectangle(left, 15, width, 4, 0)
    fill = hp * (width - 2) // max_hp
    if fill:
        display.drawFilledRectangle(left + 1, 16, fill, 2, 0)
    draw_text("EN", left, 22, 0)
    draw_text_right(str(en), left + width - 1, 22, 0)


def draw_combat_status(attacker, defender, result=False):
    """Show status before combat and updated HP/EN after the attack."""
    display = thumby.display
    display.fill(1)
    use_font(FONT_SMALL)
    draw_text(attacker["id"], 2, 1, 0)
    draw_text_right(defender["id"], 70, 1, 0)
    draw_text_center("VS", 1, 0)
    display.drawLine(0, 7, 71, 7, 0)
    display.drawLine(35, 8, 35, 31, 0)
    draw_battle_gauges(display, attacker, 2, 31)
    draw_battle_gauges(display, defender, 39, 31)
    display.drawLine(0, 32, 71, 32, 0)
    draw_text(attack_name(attacker), 2, 34, 0)
    if result:
        draw_text_right("-" + str(attack_damage), 70, 34, 0)


def draw_combat_mech(display, unit, x, y, facing=1, pose="idle", weapon=None):
    """Draw a compact articulated mech that leaves room for attack animation."""
    def point(px, py):
        return (x + (px if facing > 0 else 15 - px), y + py)

    forward_hand = (15, 7 if pose == "strike" else 9) if pose in ("strike", "recover") else (12, 7)
    custom_rows = CUSTOM_BATTLE.get(unit["id"])
    if custom_rows:
        draw_custom_mech(display, x, y, custom_rows, facing)
    else:
        # Head, visor, and an antenna give the compact fallback a robot read.
        hx, hy = point(5, 0)
        display.drawRectangle(hx, hy, 5, 4, 0)
        ax, ay = point(7, 0)
        display.drawLine(ax, ay, ax, ay - 2, 0)
        vx, vy = point(8, 2)
        display.drawLine(vx, vy, vx + facing, vy, 0)

        if unit["kind"] == "SUPER":
            tx, ty = point(4, 5)
            display.drawFilledRectangle(min(tx, tx + 7), ty, 8, 6, 0)
            display.drawLine(*point(3, 5), *point(12, 5), 0)
        else:
            display.drawLine(*point(7, 4), *point(7, 11), 0)
            display.drawLine(*point(5, 5), *point(10, 5), 0)

        stride = 2 if pose == "walk" and attack_timer % 2 else -2 if pose == "walk" else 0
        display.drawLine(*point(5, 6), *point(3, 9), 0)
        display.drawLine(*point(10, 6), *point(*forward_hand), 0)
        display.drawLine(*point(6, 11), *point(5 + stride, 15), 0)
        display.drawLine(*point(8, 11), *point(10 - stride, 15), 0)

    if weapon is not None and weapon["style"] not in ("blade", "fist"):
        # A held rifle/cannon stays attached while its shot crosses the panel.
        hand_x, hand_y = point(*forward_hand)
        muzzle_x, muzzle_y = point(16, forward_hand[1])
        display.drawLine(hand_x, hand_y, muzzle_x, muzzle_y, 0)
        display.drawLine(hand_x, hand_y - 1, muzzle_x - facing, muzzle_y - 1, 0)
    elif pose == "strike" and weapon is not None and weapon["style"] == "blade":
        hand_x, hand_y = point(*forward_hand)
        blade_x, blade_y = point(15, 2)
        display.drawLine(hand_x, hand_y, blade_x, blade_y, 0)
    elif pose == "strike" and weapon is not None and weapon["style"] == "fist":
        hand_x, hand_y = point(*forward_hand)
        fist_x, fist_y = point(15, forward_hand[1])
        display.drawLine(hand_x, hand_y, fist_x, fist_y, 0)
        display.drawFilledRectangle(fist_x - 1, fist_y - 1, 2, 2, 0)


def draw_custom_mech(display, x, y, rows, facing):
    """Draw a user-authored 16x16 black-ink sprite from the local editor."""
    for row_index, row in enumerate(rows):
        for column, pixel in enumerate(row):
            if pixel == "#":
                screen_x = column if facing > 0 else 15 - column
                display.setPixel(x + screen_x, y + row_index, 0)


def battle_sprite(unit):
    if unit["team"] == "enemy":
        return ENEMY_BATTLE
    if unit["kind"] == "SHIP":
        return SHIP_BATTLE
    return REAL_BATTLE if unit["kind"] == "REAL" else SUPER_BATTLE


def attack_name(attacker):
    return attack_weapon["name"] if attack_weapon is not None else "COUNTER"


def draw_cut_in(attacker):
    display = thumby.display
    if attacker["kind"] == "SHIP":
        frame = SHIP_CUTIN
    elif attacker["kind"] == "REAL":
        frame = REAL_CUTIN
    else:
        frame = SUPER_CUTIN
    name = attack_name(attacker)
    # Full-screen artwork is prepacked into the Thumby VLSB bitmap format.
    display.blit(frame, 0, 0, 72, 40, -1, 0, 0)
    display.drawFilledRectangle(0, 32, 72, 8, 0)
    display.drawLine(0, 32, 71, 32, 1)
    use_font(FONT_SMALL)
    draw_text(name, 2, 34)
    draw_text_right("B:SKIP", 70, 34)


def start_attack(weapon):
    global attack_is_special, attack_target, attack_damage, attack_weapon
    global attack_phase, attack_timer, state, message
    target = unit_at(units, cursor_x, cursor_y)
    if target is None or target["team"] == "ally":
        message = "NO TARGET"
        return
    if not in_range(selected_unit, target, weapon):
        message = "OUT RANGE"
        return
    attack_target = target
    attack_weapon = weapon
    attack_is_special = weapon.get("finisher", False)
    attack_damage = 0
    # Phase 0 is the pre-battle status card. Finishers add a cut-in in phase 1.
    attack_phase = 0
    attack_timer = 0
    message = "ATTACK"
    state = STATE_ATTACK


def finish_attack():
    global selected_unit, attack_target, selected_weapon, attack_weapon, state
    selected_unit["acted"] = True
    result = mission_result(units, base_hp)
    selected_unit = None
    attack_target = None
    selected_weapon = None
    attack_weapon = None
    if result == "victory":
        state = STATE_VICTORY
    elif result == "defeat":
        state = STATE_DEFEAT
    elif all_allies_acted():
        enemies_turn()
        state = STATE_DEFEAT if mission_result(units, base_hp) == "defeat" else STATE_MAP
    else:
        state = STATE_MAP


def update_attack():
    global attack_phase, attack_timer, attack_damage
    attack_timer += 1
    if attack_phase == 0:
        if attack_timer >= 10:
            attack_phase = 1 if attack_is_special else 2
            attack_timer = 0
    elif attack_phase == 1:
        if attack_timer >= 12:
            attack_phase = 2
            attack_timer = 0
    elif attack_phase == 2:
        if attack_timer >= 8:
            attack_damage = resolve_attack(selected_unit, attack_target,
                                           attack_is_special, attack_weapon)
            attack_phase = 3
            attack_timer = 0
    elif attack_phase == 3 and attack_timer >= 8:
        attack_phase = 4
        attack_timer = 0
    elif attack_phase == 4 and attack_timer >= 12:
        finish_attack()


def draw_attack():
    if attack_phase == 0:
        draw_combat_status(selected_unit, attack_target)
    elif attack_phase == 1:
        draw_cut_in(selected_unit)
    elif attack_phase == 4:
        draw_combat_status(selected_unit, attack_target, result=True)
    else:
        draw_battle_units(selected_unit, attack_target, attack_phase == 3)


def enemies_turn():
    # The first draft keeps enemy logic deterministic and easy to read.
    global base_hp
    for enemy in alive_units(units, "enemy"):
        allies = alive_units(units, "ally")
        if not allies:
            break
        nearest = min(allies, key=lambda ally: abs(ally["x"] - enemy["x"]) + abs(ally["y"] - enemy["y"]))
        if not in_range(enemy, nearest):
            reached = reachable_tiles(enemy, units)
            destinations = [point for point in reached
                            if point != (enemy["x"], enemy["y"])
                            and point != BASE_TILE]
            if destinations:
                destination = min(destinations, key=lambda point: abs(point[0] - BASE_TILE[0]) + abs(point[1] - BASE_TILE[1]))
                enemy["x"], enemy["y"] = destination
        allies = alive_units(units, "ally")
        if not allies:
            break
        nearest = min(allies, key=lambda ally: abs(ally["x"] - enemy["x"]) + abs(ally["y"] - enemy["y"]))
        if in_range(enemy, nearest):
            resolve_attack(enemy, nearest)
            if nearest["kind"] == "SHIP":
                base_hp = nearest["hp"]
        elif (abs(enemy["x"] - BASE_TILE[0]) + abs(enemy["y"] - BASE_TILE[1])
              <= enemy["range"]):
            base_hp = resolve_base_attack(enemy, base_hp)
            ship = next((unit for unit in units if unit["kind"] == "SHIP"), None)
            if ship is not None:
                ship["hp"] = base_hp
    reset_turn(units)


def all_allies_acted():
    return all(unit["acted"] for unit in alive_units(units, "ally"))


def handle_map_input():
    global selected_unit, state, message
    if thumby.buttonU.justPressed():
        move_cursor(0, -1)
    elif thumby.buttonD.justPressed():
        move_cursor(0, 1)
    elif thumby.buttonL.justPressed():
        move_cursor(-1, 0)
    elif thumby.buttonR.justPressed():
        move_cursor(1, 0)
    if thumby.buttonA.justPressed():
        unit = unit_at(units, cursor_x, cursor_y)
        if unit is not None and unit["team"] == "ally" and not unit["acted"]:
            selected_unit = unit
            state = STATE_COMMAND
            message = "COMMAND"
    if thumby.buttonB.justPressed() and selected_unit is not None:
        selected_unit = None
        state = STATE_MAP


def handle_command_input():
    global menu_index, state, message, cursor_x, cursor_y, selected_unit, weapon_index
    global move_tiles, status_page
    if thumby.buttonU.justPressed():
        menu_index = (menu_index - 1) % len(COMMANDS)
    elif thumby.buttonD.justPressed():
        menu_index = (menu_index + 1) % len(COMMANDS)
    elif thumby.buttonB.justPressed():
        selected_unit = None
        state = STATE_MAP
    elif thumby.buttonA.justPressed():
        command = COMMANDS[menu_index]
        if command == "MOVE" and selected_unit["move"] > 0 and not selected_unit["moved"]:
            cursor_x, cursor_y = selected_unit["x"], selected_unit["y"]
            # Computed once; nothing else moves while the player picks a tile.
            move_tiles = reachable_tiles(selected_unit, units)
            state = STATE_MOVE
            message = "A:OK"
        elif command == "ATTACK" and not selected_unit["acted"]:
            weapon_index = 0
            state = STATE_WEAPONS
        elif command == "STATUS":
            status_page = 0
            state = STATE_STATUS
        elif command == "END":
            selected_unit["acted"] = True
            selected_unit = None
            state = STATE_MAP
            if all_allies_acted():
                enemies_turn()
                if mission_result(units, base_hp) == "defeat":
                    state = STATE_DEFEAT


def handle_move_input():
    global state, message, move_tiles
    if thumby.buttonU.justPressed(): move_cursor(0, -1)
    elif thumby.buttonD.justPressed(): move_cursor(0, 1)
    elif thumby.buttonL.justPressed(): move_cursor(-1, 0)
    elif thumby.buttonR.justPressed(): move_cursor(1, 0)
    if thumby.buttonB.justPressed():
        move_tiles = None
        state = STATE_COMMAND
        return
    if thumby.buttonA.justPressed():
        reached = move_tiles or reachable_tiles(selected_unit, units)
        if (cursor_x, cursor_y) in reached and (cursor_x, cursor_y) != (selected_unit["x"], selected_unit["y"]):
            selected_unit["x"], selected_unit["y"] = cursor_x, cursor_y
            selected_unit["moved"] = True
            move_tiles = None
            state = STATE_COMMAND
            message = "MOVED"


def handle_weapon_input():
    global state, weapon_index, selected_weapon, cursor_x, cursor_y, message
    weapons = selected_unit["weapons"]
    if thumby.buttonU.justPressed():
        weapon_index = (weapon_index - 1) % len(weapons)
    elif thumby.buttonD.justPressed():
        weapon_index = (weapon_index + 1) % len(weapons)
    elif thumby.buttonB.justPressed():
        state = STATE_COMMAND
    elif thumby.buttonA.justPressed():
        selected_weapon = weapons[weapon_index]
        cursor_x, cursor_y = selected_unit["x"], selected_unit["y"]
        message = "A:OK"
        move_cursor(1, 0)
        state = STATE_TARGET


def handle_target_input():
    global state, selected_weapon
    if thumby.buttonU.justPressed(): move_cursor(0, -1)
    elif thumby.buttonD.justPressed(): move_cursor(0, 1)
    elif thumby.buttonL.justPressed(): move_cursor(-1, 0)
    elif thumby.buttonR.justPressed(): move_cursor(1, 0)
    if thumby.buttonB.justPressed():
        selected_weapon = None
        state = STATE_COMMAND
    elif thumby.buttonA.justPressed():
        start_attack(selected_weapon)


def update():
    global state, mission_index, cursor_x, cursor_y, base_hp, status_page
    global attack_phase, attack_timer, attack_damage
    if state == STATE_TITLE:
        if thumby.buttonA.justPressed():
            # Holding B while pressing A runs the device benchmark instead.
            if thumby.buttonB.pressed():
                run_benchmark()
                state = STATE_BENCH
            else:
                state = STATE_MAP
    elif state == STATE_BENCH:
        if thumby.buttonA.justPressed() or thumby.buttonB.justPressed():
            state = STATE_TITLE
    elif state == STATE_MAP:
        handle_map_input()
    elif state == STATE_COMMAND:
        handle_command_input()
    elif state == STATE_WEAPONS:
        handle_weapon_input()
    elif state == STATE_STATUS:
        if thumby.buttonL.justPressed() or thumby.buttonR.justPressed():
            status_page = 1 - status_page
        elif thumby.buttonA.justPressed() or thumby.buttonB.justPressed():
            state = STATE_COMMAND
    elif state == STATE_MOVE:
        handle_move_input()
    elif state == STATE_TARGET:
        handle_target_input()
    elif state == STATE_ATTACK:
        if thumby.buttonB.justPressed():
            if attack_phase == 4:
                finish_attack()
            else:
                # Skipping the action still displays its final HP/EN result.
                if attack_damage == 0:
                    attack_damage = resolve_attack(
                        selected_unit, attack_target, attack_is_special,
                        attack_weapon)
                attack_phase = 4
                attack_timer = 0
        else:
            update_attack()
    elif state == STATE_VICTORY and thumby.buttonA.justPressed():
        # Current draft replays the first mission; campaign progression is a later task.
        units[:] = create_units()
        cursor_x, cursor_y = 1, 2
        base_hp = BASE_MAX_HP
        state = STATE_MAP
    elif state == STATE_DEFEAT and thumby.buttonA.justPressed():
        units[:] = create_units()
        cursor_x, cursor_y = 1, 2
        base_hp = BASE_MAX_HP
        state = STATE_MAP


def draw_result_screen(line1, line2, prompt):
    thumby.display.fill(0)
    use_font(FONT_BIG)
    draw_text_center(line1, 6)
    draw_text_center(line2, 15)
    use_font(FONT_SMALL)
    draw_text_center(prompt, 30)


def draw_frame(force=False):
    """Draw the current state into the buffer without showing it."""
    global last_static
    if state in STATIC_STATES:
        if state == last_static and not force:
            return
        last_static = state
    else:
        last_static = None
    if state == STATE_TITLE:
        draw_title()
    elif state == STATE_ATTACK:
        draw_attack()
    elif state == STATE_VICTORY:
        draw_result_screen("MISSION", "CLEAR", "A:REPLAY")
    elif state == STATE_DEFEAT:
        draw_result_screen("MISSION", "FAILED", "A:RETRY")
    elif state == STATE_BENCH:
        draw_bench()
    else:
        draw_map()


def render():
    draw_frame()
    thumby.display.update()


def ticks_us():
    if hasattr(time, "ticks_us"):
        return time.ticks_us()
    return int(time.perf_counter() * 1000000)


def ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def bench_scene(name, setup, frames=12):
    """Average/max draw time in 0.1 ms for one representative scene."""
    total = 0
    worst = 0
    for frame in range(frames):
        setup(frame)
        start = ticks_us()
        draw_frame()
        spent = ticks_diff(ticks_us(), start)
        total += spent
        worst = max(worst, spent)
    return (name, total // frames // 100, worst // 100)


def run_benchmark():
    """Time drawing of the heaviest screens on a fresh M1 board.

    Measures CPU drawing only; the SPI transfer and frame pacing in
    display.update() are timed separately with pacing disabled.
    """
    global state, selected_unit, cursor_x, cursor_y, move_tiles
    global selected_weapon, attack_target, attack_weapon, attack_is_special
    global attack_phase, attack_timer, attack_damage, weapon_index, bench_results
    global menu_index
    gc.collect()
    free_before = gc.mem_free() if hasattr(gc, "mem_free") else -1
    unit = units[1]
    enemy = alive_units(units, "enemy")[0]
    results = []

    def map_idle(frame):
        global state, cursor_x, cursor_y
        state = STATE_MAP
        cursor_x, cursor_y = frame % MAP_WIDTH, frame % MAP_HEIGHT

    def map_move(frame):
        global state, selected_unit, move_tiles, cursor_x, cursor_y
        state = STATE_MOVE
        selected_unit = unit
        move_tiles = reachable_tiles(unit, units)
        cursor_x, cursor_y = unit["x"], unit["y"]

    def menu(frame):
        global state, selected_unit, menu_index
        state = STATE_COMMAND
        selected_unit = unit
        menu_index = frame % len(COMMANDS)

    def battle(frame):
        global state, selected_unit, attack_target, attack_weapon
        global attack_is_special, attack_phase, attack_timer, attack_damage
        state = STATE_ATTACK
        selected_unit = unit
        attack_target = enemy
        attack_weapon = unit["weapons"][frame % 2]
        attack_is_special = False
        attack_phase = 2 + (frame // 8) % 2
        attack_timer = frame % 8
        attack_damage = 10

    def cut_in(frame):
        global state, attack_phase, attack_weapon
        battle(frame)
        attack_weapon = unit["weapons"][-1]
        attack_phase = 1

    results.append(bench_scene("MAP", map_idle))
    results.append(bench_scene("MOVE", map_move))
    results.append(bench_scene("MENU", menu))
    results.append(bench_scene("FIGHT", battle, 16))
    results.append(bench_scene("CUTIN", cut_in))
    # Push one frame with pacing off to time the display transfer itself.
    try:
        thumby.display.setFPS(0)
        start = ticks_us()
        thumby.display.update()
        show = ticks_diff(ticks_us(), start) // 100
    finally:
        thumby.display.setFPS(FPS)
    gc.collect()
    free_after = gc.mem_free() if hasattr(gc, "mem_free") else -1
    selected_unit = None
    move_tiles = None
    attack_target = None
    attack_weapon = None
    bench_results = (results, show, free_before, free_after)


def fmt_ms(tenths):
    return str(tenths // 10) + "." + str(tenths % 10)


def draw_bench():
    thumby.display.fill(0)
    use_font(FONT_SMALL)
    results, show, free_before, free_after = bench_results
    draw_text("DRAW MS AVG/MAX", 0, 0)
    for index, (name, average, worst) in enumerate(results):
        y = 6 + index * 6
        draw_text(name, 0, y)
        draw_text_right(fmt_ms(average) + "/" + fmt_ms(worst), 71, y)
    draw_text("SHOW " + fmt_ms(show), 0, 35)
    free_k = str(free_after // 1024) + "K" if free_after >= 0 else "?"
    draw_text_right("FREE " + free_k, 71, 35)


def main():
    gc.collect()
    while True:
        update()
        render()


# The Thumby launcher may import the game instead of running it as
# __main__, so also start on MicroPython (same pattern as ThumbyBrawlBase).
if __name__ == "__main__" or sys.implementation.name == "micropython":
    main()
