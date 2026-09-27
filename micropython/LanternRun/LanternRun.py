"""Original monochrome Thumby game. Install in /Games/LanternRun/."""
import gc
import sys

import thumby

GAME_PATH = "/Games/LanternRun"
if GAME_PATH not in sys.path:
    sys.path.insert(0, GAME_PATH)

from lantern_core import Game, LEFT, RIGHT, UP, DOWN, ATTACK, DODGE, PLAY, WON


def read_buttons():
    keys = 0
    if thumby.buttonL.pressed():
        keys |= LEFT
    if thumby.buttonR.pressed():
        keys |= RIGHT
    if thumby.buttonU.pressed():
        keys |= UP
    if thumby.buttonD.pressed():
        keys |= DOWN
    if thumby.buttonA.pressed():
        keys |= ATTACK
    if thumby.buttonB.pressed():
        keys |= DODGE
    return keys


def draw_actor(display, actor, camera, game):
    if actor.hp <= 0:
        return
    x, y = actor.x - camera, actor.y
    if x < -14 or x > 85:
        return
    player = actor is game.player
    display.drawLine(x - 3, y, x + 3, y, 1)  # Ground shadow / lane reference.
    if player and game.invulnerable and game.frame % 2:
        return
    if actor.flash and game.frame % 2:
        return
    # Original geometric figures: courier's white headband and parcel,
    # hollow-headed raiders, and a broad, double-belted heavy.
    display.drawFilledRectangle(x - 3, y - 11, 7, 11, 0)
    display.drawRectangle(x - 2, y - 11, 5, 4, 1)
    if player:
        display.drawLine(x - 3, y - 10, x + 3, y - 10, 1)
        display.drawFilledRectangle(x - actor.facing * 3 - 1, y - 7, 3, 4, 1)
    display.setPixel(x + actor.facing, y - 9, 1)
    display.drawLine(x, y - 7, x, y - 3, 1)
    width = 3 if actor.kind == 1 else 2
    display.drawLine(x - width, y - 6, x + width, y - 6, 1)
    if actor.kind == 1:
        display.drawLine(x - 3, y - 5, x + 3, y - 5, 1)
    stride = 1 + (game.frame // 4) % 2
    if player and game.dodge:
        stride = 3
        display.drawLine(x - actor.facing * 7, y - 4,
                         x - actor.facing * 4, y - 4, 1)
    display.drawLine(x, y - 3, x - stride, y - 1, 1)
    display.drawLine(x, y - 3, x + stride, y - 1, 1)
    if player and game.attack:
        reach = 15 if game.combo == 3 else 12
        display.drawLine(x, y - 6, x + actor.facing * reach, y - 6, 1)
        display.drawLine(x + actor.facing * reach, y - 7,
                         x + actor.facing * reach, y - 5, 1)
    if actor.wind:
        # Beside the head so the HUD never hides the warning in the top lane.
        display.drawLine(x + 5, y - 13, x + 5, y - 11, 1)
        display.setPixel(x + 5, y - 9, 1)
        display.drawLine(x, y - 5, x + actor.facing * 5, y - 7, 1)


def draw_game(display, game, order):
    display.fill(0)
    camera = game.camera()
    # Procedural scrolling fence and lanterns, no external art assets.
    display.drawLine(0, 18, 71, 18, 1)
    for world_x in range(game.room * 112, (game.room + 1) * 112, 16):
        x = world_x - camera
        if 0 <= x <= 71:
            display.drawLine(x, 13, x, 18, 1)
            if world_x % 32 == 0:
                display.drawRectangle(x - 2, 10, 5, 5, 1)
    display.drawLine(0, 39, 71, 39, 1)
    # In-place insertion sort: four persistent references, feet decide depth.
    for i in range(1, 4):
        actor = order[i]
        j = i - 1
        while j >= 0 and order[j].y > actor.y:
            order[j + 1] = order[j]
            j -= 1
        order[j + 1] = actor
    for actor in order:
        draw_actor(display, actor, camera, game)
    display.drawFilledRectangle(0, 0, 72, 8, 0)
    display.drawRectangle(0, 1, 22, 5, 1)
    display.drawFilledRectangle(1, 2, game.player.hp * 2, 3, 1)
    display.drawText(str(game.room + 1) + "/3", 26, 0, 1)
    if game.remaining():
        display.drawText("E" + str(game.remaining()), 50, 0, 1)
    else:
        display.drawText("GO>", 50, 0, 1)
    # Small recharge meter under health; full width means dodge is ready.
    display.drawLine(0, 7, (26 - game.dodge_cooldown) * 21 // 26, 7, 1)


def main():
    display = thumby.display
    display.setFPS(30)
    display.setFont("/lib/font5x7.bin", 5, 7, 1)
    game = Game()
    order = [game.player, game.enemies[0], game.enemies[1], game.enemies[2]]
    menu = True
    paused = False
    previous = 0
    chord = 0
    chord_used = False
    gc.collect()
    while True:
        keys = read_buttons()
        edge = keys & ~previous
        previous = keys
        if menu:
            display.fill(0)
            display.drawText("LANTERN RUN", 3, 0, 1)
            display.drawText("A:HIT B:ROLL", 0, 9, 1)
            display.drawText("DPAD:MOVE", 9, 19, 1)
            display.drawText("A:GO B:EXIT", 3, 30, 1)
            if edge & DODGE:
                thumby.reset()
                return
            if edge & ATTACK:
                game.reset()
                game.previous = keys
                menu = False
                gc.collect()
        elif game.state != PLAY:
            display.fill(0)
            display.drawText("DELIVERED!" if game.state == WON else "TRY AGAIN!", 6, 2, 1)
            display.drawText("FOES " + str(game.kills) + "/8", 12, 12, 1)
            display.drawText("A:RETRY", 15, 23, 1)
            display.drawText("B:TITLE", 15, 32, 1)
            if edge & ATTACK:
                game.reset()
                game.previous = keys
                gc.collect()
            elif edge & DODGE:
                menu = True
        else:
            if keys & (ATTACK | DODGE) == (ATTACK | DODGE):
                chord = min(18, chord + 1)
                if chord == 18 and not chord_used:
                    paused = not paused
                    chord_used = True
                    thumby.audio.stop()
            else:
                chord = 0
                chord_used = False
            if paused:
                display.fill(0)
                display.drawText("PAUSED", 18, 2, 1)
                display.drawText("A+B:RESUME", 6, 14, 1)
                display.drawText("DOWN:TITLE", 6, 26, 1)
                if edge & DOWN:
                    menu = True
                    paused = False
            else:
                old_room = game.room
                # Reserve a two-button chord for pause; no accidental attacks.
                game.step(keys & ~(ATTACK | DODGE) if chord else keys)
                if old_room != game.room:
                    gc.collect()
                if game.sound:
                    frequency = (0, 330, 880, 140, 1200)[game.sound]
                    thumby.audio.play(frequency, 45)
                draw_game(display, game, order)
        display.update()


if __name__ == "__main__":
    main()
