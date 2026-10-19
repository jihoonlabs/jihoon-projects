"""Playable first-pass tactical SRPG for the standard monochrome Thumby."""

import gc
import thumby

from assets import (ENEMY_BATTLE, ENEMY_ICON, REAL_BATTLE, REAL_CUTIN,
                    REAL_ICON, SHIP_BATTLE, SHIP_CUTIN, SHIP_ICON,
                    SUPER_BATTLE, SUPER_CUTIN, SUPER_ICON)
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

thumby.display.setFPS(20)


def draw_text(text, x, y, color=1):
    thumby.display.drawText(text, x, y, color)


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


def draw_weapon_menu():
    display = thumby.display
    display.fill(0)
    draw_text(selected_unit["id"] + " WEAPON", 1, 0)
    weapons = selected_unit["weapons"]
    for index, weapon in enumerate(weapons):
        y = 6 + index * 5
        line = weapon["short"] + " " + str(weapon["power"]) + " R" + str(weapon["range"])
        if index == weapon_index:
            display.drawFilledRectangle(0, y - 1, 72, 6, 1)
            draw_text(line, 2, y, 0)
        else:
            draw_text(line, 2, y, 1)
    draw_text("A:OK B:BACK", 1, 34)


def draw_status_screen(unit):
    display = thumby.display
    display.fill(0)
    draw_text(unit["id"] + " " + unit["kind"], 1, 0)
    draw_text("HP " + str(unit["hp"]) + "/" + str(unit["max_hp"]), 1, 7)
    draw_text("EN " + str(unit["en"]) + "/" + str(unit["max_en"]), 1, 13)
    draw_text("ARM " + str(unit["armor"]), 1, 19)
    draw_text("MOB " + str(unit["mobility"]), 1, 25)
    draw_text("MOVE " + str(unit["move"]), 1, 31)
    draw_text("B:BK", 48, 31)


def draw_map():
    display = thumby.display
    display.fill(0)
    update_camera()
    movement_tiles = (reachable_tiles(selected_unit, units)
                      if selected_unit is not None and state == STATE_MOVE else ())
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
            unit = unit_at(units, wx, wy)
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
    if state == STATE_WEAPONS:
        draw_weapon_menu()
        return
    if state == STATE_STATUS:
        draw_status_screen(selected_unit)
        return
    if state == STATE_COMMAND:
        # The command/status overlay is contextual and appears only after A.
        overlay_x = 42
        display.drawFilledRectangle(overlay_x, 0, SCREEN_W - overlay_x, SCREEN_H, 0)
        display.drawRectangle(overlay_x, 0, SCREEN_W - overlay_x, SCREEN_H, 1)
        draw_text(selected_unit["id"], overlay_x + 3, 1)
        draw_text("H" + str(selected_unit["hp"]), overlay_x + 14, 1)
        hp_width = max(0, min(25, selected_unit["hp"] * 25 // selected_unit["max_hp"]))
        display.drawRectangle(overlay_x + 2, 7, 25, 4, 1)
        if hp_width:
            display.drawFilledRectangle(overlay_x + 3, 8, hp_width, 2, 1)
        for index, command in enumerate(COMMANDS):
            y = 9 + index * 7
            label = COMMAND_LABELS[index]
            if command == "MOVE" and (selected_unit["moved"] or selected_unit["move"] == 0):
                label = "MOV-"
            if command == "ATTACK" and selected_unit["acted"]:
                label = "ATK-"
            if index == menu_index:
                display.drawFilledRectangle(overlay_x + 1, y - 1, 28, 7, 1)
                draw_text(label, overlay_x + 3, y, 0)
            else:
                draw_text(label, overlay_x + 2, y, 1)
    elif state in (STATE_MOVE, STATE_TARGET):
        draw_text("MOVE" if state == STATE_MOVE else "TARGET", 1, 1)
        draw_text(message[:4], 1, 8)
        draw_text("A:OK B:BK", 1, 34)


def draw_title():
    display = thumby.display
    draw_hangar_background()
    display.drawRectangle(3, 4, 66, 31, 1)
    draw_text("SRPG-V1", 16, 9)
    draw_text("MONO TACTICS", 8, 18)
    draw_text("A:START", 20, 29)


def draw_battle_units(attacker, defender, impact=False):
    display = thumby.display
    draw_hangar_background()
    display.drawLine(0, 0, 71, 0, 1)
    draw_text(attacker["id"] + " " + str(attacker["hp"]), 1, 1)
    draw_text(defender["id"], 61, 1)
    display.drawRectangle(1, 8, 28, 4, 1)
    display.drawRectangle(43, 8, 28, 4, 1)
    display.drawFilledRectangle(2, 9, max(0, attacker["hp"] * 26 // attacker["max_hp"]), 2, 1)
    display.drawFilledRectangle(44, 9, max(0, defender["hp"] * 26 // defender["max_hp"]), 2, 1)
    attacker_sprite = battle_sprite(attacker)
    defender_sprite = battle_sprite(defender)
    draw_bitmap(display, 7, 14, attacker_sprite)
    draw_bitmap(display, 51, 14, defender_sprite, mirror=True)
    if attack_weapon is not None and attack_weapon["style"] != "blade":
        # A small outlined cannon stays attached during a ranged shot.
        display.drawFilledRectangle(19, 19, 8, 3, 1)
        display.drawLine(21, 20, 26, 20, 0)
    else:
        # A short blade silhouette also reads as a heavy melee swing at this scale.
        display.drawLine(19, 23, 26, 16, 1)
        display.drawLine(20, 24, 27, 17, 1)
        display.drawLine(20, 23, 23, 25, 1)
    if impact:
        for x, y in ((45, 19), (48, 17), (49, 21), (47, 24), (52, 18), (52, 23)):
            display.setPixel(x, y, 1)
        draw_text("-" + str(attack_damage), 46, 31)
    elif attack_weapon is not None and attack_weapon["style"] == "blade":
        slash_x = min(48, 26 + attack_timer * 2)
        slash_y = max(13, 27 - attack_timer * 2)
        display.drawLine(24, 27, slash_x, slash_y, 1)
        display.drawLine(25, 28, slash_x + 1, slash_y + 1, 1)
    elif attacker["kind"] in ("REAL", "SHIP") or attack_weapon is not None:
        # The miniature stays in place while its shot travels across the screen.
        shot_x = min(47, 28 + attack_timer * 2)
        if attack_weapon is not None and attack_weapon["style"] == "beam":
            display.drawLine(27, 20, shot_x, 20, 1)
            display.drawLine(27, 22, shot_x, 22, 1)
        else:
            display.drawLine(max(27, shot_x - 4), 21, shot_x, 21, 1)
            display.drawFilledRectangle(shot_x, 20, 2, 2, 1)
    else:
        # Super units swing a traveling slash; they never need to walk beside a target.
        slash_x = min(48, 26 + attack_timer * 2)
        slash_y = max(13, 27 - attack_timer * 2)
        display.drawLine(24, 27, slash_x, slash_y, 1)
        display.drawLine(25, 28, slash_x + 1, slash_y + 1, 1)
        if attack_is_special:
            display.drawLine(27, 28, slash_x + 2, slash_y, 1)
    display.drawLine(0, 31, 71, 31, 1)
    draw_text(attack_name(attacker), 4, 33)


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
    draw_text(name, 3, 34)
    draw_text("B", 67, 34)


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
        if attack_timer >= 12:
            attack_phase = 1
            attack_timer = 0
    elif attack_phase == 1:
        if attack_timer >= 8:
            attack_damage = resolve_attack(selected_unit, attack_target,
                                           attack_is_special, attack_weapon)
            attack_phase = 2
            attack_timer = 0
    elif attack_phase == 2 and attack_timer >= 20:
        finish_attack()


def draw_attack():
    if attack_phase == 0:
        draw_cut_in(selected_unit)
    else:
        draw_battle_units(selected_unit, attack_target, attack_phase == 2)


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
            state = STATE_MOVE
            message = "RANGE " + str(selected_unit["move"])
        elif command == "ATTACK" and not selected_unit["acted"]:
            weapon_index = 0
            state = STATE_WEAPONS
        elif command == "STATUS":
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
    global state, message
    if thumby.buttonU.justPressed(): move_cursor(0, -1)
    elif thumby.buttonD.justPressed(): move_cursor(0, 1)
    elif thumby.buttonL.justPressed(): move_cursor(-1, 0)
    elif thumby.buttonR.justPressed(): move_cursor(1, 0)
    if thumby.buttonB.justPressed():
        state = STATE_COMMAND
        return
    if thumby.buttonA.justPressed():
        reached = reachable_tiles(selected_unit, units)
        if (cursor_x, cursor_y) in reached and (cursor_x, cursor_y) != (selected_unit["x"], selected_unit["y"]):
            selected_unit["x"], selected_unit["y"] = cursor_x, cursor_y
            selected_unit["moved"] = True
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
        message = selected_weapon["short"]
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
    global state, mission_index, cursor_x, cursor_y, base_hp
    if state == STATE_TITLE:
        if thumby.buttonA.justPressed():
            state = STATE_MAP
    elif state == STATE_MAP:
        handle_map_input()
    elif state == STATE_COMMAND:
        handle_command_input()
    elif state == STATE_WEAPONS:
        handle_weapon_input()
    elif state == STATE_STATUS:
        if thumby.buttonA.justPressed() or thumby.buttonB.justPressed():
            state = STATE_COMMAND
    elif state == STATE_MOVE:
        handle_move_input()
    elif state == STATE_TARGET:
        handle_target_input()
    elif state == STATE_ATTACK:
        if thumby.buttonB.justPressed():
            # Skip remains deterministic: apply damage once if impact has not happened.
            if attack_damage == 0:
                resolve_attack(selected_unit, attack_target, attack_is_special,
                               attack_weapon)
            finish_attack()
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


def render():
    if state == STATE_TITLE:
        draw_title()
    elif state in (STATE_ATTACK,):
        draw_attack()
    elif state == STATE_VICTORY:
        thumby.display.fill(0)
        draw_text("MISSION CLEAR", 2, 8)
        draw_text("A:REPLAY", 11, 22)
    elif state == STATE_DEFEAT:
        thumby.display.fill(0)
        draw_text("MISSION FAILED", 1, 8)
        draw_text("A:RETRY", 17, 22)
    else:
        draw_map()
    thumby.display.update()


def main():
    gc.collect()
    while True:
        update()
        render()


if __name__ == "__main__":
    main()
