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
from rules import (update_state, encode_save_data, decode_save_data,
                   GOAL_STAGES, ENCOUNTERS, REGIONS, STAGES_PER_REGION,
                   CITY_NAMES, stage_index, new_game_state)

# Original 6x7 silhouettes: headband/robe, hood, then three boss helmets.
# Visuals stay inside the existing collision body; no source-game assets used.
HERO_ROWS = b'\x0e\x3e\x0a\x1c\x3e\x14\x36'
FOE_ROWS = b'\x1e\x12\x1e\x1e\x12\x14\x36'
BOSS_ROWS = (
    b'\x15\x3f\x12\x3f\x1e\x14\x36',
    b'\x3f\x2d\x12\x1e\x3f\x14\x36',
    b'\x21\x3f\x12\x33\x1e\x14\x36',
)
HEART_ROWS = b'\x0a\x1f\x1f\x0e\x04'
ENEMY_ICON_ROWS = b'\x0e\x1f\x15\x0e\x0a'


def draw_rows(display, rows, x, y, width, mirror=False):
    # Draw contiguous lit pixels in one call; keep the same monochrome bitmap.
    for row,mask in enumerate(rows):
        column = 0
        while column < width:
            if not mask & (1 << (column if mirror else width-1-column)):
                column += 1
                continue
            start = column
            while column < width and mask & (1 << (column if mirror else width-1-column)):
                column += 1
            left,right = max(0,x+start),min(72,x+column)
            if right>left and 0<=y+row<40:
                display.drawFilledRectangle(left,y+row,right-left,1,1)


def character_rows(state, player):
    if player:
        rows = HERO_ROWS
    elif state['progress']%STAGES_PER_REGION == STAGES_PER_REGION-1:
        rows = BOSS_ROWS[stage_index(state)//STAGES_PER_REGION]
    else:
        rows = FOE_ROWS
    if (state['combat_frame']//5)%2:
        return rows[:5]+b'\x0c\x12'
    return rows


# Original monochrome scenery, stored once. These are decoration, not obstacles.
# x, y, width, height in the distant layer; battle HUD ends at y=13.
SCENERY = (
    # KR1: tiled-roof village street.
    ((2,21,27,1),(6,20,19,1),(10,19,11,1),(15,18,2,1),
     (7,22,2,8),(24,22,2,8),(50,20,29,1),(55,19,19,1),
     (60,18,9,1),(63,17,3,1),(56,21,2,8),(72,21,2,8)),
    # KR2: bamboo mountain pass.
    ((8,14,1,15),(6,18,5,1),(7,23,4,1),(16,15,1,13),(14,19,5,1),
     (35,14,1,16),(33,20,5,1),(40,16,1,13),(38,22,5,1),
     (67,14,1,14),(65,17,5,1),(76,16,1,14),(74,23,5,1)),
    # KR3: mountain fortress stones.
    ((0,24,96,1),(0,30,96,1),(2,25,1,5),(18,25,1,5),(34,25,1,5),
     (50,25,1,5),(66,25,1,5),(82,25,1,5),(9,22,5,2),(30,22,5,2),
     (53,22,5,2),(74,22,5,2)),
    # KR4: temple yard, broad eaves and bell frame.
    ((5,19,32,1),(10,18,22,1),(14,17,14,1),(20,16,2,1),
     (10,20,2,9),(30,20,2,9),(52,16,20,2),(54,18,2,13),
     (68,18,2,13),(60,18,3,2),(58,20,7,4),(57,24,9,1)),
    # KR5: fortress gate with raised pavilion.
    ((23,18,34,2),(28,17,24,1),(33,16,14,1),(38,15,4,1),
     (27,20,3,11),(50,20,3,11),(30,24,20,1),(35,25,1,6),(44,25,1,6),
     (0,28,23,2),(57,28,39,2),(7,26,4,2),(72,26,4,2)),
    # CN1: brick city avenue.
    ((0,22,96,1),(0,28,96,1),(0,32,96,1),(6,23,1,5),(24,23,1,5),
     (42,23,1,5),(60,23,1,5),(78,23,1,5),(15,20,5,2),(48,20,5,2),
     (18,29,1,3),(54,29,1,3),(84,20,5,2)),
    # CN2: river landing, boat mast and bridge rail.
    ((1,30,28,1),(7,28,17,2),(16,16,1,12),(17,18,8,1),(17,19,7,5),
     (44,22,45,1),(48,23,2,8),(69,23,2,8),(85,23,2,8),
     (45,18,1,4),(59,18,1,4),(73,18,1,4),(45,18,29,1)),
    # CN3: dense bamboo grove, but open combat lanes.
    ((1,14,1,14),(10,16,1,15),(23,14,1,17),(29,18,1,12),
     (46,14,1,15),(57,15,1,15),(70,14,1,17),(85,16,1,14),
     (0,19,4,1),(8,22,5,1),(21,18,5,1),(44,21,5,1),(68,19,5,1)),
    # CN4: layered pagoda silhouettes.
    ((6,18,25,1),(10,16,17,1),(15,14,7,1),(11,19,15,1),(8,22,21,1),
     (12,23,13,1),(10,26,17,1),(13,27,2,5),(23,27,2,5),
     (56,17,25,1),(60,15,17,1),(64,14,9,1),(59,21,19,1),
     (61,25,15,1),(63,26,2,5),(74,26,2,5)),
    # CN5: stone courtyard gate and pillars.
    ((24,15,32,2),(20,17,40,1),(25,18,3,13),(52,18,3,13),
     (30,19,20,1),(32,20,1,10),(47,20,1,10),
     (7,16,3,15),(5,14,7,2),(74,16,3,15),(72,14,7,2)),
    # JP1: mountain hamlet with steep roofs.
    ((3,23,25,1),(7,21,17,1),(11,19,9,1),(14,17,3,1),
     (7,24,2,8),(23,24,2,8),(49,22,29,1),(54,20,19,1),
     (60,18,7,1),(62,16,3,1),(55,23,2,8),(72,23,2,8)),
    # JP2: pine ridge.
    ((13,17,1,14),(10,17,7,1),(7,20,13,1),(4,23,19,1),
     (36,14,1,16),(33,15,7,1),(30,18,13,1),(27,21,19,1),
     (64,18,1,13),(61,18,7,1),(58,21,13,1),(55,24,19,1)),
    # JP3: moat and stone bridge.
    ((4,28,84,2),(7,23,1,5),(22,23,1,5),(37,23,1,5),(52,23,1,5),
     (67,23,1,5),(82,23,1,5),(7,23,76,1),(11,30,4,3),(32,30,4,3),
     (53,30,4,3),(74,30,4,3)),
    # JP4: castle-town walls and storehouses.
    ((0,25,96,1),(5,20,27,1),(10,18,17,1),(15,16,7,1),
     (8,21,2,10),(27,21,2,10),(44,23,1,7),(46,23,1,7),
     (56,18,25,1),(60,16,17,1),(65,14,7,1),(60,19,2,12),(76,19,2,12)),
    # JP5: stepped castle keep.
    ((18,29,46,2),(23,25,36,2),(27,21,28,2),(31,17,20,2),(36,14,10,1),
     (27,27,2,2),(54,27,2,2),(31,23,2,2),(50,23,2,2),
     (35,19,2,2),(46,19,2,2),(40,15,2,2)),
)


def stage_code(progress):
    stage = stage_index(progress) if isinstance(progress,dict) else min(max(0,progress),GOAL_STAGES-1)
    return REGIONS[stage//STAGES_PER_REGION]+str(stage%STAGES_PER_REGION+1)


def scene_rect(display, x, y, width, height, color=1):
    # Clip decoration/actor backing to the world area; never paint over the HUD.
    right, bottom = min(72, x+width), min(40, y+height)
    left, top = max(0, x), max(14, y)
    if right > left and bottom > top:
        display.drawFilledRectangle(left, top, right-left, bottom-top, color)


def draw_background(display, progress, camera):
    stage = min(max(0, progress), GOAL_STAGES-1)
    for x, y, width, height in SCENERY[stage]:
        # Small distant buildings leave the actor-foot plane (y=21..39) open.
        top = 14+(y-14)//3
        scene_rect(display, x*3//4-camera//3, top, max(1,width*3//4),
                   min(max(1,(height+2)//3),21-top))
    # Three depths of road texture show a broad floor, rather than one platform.
    for y,spacing,width,offset in ((23,12,1,3),(29,18,2,8),(37,24,3,0)):
        for world_x in range(-24,168,spacing):
            scene_rect(display,world_x+offset-camera,y,width,1)


def main_loop():
    thumby.display.setFPS(30)
    action = None
    while action is None:
        action = title_frame()
    state = load_save_data() if action == 'load' else new_game_state()
    while True:
        state = step_frame(state)


def title_frame():
    display = thumby.display
    display.fill(0)
    display.drawText('GROWTH', 18, 2, 1)
    display.drawText('15 DUELS', 12, 12, 1)
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
    if screen == 'country_select':
        display.drawText('START WHERE?' if state['progress']==0 else 'NEXT COUNTRY',0,0,1)
        choices = [region for region in range(3) if region not in state['route']]
        for row,region in enumerate(choices):
            y=10+row*10
            selected=row==state['menu_selection']
            if selected:
                display.drawFilledRectangle(0,y,72,8,1)
            display.drawText(('>' if selected else ' ')+('KOREA','CHINA','JAPAN')[region],0,y,0 if selected else 1)
        if len(choices)<3:
            display.drawText(status if status in ('SAVED','SAVE ERR') else 'B:SAVE',0,30,1)
    elif screen == 'safe' and state['progress'] >= GOAL_STAGES:
        display.drawText('QUEST CLEAR', 3, 0, 1)
        display.drawText('$'+str(state['money']), 0, 10, 1)
        display.drawText('A:NEW', 0, 20, 1)
        display.drawText(status if status in ('SAVED','SAVE ERR') else 'B:SAVE', 0, 30, 1)
    elif screen == 'battle':
        camera = max(0, min(72, state['player_x']-32))
        draw_background(display, stage_index(state), camera)
        draw_rows(display,HEART_ROWS,0,1,5)
        display.drawText(str(state['HP']),7,0,1)
        draw_rows(display,ENEMY_ICON_ROWS,42,1,5)
        display.drawText(str(state['enemy_hp']),49,0,1)
        for x, hp, maximum in ((0, state['HP'], state['maxHP']),
                                (42, state['enemy_hp'], ENCOUNTERS[min(state['progress'],GOAL_STAGES-1)][0])):
            display.drawFilledRectangle(x, 9, 30, 4, 1)
            display.drawFilledRectangle(x+1, 10, 28, 2, 0)
            width = max(0, min(28, 28*hp//max(1,maximum)))
            if width:
                display.drawFilledRectangle(x+1, 10, width, 2, 1)
        actors = [(True, state['player_x'], state.get('player_y',28))]
        if state['active_enemy']:
            actors.append((False, state['enemy_x'], state.get('enemy_y',28)))
        actors.sort(key=lambda actor: actor[2])
        for player, world_x, y in actors:
            x = world_x-camera
            # A black one-pixel backing separates white actors from white scenery.
            scene_rect(display, x-1, y-1, 8, 9, 0)
            rightward = state['direction']=='R' if player else world_x<state['player_x']
            flashing = state.get('player_hit_flash' if player else 'enemy_hit_flash',0)>0 and state['combat_frame']%2==0
            rows = character_rows(state,player)
            if not flashing:
                draw_rows(display,rows,x,y,6,not rightward)
            if not player and state.get('enemy_windup',0):
                # Small outlined warning marker, kept below the HUD.
                warning_y = max(20,y)
                scene_rect(display,x+1,warning_y-6,4,5,0)
                scene_rect(display,x+2,warning_y-5,1,2,1)
                scene_rect(display,x+2,warning_y-2,1,1,1)
            kicking = state.get('attack_kind')=='kick'
            if player and not flashing and state['player_attack_cooldown']>=(15 if kicking else 11):
                length = 4 if kicking else (2 if state['equipped_weapon'] is None else (6 if state['equipped_weapon']==0 else 8))
                front = x+6 if rightward else x-length
                left, right = max(0,front), min(72,front+length)
                if right>left:
                    display.drawFilledRectangle(left,y+(5 if kicking else 3),right-left,1,1)
    elif screen == 'pause':
        display.drawText('HP'+str(state['HP'])+' AT'+str(state['attack'])+' DF'+str(state['defense']),0,0,1)
        index=stage_index(state)
        display.drawText(CITY_NAMES[index//5][index%5],0,10,1)
        display.drawText(status if status in ('SAVED','SAVE ERR') else '$'+str(state['money'])+' '+stage_code(state),0,20,1)
        for row,label in enumerate(('BACK','SAVE')):
            x=row*36
            selected=row==state['menu_selection']
            if selected:
                display.drawFilledRectangle(x,30,36,8,1)
            display.drawText(('>' if selected else ' ')+label,x,30,0 if selected else 1)
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
        index=stage_index(state)
        header = CITY_NAMES[index//5][index%5] if screen == 'safe' else screen.upper()
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
        'A_held': bool(thumby.buttonA.pressed()),
        'B_held': bool(thumby.buttonB.pressed()),
    }


def load_save_data():
    initial = {
        'version': 2, 'money': 0, 'progress': 0, 'route': [], 'owned': [False]*4,
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
