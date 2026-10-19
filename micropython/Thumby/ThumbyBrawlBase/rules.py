STAGES_PER_REGION = 5
REGIONS = ('KR', 'CN', 'JP')
GOAL_STAGES = 15
ENEMY_WINDUP_FRAMES = 12
HIT_FLASH_FRAMES = 6
# Small demo economy; the first four equipment IDs remain save-compatible.
ITEM_NAMES = ('BLADE','SWORD','VEST','ARMOR','GUN','MEAT','HP+','ATK+','DEF+','SKILL')
ITEM_PRICES = (40,80,40,80,60,15,50,60,60,80)
ITEM_EFFECTS = ('ATK+2','ATK+4','DEF+1','DEF+2','RNG40','HEAL+6','HP+2','ATK+1','DEF+1','UU+A')
GROWTH_LIMIT = 5
COMMAND_WINDOW = 12


def item_owned(state, item):
    if item < 4:
        return state['owned'][item]
    if item == 4:
        return state.get('gun_owned',False)
    if item == 9:
        return state.get('skill_owned',False)
    return False


def item_counter(state,item):
    if item==5:
        return state.get('potions',0)
    if item in (6,7,8):
        return state.get(('hp_growth','atk_growth','def_growth')[item-6],0)
    return None


def purchase_status(state,item):
    if item_owned(state,item):
        return 'OWNED'
    counter=item_counter(state,item)
    if counter is not None and counter >= (9 if item==5 else GROWTH_LIMIT):
        return 'STOCK FULL' if item==5 else 'MAX LEVEL'
    if state['money'] < get_item_price(item):
        return 'NO MONEY'
    return 'A:BUY'


def can_buy(state,item):
    return purchase_status(state,item)=='A:BUY'


def apply_stats(state):
    weapon,armor = state['equipped_weapon'],state['equipped_armor']
    state['maxHP'] = 10+2*state.get('hp_growth',0)
    state['attack'] = 2+state.get('atk_growth',0)+(2 if weapon==0 else 4 if weapon==1 else 0)
    state['defense'] = state.get('def_growth',0)+(1 if armor==2 else 2 if armor==3 else 0)
# HP, attack, defense. Each fifth encounter closes one region.
ENCOUNTERS = (
    (6,2,0), (10,3,1), (8,3,0), (12,3,1), (16,4,2),
    (10,3,1), (12,3,1), (12,4,1), (16,4,2), (20,4,2),
    (14,4,2), (16,4,2), (18,4,2), (18,5,2), (24,5,3),
)
CITY_NAMES = (
    ('SEOUL','BUSAN','DAEGU','GYEONGJU','ULSAN'),
    ('BEIJING','SHANGHAI','GUANGZHOU','CHENGDU','XIAN'),
    ('TOKYO','OSAKA','KYOTO','NAGOYA','SAPPORO'),
)
# Each city is a short chain of explorable screens. The final screen leads to
# the city boss; regular enemy waves can continue until the player moves on.
CITY_MAP_COUNTS = (
    (5,4,3,2,3),
    (5,4,3,2,4),
    (5,4,3,2,4),
)
MAX_ACTIVE_ENEMIES = 3
ENEMY_WAVE_DELAY = 24


def city_map_count(region, city):
    return CITY_MAP_COUNTS[region][city]


def legacy_route(progress):
    completed = min(3, progress//5)
    count = min(3, completed+(1 if progress%5 or progress==0 else 0))
    return list(range(count))


def stage_index(state):
    if isinstance(state,dict) and state.get('campaign_mode') and state.get('current_city') is not None:
        return state['current_city']
    route = state.get('route', legacy_route(state['progress']))
    region = route[-1] if route else 0
    city = 4 if state['progress'] >= GOAL_STAGES else state['progress']%5
    return region*5+city


def combat_power(state):
    # Current build strength, independent of the selected country or its identity.
    return state.get('maxHP',10)//2 + state.get('attack',2)*3 + state.get('defense',0)*2


def encounter_stats(state):
    progress=min(max(0,state['progress']),GOAL_STAGES-1)
    hp,attack,defense=ENCOUNTERS[progress]
    if progress%STAGES_PER_REGION == STAGES_PER_REGION-1:
        boss_round=progress//STAGES_PER_REGION
        target_power=20+8*boss_round
        surplus=max(0,combat_power(state)-target_power)
        hp+=min(16,surplus//2)
        attack+=min(2,surplus//12)
        defense+=min(2,surplus//18)
    return hp,attack,defense


def new_game_state():
    return decode_save_data(dict(version=2, money=0, progress=0, route=[],
        owned=[False]*4, equipped_weapon=None, equipped_armor=None))


def update_state(state, inputs):
    new_state = dict(state)
    new_state['owned'] = list(state['owned'])
    new_state['route'] = list(state.get('route', legacy_route(state['progress'])))
    new_state.setdefault('player_y', 28)
    new_state.setdefault('enemy_y', 28)
    screen = state['screen_state']
    r_new = inputs['R'] and not state['menu_r_held']
    new_state['menu_r_held'] = inputs['R']
    new_state['save_requested'] = False
    new_state.setdefault('attack_kind', 'punch')
    for field in ('enemy_windup','enemy_stun','enemy_hit_flash','player_hit_flash'):
        new_state.setdefault(field,0)
    for field in ('command_timer','command_ready'):
        new_state.setdefault(field,0)

    # A storefront can be opened from the map when the fighter reaches its door.
    if (screen == 'battle' and inputs['U'] and not inputs['D']
            and abs(state['player_x']-104)<=8):
        new_state['screen_state']='shop'
        new_state['shop_return']='battle'
        new_state['menu_selection']=0
        new_state['menu_scroll']=0
        return new_state

    if screen == 'country_select':
        choices = [region for region in range(3) if region not in new_state['route']]
        if not choices:
            new_state['screen_state'] = 'safe'
            return new_state
        selected = min(state['menu_selection'], len(choices)-1)
        if inputs['U'] and not inputs['D']:
            selected = max(0, selected-1)
        elif inputs['D'] and not inputs['U']:
            selected = min(len(choices)-1, selected+1)
        new_state['menu_selection'] = selected
        if inputs['B']:
            new_state['save_requested'] = True
        elif inputs['A']:
            new_state['route'].append(choices[selected])
            new_state['screen_state'] = 'safe'
            new_state['menu_selection'] = 0
            new_state['menu_scroll'] = 0
        return new_state

    # A completed save opens the ending, rather than an endless next fight.
    if screen == 'safe' and state['progress'] >= GOAL_STAGES:
        if inputs['B']:
            new_state['save_requested'] = True
        elif inputs['A']:
            return new_game_state()
        return new_state

    # Both attack buttons open the status screen and cannot also deal damage.
    chord = (inputs['A'] and inputs['B']) or (
        inputs.get('A_held', False) and inputs.get('B_held', False)
        and (inputs['A'] or inputs['B']))
    if screen == 'battle' and chord:
        new_state['screen_state'] = 'pause'
        new_state['menu_selection'] = 0
        new_state['menu_scroll'] = 0
        new_state['command_timer'] = 0
        new_state['command_ready'] = 0
        return new_state

    # 画面遷移の入力は、遷移先で重ねて処理しない。
    if inputs['B'] and screen != 'battle':
        if screen == 'pause':
            new_state['screen_state'] = 'battle'
        elif screen in ('shop', 'equip'):
            new_state['screen_state'] = state.get('shop_return','safe') if screen=='shop' else 'safe'
        elif screen in ('shop_detail', 'equip_detail'):
            new_state['screen_state'] = screen[:-7]
            return new_state
        else:
            return new_state
        new_state['menu_selection'] = 0
        new_state['menu_scroll'] = 0
        return new_state

    if screen in ('safe', 'pause', 'shop', 'equip'):
        limit = 2 if screen == 'pause' else 9 if screen == 'shop' else 4 if screen == 'equip' else 3
        selected = state['menu_selection']
        if inputs['U'] and not inputs['D']:
            selected = max(0, selected - 1)
        elif inputs['D'] and not inputs['U']:
            selected = min(limit, selected + 1)
        scroll = state['menu_scroll']
        if selected < scroll:
            scroll = selected
        elif selected >= scroll + 3:
            scroll = selected - 2
        new_state['menu_selection'] = selected
        new_state['menu_scroll'] = max(0, min(max(0, limit - 2), scroll))
        if screen in ('shop', 'equip') and r_new:
            new_state['screen_state'] = screen + '_detail'
            return new_state

    # NEXTと再挑戦は状態だけ初期化し、戦闘処理は次の呼び出しから行う。
    if inputs['A'] and ((screen == 'safe' and new_state['menu_selection'] == 0)
                        or screen == 'defeat'):
        new_state['HP'] = new_state['maxHP']
        new_state['player_x'] = 16
        new_state['enemy_x'] = 112
        new_state['player_y'] = 28
        new_state['enemy_y'] = 28
        new_state['direction'] = 'R'
        new_state['combat_frame'] = 0
        new_state['player_attack_cooldown'] = 0
        new_state['attack_kind'] = 'punch'
        for field in ('enemy_windup','enemy_stun','enemy_hit_flash','player_hit_flash'):
            new_state[field] = 0
        new_state['enemy_attack_cooldown'] = 0
        new_state['active_enemy'] = True
        apply_stats(new_state)
        hp, attack, defense = encounter_stats(new_state)
        new_state['enemy_hp'] = hp
        new_state['enemy_attack'] = attack
        new_state['enemy_defense'] = defense
        new_state['command_timer'] = 0
        new_state['command_ready'] = 0
        new_state['screen_state'] = 'battle'
        new_state['menu_selection'] = 0
        new_state['menu_scroll'] = 0
        return new_state

    if screen == 'safe':
        if inputs['A']:
            selected = new_state['menu_selection']
            if selected in (1, 2):
                new_state['screen_state'] = 'shop' if selected == 1 else 'equip'
                new_state['shop_return'] = 'safe'
                new_state['menu_selection'] = 0
                new_state['menu_scroll'] = 0
            elif selected == 3:
                new_state['save_requested'] = True
        return new_state
    if screen == 'pause':
        if inputs['A']:
            if new_state['menu_selection'] == 0:
                new_state['screen_state'] = 'battle'
                new_state['menu_selection'] = 0
                new_state['menu_scroll'] = 0
            elif new_state['menu_selection'] == 1:
                new_state['save_requested'] = True
            elif new_state.get('potions',0) and new_state['HP'] < new_state['maxHP']:
                new_state['potions'] -= 1
                new_state['HP'] = min(new_state['maxHP'],new_state['HP']+6)
        return new_state
    if screen == 'defeat':
        return new_state

    if screen in ('shop', 'shop_detail', 'equip', 'equip_detail'):
        if inputs['A']:
            item_id = new_state['menu_selection']
            if screen in ('shop', 'shop_detail'):
                price = get_item_price(item_id)
                if can_buy(new_state,item_id):
                    new_state['money'] -= price
                    if item_id < 4:
                        new_state['owned'][item_id] = True
                    elif item_id in (4,9):
                        new_state['gun_owned' if item_id==4 else 'skill_owned'] = True
                    elif item_id==5:
                        new_state['potions'] = new_state.get('potions',0)+1
                    else:
                        field = ('hp_growth','atk_growth','def_growth')[item_id-6]
                        new_state[field] = new_state.get(field,0)+1
                        apply_stats(new_state)
                        if item_id==6:
                            new_state['HP'] = min(new_state['maxHP'],new_state['HP']+2)
            elif item_owned(new_state,item_id):
                if item_id in (0,1,4):
                    new_state['equipped_weapon'] = None if new_state['equipped_weapon'] == item_id else item_id
                else:
                    new_state['equipped_armor'] = None if new_state['equipped_armor'] == item_id else item_id
                apply_stats(new_state)
        return new_state
    if screen != 'battle':
        return new_state

    new_state['combat_frame'] += 1
    for field in ('enemy_stun','enemy_hit_flash','player_hit_flash'):
        new_state[field] = max(0,new_state[field]-1)
    new_state['player_attack_cooldown'] = max(0, state['player_attack_cooldown'] - 1)
    new_state['enemy_attack_cooldown'] = max(0, state['enemy_attack_cooldown'] - 1)
    # Direction edges, not held movement, arm the purchased UP UP + A skill.
    new_state['command_timer'] = max(0,new_state['command_timer']-1)
    new_state['command_ready'] = max(0,new_state['command_ready']-1)
    if inputs['U'] and not inputs['D']:
        if new_state['command_timer']:
            new_state['command_ready'] = COMMAND_WINDOW
            new_state['command_timer'] = 0
        else:
            new_state['command_timer'] = COMMAND_WINDOW
    # World 144x40. Top-left body coordinates; HUD occupies y=0..13.
    player = state['player_x']
    enemy = state['enemy_x']
    py = new_state['player_y']
    ey = new_state['enemy_y']
    dx = int(bool(inputs['R'])) - int(bool(inputs['L']))
    dy = int(bool(inputs.get('D_held', inputs['D']))) - int(bool(inputs.get('U_held', inputs['U'])))
    if dx:
        new_state['direction'] = 'R' if dx > 0 else 'L'
    # Two pixels per held frame makes short-screen combat less sluggish.
    moved = max(0, min(138, player + dx * 2))
    moved_y = max(15, min(33, py + dy * 2))
    # Resolve each axis separately so actors can slide past one another.
    if new_state['active_enemy'] and abs(moved-enemy) < 6 and abs(py-ey) < 7:
        moved = player
    if new_state['active_enemy'] and abs(moved-enemy) < 6 and abs(moved_y-ey) < 7:
        moved_y = py
    new_state['player_x'] = moved
    new_state['player_y'] = moved_y
    if (new_state['active_enemy'] and not state.get('enemy_stun',0)
            and not state.get('enemy_windup',0) and new_state['combat_frame'] % 2 == 0):
        next_enemy = max(0, min(138, enemy + (1 if moved > enemy else -1 if moved < enemy else 0)))
        if not (abs(next_enemy-moved) < 6 and abs(ey-moved_y) < 7):
            enemy = next_enemy
        next_y = max(15, min(33, ey + (1 if moved_y > ey else -1 if moved_y < ey else 0)))
        if not (abs(enemy-moved) < 6 and abs(next_y-moved_y) < 7):
            ey = next_y
        new_state['enemy_x'] = enemy
        new_state['enemy_y'] = ey
    same_lane = abs(moved_y-ey) <= 3

    if (inputs['A'] or inputs['B']) and new_state['player_attack_cooldown'] == 0:
        kicking = bool(inputs['B'])
        skill = not kicking and new_state.get('skill_owned',False) and new_state['command_ready']>0
        shooting = not kicking and not skill and new_state['equipped_weapon']==4
        new_state['attack_kind'] = 'skill' if skill else 'shot' if shooting else 'kick' if kicking else 'punch'
        new_state['player_attack_cooldown'] = 30 if skill or shooting else 12 if kicking else 10
        new_state['command_ready'] = 0
        new_state['command_timer'] = 0
        gap = enemy - (moved + 6) if new_state['direction'] == 'R' else moved - (enemy + 6)
        reach = 40 if shooting else 12 if skill else 10 if kicking else 8
        if new_state['active_enemy'] and same_lane and 0 <= gap <= reach:
            power = 1+new_state.get('atk_growth',0) if shooting else new_state['attack']+(4 if skill else 0)
            damage = calculate_damage({'attack':power}, {'defense': new_state['enemy_defense']})
            new_state['enemy_hp'] = max(0, new_state['enemy_hp'] - damage)
            # A landed hit interrupts preparation; misses never cause stun.
            new_state['enemy_windup'] = 0
            new_state['enemy_stun'] = 12 if kicking else 8
            new_state['enemy_hit_flash'] = HIT_FLASH_FRAMES
            if kicking:
                enemy = max(0,min(138,enemy+(3 if new_state['direction']=='R' else -3)))
                new_state['enemy_x'] = enemy
            if new_state['enemy_hp'] == 0:
                new_state['money'] += 30 if new_state['progress'] % 2 else 20
                new_state['progress'] += 1
                new_state['HP'] = new_state['maxHP']
                new_state['active_enemy'] = False
                new_state['enemy_hp'] = 0
                new_state['enemy_attack'] = 0
                new_state['enemy_defense'] = 0
                new_state['screen_state'] = ('country_select' if
                    new_state['progress'] < GOAL_STAGES and new_state['progress']%5 == 0 else 'safe')
                new_state['menu_selection'] = 0
                new_state['menu_scroll'] = 0
                return new_state

    gap = max(moved, enemy) - (min(moved, enemy) + 6)
    in_range = same_lane and 0 <= gap <= 2
    if new_state['active_enemy'] and not new_state['enemy_stun']:
        if new_state['enemy_windup']:
            new_state['enemy_windup'] -= 1
            if new_state['enemy_windup'] == 0:
                # Commit the swing even after a dodge; recovery prevents instant retry.
                if in_range:
                    damage = calculate_damage({'attack': new_state['enemy_attack']}, new_state)
                    new_state['HP'] = max(0, new_state['HP'] - damage)
                    new_state['player_hit_flash'] = HIT_FLASH_FRAMES
                new_state['enemy_attack_cooldown'] = 120
        elif in_range and new_state['enemy_attack_cooldown'] == 0:
            new_state['enemy_windup'] = ENEMY_WINDUP_FRAMES
    if new_state['HP'] == 0:
        new_state['screen_state'] = 'defeat'
        new_state['menu_selection'] = 0
        new_state['menu_scroll'] = 0
    return new_state

def calculate_damage(attacker_stats, defender_stats):
    return max(1, attacker_stats['attack'] - defender_stats['defense'])

def get_item_price(item_id):
    return ITEM_PRICES[item_id]

def get_item_type(item_id):
    types = ('weapon','weapon','armor','armor','weapon','potion','growth','growth','growth','skill')
    return types[item_id]

def is_valid_save_data(data):
    if not isinstance(data, dict):
        return False

    required_keys = {'version', 'money', 'progress', 'owned', 'equipped_weapon', 'equipped_armor'}
    if not required_keys.issubset(data):
        return False
    if type(data['version']) is not int or data['version'] not in (1,2,3):
        return False
    if data['version'] >= 2:
        required_keys.add('route')
    if data['version']==3:
        required_keys.update(('gun_owned','skill_owned','potions','hp_growth','atk_growth','def_growth'))
        for field in ('gun_owned','skill_owned'):
            if type(data.get(field)) is not bool:
                return False
        for field,maximum in (('potions',9),('hp_growth',5),('atk_growth',5),('def_growth',5)):
            if type(data.get(field)) is not int or not 0<=data[field]<=maximum:
                return False
    if set(data.keys()) != required_keys:
        return False

    if type(data['money']) is not int or data['money'] < 0:
        return False

    if type(data['progress']) is not int or data['progress'] < 0:
        return False
    if data['version'] >= 2:
        route = data['route']
        completed, city = divmod(data['progress'],5)
        if data['progress'] > 15 or not isinstance(route,list) or len(route)>3:
            return False
        if any(type(region) is not int or region not in (0,1,2) for region in route):
            return False
        if len(set(route)) != len(route):
            return False
        if city and len(route) != completed+1:
            return False
        if not city and len(route) not in (completed,min(3,completed+1)):
            return False

    if not isinstance(data['owned'], list) or len(data['owned']) != 4:
        return False
    for item in data['owned']:
        if not isinstance(item, bool):
            return False

    if data['equipped_weapon'] is not None and (type(data['equipped_weapon']) is not int or data['equipped_weapon'] not in ((0,1,4) if data['version']==3 else (0,1))):
        return False

    if data['equipped_armor'] is not None and (type(data['equipped_armor']) is not int or data['equipped_armor'] not in (2, 3)):
        return False

    # 装備できるのは所有しているアイテムだけ。
    if data['equipped_weapon'] is not None and not item_owned(data,data['equipped_weapon']):
        return False

    if data['equipped_armor'] is not None and not data['owned'][data['equipped_armor']]:
        return False

    return True

def encode_save_data(state):
    data = {
        'version': 3,
        'money': state['money'],
        'progress': state['progress'],
        'owned': list(state['owned']),
        'equipped_weapon': state['equipped_weapon'],
        'equipped_armor': state['equipped_armor'],
        'route': list(state.get('route', legacy_route(state['progress'])))
    }
    for field in ('gun_owned','skill_owned','potions','hp_growth','atk_growth','def_growth'):
        data[field] = state.get(field,False if field.endswith('_owned') else 0)
    if not is_valid_save_data(data):
        raise ValueError('保存する進行状況／地域順序が正しくありません。')
    return data

def decode_save_data(data):
    if not is_valid_save_data(data):
        return None

    progress = min(15,data['progress'])
    route = list(data['route'] if data['version']>=2 else legacy_route(progress))
    selecting = progress<15 and len(route)==progress//5
    new_state = dict(
        HP=10,
        maxHP=10,
        money=data['money'],
        attack=2,
        defense=0,
        progress=progress,
        route=route,
        owned=list(data['owned']),
        equipped_weapon=data['equipped_weapon'],
        equipped_armor=data['equipped_armor'],
        player_x=16,
        player_y=28,
        enemy_y=28,
        enemy_x=112,
        screen_state='country_select' if selecting else 'safe',
        menu_selection=0,
        menu_scroll=0,
        direction='R',
        player_attack_cooldown=0,
        attack_kind='punch',
        enemy_windup=0,
        enemy_stun=0,
        enemy_hit_flash=0,
        player_hit_flash=0,
        enemy_attack_cooldown=0,
        active_enemy=False,
        enemy_hp=0,
        enemy_attack=0,
        enemy_defense=0,
        combat_frame=0,
        save_requested=False,
        save_status='',
        menu_r_held=False
    )

    for field in ('gun_owned','skill_owned','potions','hp_growth','atk_growth','def_growth'):
        new_state[field] = data.get(field,False if field.endswith('_owned') else 0)
    new_state['command_timer'] = 0
    new_state['command_ready'] = 0
    apply_stats(new_state)
    new_state['HP'] = new_state['maxHP']

    return new_state
