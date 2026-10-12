import sys
import time
try:
    import ujson as json
except ImportError:
    import json
import thumby
from rules import update_state, encode_save_data, decode_save_data


def main_loop():
    thumby.display.setFPS(30)
    state = load_save_data()
    while True:
        state = step_frame(state)


def step_frame(state):
    inputs = handle_inputs()
    new_state = update_state(state, inputs)
    if new_state['save_requested']:
        new_state['save_status'] = save_game(new_state)
        new_state['save_requested'] = False
    elif new_state['screen_state'] != state['screen_state']:
        new_state['save_status'] = ''
    else:
        new_state['save_status'] = state['save_status']
    draw_game(new_state)
    return new_state


def draw_game(state):
    display = thumby.display
    display.fill(0)
    screen = state['screen_state']
    status = state['save_status']
    if screen == 'battle':
        display.drawText('HP:'+str(state['HP']), 0, 0, 1)
        money = state['money']
        shown = str(money) if money < 1000 else str(min(999, money//1000))+'k'
        display.drawText('$'+shown, 72-6*(len(shown)+1), 0, 1)
        camera = max(0, min(72, state['player_x']-32))
        positions = [state['player_x']]
        if state['active_enemy']:
            positions.append(state['enemy_x'])
        for world_x in positions:
            x = world_x-camera
            left = max(0, x)
            right = min(72, x+8)
            if right > left:
                display.drawFilledRectangle(left, 32, right-left, 8, 1)
    elif screen in ('shop_detail', 'equip_detail'):
        item = state['menu_selection']
        names = ('Blade', 'Sword', 'Vest', 'Armor')
        prices = (40, 80, 40, 80)
        display.drawText(names[item], 0, 0, 1)
        display.drawText('P:'+str(prices[item]), 0, 8, 1)
        money = str(state['money'])
        display.drawText(money[:12], 0, 16, 1)
        if len(money) > 12:
            display.drawText(money[12:], 0, 24, 1)
        owned = 'Y' if state['owned'][item] else 'N'
        equipped = item in (state['equipped_weapon'], state['equipped_armor'])
        display.drawText('O:'+owned+' E:'+('Y' if equipped else 'N'), 0, 32, 1)
    elif screen == 'defeat':
        display.drawText('DEFEAT', 0, 0, 1)
        display.drawText('A:RETRY', 0, 20, 1)
    else:
        if screen == 'safe':
            choices = ('NEXT', 'SHOP', 'EQUIP', 'SAVE')
        elif screen == 'pause':
            choices = ('RESUME', 'SAVE')
        else:
            choices = ('Blade', 'Sword', 'Vest', 'Armor')
        display.drawText(status if status in ('SAVED','SAVE ERR') else screen.upper(), 0, 0, 1)
        start = state['menu_scroll']
        for row in range(3):
            index = start+row
            if index < len(choices):
                selected = '>' if index == state['menu_selection'] else ' '
                display.drawText(selected+choices[index], 0, 10+row*10, 1)
    if status in ('SAVED', 'SAVE ERR') and screen in ('battle','shop_detail','equip_detail','defeat'):
        display.drawText(status, 0, 0, 1)
    display.update()


def handle_inputs():
    return {
        'L': bool(thumby.buttonL.pressed()),
        'R': bool(thumby.buttonR.pressed()),
        'A': bool(thumby.buttonA.justPressed()),
        'B': bool(thumby.buttonB.justPressed()),
        'U': bool(thumby.buttonU.justPressed()),
        'D': bool(thumby.buttonD.justPressed()),
    }


def load_save_data():
    initial = {
        'version': 1, 'money': 0, 'progress': 0, 'owned': [False]*4,
        'equipped_weapon': None, 'equipped_armor': None,
    }
    try:
        thumby.saveData.setName('ThumbyGrowth')
        if not thumby.saveData.hasItem('state'):
            return decode_save_data(initial)
        raw = thumby.saveData.getItem('state')
        restored = decode_save_data(json.loads(raw))
        if restored is not None:
            return restored
    except Exception:
        pass
    thumby.display.fill(0)
    thumby.display.drawText('LOAD ERR', 0, 0, 1)
    thumby.display.update()
    if sys.implementation.name == 'micropython':
        time.sleep(1)
    return decode_save_data(initial)


def save_game(state):
    try:
        data = json.dumps(encode_save_data(state))
        thumby.saveData.setName('ThumbyGrowth')
        thumby.saveData.setItem('state', data)
        thumby.saveData.save()
        return 'SAVED'
    except Exception:
        return 'SAVE ERR'


if sys.implementation.name == 'micropython':
    main_loop()
