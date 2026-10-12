def update_state(state, inputs):
    new_state = dict(state)
    new_state['owned'] = list(state['owned'])
    screen = state['screen_state']
    r_new = inputs['R'] and not state['menu_r_held']
    new_state['menu_r_held'] = inputs['R']
    new_state['save_requested'] = False

    # 복귀 입력은 전환한 화면에서 다시 처리하지 않는다.
    if inputs['B']:
        if screen == 'battle':
            new_state['screen_state'] = 'pause'
        elif screen == 'pause':
            new_state['screen_state'] = 'battle'
        elif screen in ('shop', 'equip'):
            new_state['screen_state'] = 'safe'
        elif screen in ('shop_detail', 'equip_detail'):
            new_state['screen_state'] = screen[:-7]
            return new_state
        else:
            return new_state
        new_state['menu_selection'] = 0
        new_state['menu_scroll'] = 0
        return new_state

    if screen in ('safe', 'pause', 'shop', 'equip'):
        limit = 1 if screen == 'pause' else 3
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

    # NEXT와 재도전은 초기화만 수행하고 전투는 다음 호출부터 진행한다.
    if inputs['A'] and ((screen == 'safe' and new_state['menu_selection'] == 0)
                        or screen == 'defeat'):
        new_state['HP'] = new_state['maxHP']
        new_state['player_x'] = 16
        new_state['enemy_x'] = 112
        new_state['direction'] = 'R'
        new_state['combat_frame'] = 0
        new_state['player_attack_cooldown'] = 0
        new_state['enemy_attack_cooldown'] = 0
        new_state['active_enemy'] = True
        odd = new_state['progress'] % 2
        new_state['enemy_hp'] = 10 if odd else 6
        new_state['enemy_attack'] = 3 if odd else 2
        new_state['enemy_defense'] = 1 if odd else 0
        weapon = new_state['equipped_weapon']
        armor = new_state['equipped_armor']
        new_state['attack'] = 2 + (0 if weapon is None else (2 if weapon == 0 else 4))
        new_state['defense'] = 0 if armor is None else (1 if armor == 2 else 2)
        new_state['screen_state'] = 'battle'
        new_state['menu_selection'] = 0
        new_state['menu_scroll'] = 0
        return new_state

    if screen == 'safe':
        if inputs['A']:
            selected = new_state['menu_selection']
            if selected in (1, 2):
                new_state['screen_state'] = 'shop' if selected == 1 else 'equip'
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
            else:
                new_state['save_requested'] = True
        return new_state
    if screen == 'defeat':
        return new_state

    if screen in ('shop', 'shop_detail', 'equip', 'equip_detail'):
        if inputs['A']:
            item_id = new_state['menu_selection']
            if screen in ('shop', 'shop_detail'):
                price = get_item_price(item_id)
                if not new_state['owned'][item_id] and new_state['money'] >= price:
                    new_state['money'] -= price
                    new_state['owned'][item_id] = True
            elif new_state['owned'][item_id]:
                if item_id < 2:
                    new_state['equipped_weapon'] = None if new_state['equipped_weapon'] == item_id else item_id
                else:
                    new_state['equipped_armor'] = None if new_state['equipped_armor'] == item_id else item_id
                weapon = new_state['equipped_weapon']
                armor = new_state['equipped_armor']
                new_state['attack'] = 2 + (0 if weapon is None else (2 if weapon == 0 else 4))
                new_state['defense'] = 0 if armor is None else (1 if armor == 2 else 2)
        return new_state
    if screen != 'battle':
        return new_state

    new_state['combat_frame'] += 1
    new_state['player_attack_cooldown'] = max(0, state['player_attack_cooldown'] - 1)
    new_state['enemy_attack_cooldown'] = max(0, state['enemy_attack_cooldown'] - 1)
    player = state['player_x']
    enemy = state['enemy_x']
    moved = player
    if inputs['L'] and not inputs['R']:
        moved = max(0, player - 1)
        if new_state['active_enemy'] and enemy < player:
            moved = max(moved, enemy + 8)
    elif inputs['R'] and not inputs['L']:
        moved = min(136, player + 1)
        if new_state['active_enemy'] and enemy > player:
            moved = min(moved, enemy - 8)
    if moved != player:
        new_state['direction'] = 'R' if moved > player else 'L'
    new_state['player_x'] = moved
    if new_state['active_enemy'] and new_state['combat_frame'] % 2 == 0:
        if enemy > moved:
            enemy = max(moved + 8, enemy - 1)
        else:
            enemy = min(moved - 8, enemy + 1)
        new_state['enemy_x'] = enemy

    if inputs['A'] and new_state['player_attack_cooldown'] == 0:
        new_state['player_attack_cooldown'] = 15
        gap = enemy - (moved + 8) if new_state['direction'] == 'R' else moved - (enemy + 8)
        if new_state['active_enemy'] and 0 <= gap <= 8:
            damage = calculate_damage(new_state, {'defense': new_state['enemy_defense']})
            new_state['enemy_hp'] = max(0, new_state['enemy_hp'] - damage)
            if new_state['enemy_hp'] == 0:
                new_state['money'] += 30 if new_state['progress'] % 2 else 20
                new_state['progress'] += 1
                new_state['HP'] = new_state['maxHP']
                new_state['active_enemy'] = False
                new_state['enemy_hp'] = 0
                new_state['enemy_attack'] = 0
                new_state['enemy_defense'] = 0
                new_state['screen_state'] = 'safe'
                new_state['menu_selection'] = 0
                new_state['menu_scroll'] = 0
                return new_state

    gap = max(moved, enemy) - (min(moved, enemy) + 8)
    if new_state['active_enemy'] and 0 <= gap <= 2 and new_state['enemy_attack_cooldown'] == 0:
        damage = calculate_damage({'attack': new_state['enemy_attack']}, new_state)
        new_state['HP'] = max(0, new_state['HP'] - damage)
        new_state['enemy_attack_cooldown'] = 30
    if new_state['HP'] == 0:
        new_state['screen_state'] = 'defeat'
        new_state['menu_selection'] = 0
        new_state['menu_scroll'] = 0
    return new_state

def calculate_damage(attacker_stats, defender_stats):
    return max(1, attacker_stats['attack'] - defender_stats['defense'])

def get_item_price(item_id):
    prices = [40, 80, 40, 80]
    return prices[item_id]

def get_item_type(item_id):
    types = ['weapon', 'weapon', 'armor', 'armor']
    return types[item_id]

def is_valid_save_data(data):
    if not isinstance(data, dict):
        return False
    
    required_keys = {'version', 'money', 'progress', 'owned', 'equipped_weapon', 'equipped_armor'}
    if set(data.keys()) != required_keys:
        return False
    
    if data['version'] != 1 or type(data['version']) is not int:
        return False
    
    if type(data['money']) is not int or data['money'] < 0:
        return False
    
    if type(data['progress']) is not int or data['progress'] < 0:
        return False
    
    if not isinstance(data['owned'], list) or len(data['owned']) != 4:
        return False
    for item in data['owned']:
        if not isinstance(item, bool):
            return False
    
    if data['equipped_weapon'] is not None and (type(data['equipped_weapon']) is not int or data['equipped_weapon'] not in (0, 1)):
        return False
    
    if data['equipped_armor'] is not None and (type(data['equipped_armor']) is not int or data['equipped_armor'] not in (2, 3)):
        return False
    
    # 장착된 아이템은 반드시 소유해야 함
    if data['equipped_weapon'] is not None and not data['owned'][data['equipped_weapon']]:
        return False
    
    if data['equipped_armor'] is not None and not data['owned'][data['equipped_armor']]:
        return False
    
    return True

def encode_save_data(state):
    return {
        'version': 1,
        'money': state['money'],
        'progress': state['progress'],
        'owned': list(state['owned']),
        'equipped_weapon': state['equipped_weapon'],
        'equipped_armor': state['equipped_armor']
    }

def decode_save_data(data):
    if not is_valid_save_data(data):
        return None
    
    new_state = dict(
        HP=10,
        maxHP=10,
        money=data['money'],
        attack=2,
        defense=0,
        progress=data['progress'],
        owned=list(data['owned']),
        equipped_weapon=data['equipped_weapon'],
        equipped_armor=data['equipped_armor'],
        player_x=16,
        enemy_x=112,
        screen_state='safe',
        menu_selection=0,
        menu_scroll=0,
        direction='R',
        player_attack_cooldown=0,
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
    
    # 장비 스탯 재계산
    if new_state['equipped_weapon'] is not None:
        new_state['attack'] += 2 if new_state['equipped_weapon'] == 0 else 4
    
    if new_state['equipped_armor'] is not None:
        new_state['defense'] += 1 if new_state['equipped_armor'] == 2 else 2
    
    return new_state
