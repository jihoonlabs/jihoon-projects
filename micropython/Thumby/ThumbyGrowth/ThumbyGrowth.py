import sys
import time
try:
    import ujson as json
except ImportError:
    import json
import thumby
# The device launcher need not add the game's sibling-module directory.
if sys.implementation.name == 'micropython':
    sys.path.append('/Games/ThumbyGrowth')
from rules import update_state, encode_save_data, decode_save_data, GOAL_STAGES, ENCOUNTERS


def main_loop():
    thumby.display.setFPS(30)
    action = None
    while action is None:
        action = title_frame()
    state = (load_save_data() if action == 'load' else
             decode_save_data(dict(version=1, money=0, progress=0,
                 owned=[False]*4, equipped_weapon=None, equipped_armor=None)))
    while True:
        state = step_frame(state)


def title_frame():
    display = thumby.display
    display.fill(0)
    display.drawText('GROWTH', 18, 2, 1)
    display.drawText('5 DUELS', 15, 12, 1)
    display.drawText('A:NEW', 0, 23, 1)
    display.drawText('B:LOAD', 0, 33, 1)
    display.update()
    # Loading takes priority if both buttons are pressed; it cannot erase a save.
    if thumby.buttonB.justPressed():
        return 'load'
    if thumby.buttonA.justPressed():
        return 'new'
    return None


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
    if screen == 'safe' and state['progress'] >= GOAL_STAGES:
        display.drawText('QUEST CLEAR', 3, 0, 1)
        display.drawText('$'+str(state['money']), 0, 10, 1)
        display.drawText('A:NEW', 0, 20, 1)
        display.drawText(status if status in ('SAVED','SAVE ERR') else 'B:SAVE', 0, 30, 1)
    elif screen == 'battle':
        display.drawText('HP'+str(state['HP']), 0, 0, 1)
        display.drawText(str(state['progress']+1)+'/5', 24, 0, 1)
        display.drawText('E'+str(state['enemy_hp']), 48, 0, 1)
        for x, hp, maximum in ((0, state['HP'], state['maxHP']),
                                (42, state['enemy_hp'], ENCOUNTERS[min(state['progress'],GOAL_STAGES-1)][0])):
            display.drawFilledRectangle(x, 9, 30, 4, 1)
            display.drawFilledRectangle(x+1, 10, 28, 2, 0)
            width = max(0, min(28, 28*hp//max(1,maximum)))
            if width:
                display.drawFilledRectangle(x+1, 10, width, 2, 1)
        camera = max(0, min(72, state['player_x']-32))
        actors = [(True, state['player_x'], state.get('player_y',28))]
        if state['active_enemy']:
            actors.append((False, state['enemy_x'], state.get('enemy_y',28)))
        actors.sort(key=lambda actor: actor[2])
        for player, world_x, y in actors:
            x = world_x-camera
            rightward = state['direction']=='R' if player else world_x<state['player_x']
            flashing = player and state['enemy_attack_cooldown']>=115 and state['combat_frame']%2==0
            rows = (12,30,26,12,31,18,33) if player else (30,18,30,12,63,18,33)
            if player and (state['combat_frame']//5)%2:
                rows = rows[:5]+(12,18)
            if not flashing:
                for row, mask in enumerate(rows):
                    for column in range(6):
                        bit = 5-column if rightward else column
                        if mask & (1<<bit) and 0<=x+column<72:
                            display.drawFilledRectangle(x+column, y+row, 1, 1, 1)
            if player and not flashing and state['player_attack_cooldown']>=11:
                length = 2 if state['equipped_weapon'] is None else (6 if state['equipped_weapon']==0 else 8)
                front = x+6 if rightward else x-length
                left, right = max(0,front), min(72,front+length)
                if right>left:
                    display.drawFilledRectangle(left,y+3,right-left,1,1)
    elif screen in ('shop_detail', 'equip_detail'):
        item = state['menu_selection']
        names = ('Blade', 'Sword', 'Vest', 'Armor')
        prices = (40, 80, 40, 80)
        display.drawText(names[item], 0, 0, 1)
        display.drawText('P:'+str(prices[item]), 0, 8, 1)
        effect = ('ATK+2','ATK+4','DEF+1','DEF+2')[item]
        display.drawText(effect, 36, 8, 1)
        money = str(state['money'])
        display.drawText(money[:12], 0, 16, 1)
        if len(money) > 12:
            display.drawText(money[12:], 0, 24, 1)
        owned = 'Y' if state['owned'][item] else 'N'
        equipped = item in (state['equipped_weapon'], state['equipped_armor'])
        if len(money) <= 12:
            if screen == 'shop_detail':
                action = 'OWNED' if state['owned'][item] else ('A:BUY' if state['money']>=prices[item] else 'NO MONEY')
            else:
                action = 'BUY FIRST' if not state['owned'][item] else ('A:REMOVE' if equipped else 'A:EQUIP')
            display.drawText(action, 0, 24, 1)
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
        header = 'STAGE '+str(state['progress']+1) if screen == 'safe' else screen.upper()
        if screen in ('shop','equip'):
            chosen = state['menu_selection']
            if screen == 'shop':
                header = 'BOUGHT' if state['owned'][chosen] else ('A:BUY' if state['money'] >= (40,80,40,80)[chosen] else 'NO MONEY')
            else:
                on = chosen in (state['equipped_weapon'],state['equipped_armor'])
                header = 'BUY FIRST' if not state['owned'][chosen] else ('ON ATK'+str(state['attack']) if on and chosen<2 else ('ON DEF'+str(state['defense']) if on else 'A:EQUIP'))
        if screen in ('shop','equip'):
            header = 'AT'+str(state['attack'])+' DF'+str(state['defense'])
        if status in ('SAVED','SAVE ERR'):
            header = status
        display.drawText(header, 0, 0, 1)
        cash = str(state['money']) if state['money']<1000 else str(min(999,state['money']//1000))+'k'
        if len(header)+len(cash)+1 <= 12:
            display.drawText('$'+cash, 72-6*(len(cash)+1), 0, 1)
        start = state['menu_scroll']
        for row in range(3):
            index = start+row
            if index < len(choices):
                active = index == state['menu_selection']
                ink = 0 if active else 1
                if active:
                    display.drawFilledRectangle(0,10+row*10,72,8,1)
                selected = '>' if active else ' '
                label = selected+choices[index]
                if screen in ('shop','equip') and state['owned'][index]:
                    label += '+'
                display.drawText(label, 0, 10+row*10, ink)
                if screen == 'shop':
                    display.drawText(str((40,80,40,80)[index]), 54, 10+row*10, ink)
                elif screen == 'equip':
                    on = index in (state['equipped_weapon'],state['equipped_armor'])
                    display.drawText('ON' if on else ('OK' if state['owned'][index] else '--'), 54, 10+row*10, ink)
    if status in ('SAVED', 'SAVE ERR') and screen in ('shop_detail','equip_detail','defeat'):
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
        'U_held': bool(thumby.buttonU.pressed()),
        'D_held': bool(thumby.buttonD.pressed()),
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
