"""Selectable-origin city campaign with map shops and bounded enemy waves."""
from rules import (CITY_NAMES, CITY_MAP_COUNTS, MAX_ACTIVE_ENEMIES,
                   ITEM_NAMES, ITEM_EFFECTS, ITEM_PRICES, GROWTH_LIMIT,
                   apply_stats, combat_power, calculate_damage, item_owned,
                   can_buy, purchase_status)

VERSION = 4
WAVE_DELAY = 24
SHOP_X = 104
SHOP_DEPTH = 19
COUNTRY_NAMES = ('KOREA','CHINA','JAPAN')
COUNTRY_WEAPONS = (4,0,1)  # Korea: gun, China: spear, Japan: sword
WEAPON_LABELS = {0:'SPEAR',1:'SWORD',4:'GUN'}
STAT_STOCK = (6,7,8)
ARMOR_STOCK = (2,3)
FOOD_STOCK = ('RICE','BBQ','SOUP','TEA','NOODLE','BUN','DUCK','TANG','DUMPL','WONTON',
              'SUSHI','CURRY','SOBA','MISO','RAMEN')
ARMOR_LABELS = ('VEST','PAD','SHELL','MAIL','PLATE','GI','GUARD','COAT','SCALE','BRACE',
                'KEIKO','DO','HAORI','LAMELL','KABUTO')


def _copy_foes(foes):
    # Enemy records contain only scalar values; copy them without importing the
    # CPython-only `copy` module, which is absent from the Thumby MicroPython.
    return [dict(foe) for foe in foes]


def new_game_state():
    return dict(campaign_mode=True,version=VERSION,screen_state='country_select',
        money=0,progress=0,route=[],completed_cities=[],current_city=None,
        map_index=0,wave=0,wave_delay=0,frame=0,foes=[],HP=10,maxHP=10,
        attack=2,defense=0,owned=[False]*4,equipped_weapon=None,
        equipped_armor=None,gun_owned=False,skill_owned=False,potions=0,
        hp_growth=0,atk_growth=0,def_growth=0,player_x=16,player_y=28,
        direction='R',player_attack_cooldown=0,attack_kind='punch',
        player_stun=0,player_hit_flash=0,player_invuln=0,command_timer=0,command_ready=0,menu_selection=0,menu_scroll=0,
        menu_r_held=False,save_requested=False,save_status='',boss_active=False)


def valid_save(data):
    if not isinstance(data,dict) or data.get('version')!=VERSION:
        return False
    required={'version','money','progress','route','completed_cities','current_city',
        'map_index','wave','owned','equipped_weapon','equipped_armor','gun_owned',
        'skill_owned','potions','hp_growth','atk_growth','def_growth','boss_active',
        'HP','player_x','player_y','direction'}
    if set(data)!=required:
        return False
    if type(data['money']) is not int or data['money']<0:
        return False
    if type(data['progress']) is not int or not 0<=data['progress']<=15:
        return False
    if not isinstance(data['route'],list) or len(data['route'])>3:
        return False
    if any(type(x) is not int or x not in (0,1,2) for x in data['route']):
        return False
    if len(set(data['route']))!=len(data['route']):
        return False
    done=data['completed_cities']
    if not isinstance(done,list) or len(done)>15 or any(type(x) is not int or not 0<=x<15 for x in done):
        return False
    if len(set(done))!=len(done) or len(done)!=data['progress']:
        return False
    city=data['current_city']
    if city is not None and (type(city) is not int or not 0<=city<15 or city in done):
        return False
    if city is not None and (not data['route'] or city//5!=data['route'][-1]):
        return False
    if type(data['map_index']) is not int or data['map_index']<0:
        return False
    if city is not None and data['map_index']>=CITY_MAP_COUNTS[city//5][city%5]:
        return False
    if type(data['wave']) is not int or data['wave']<0:
        return False
    if type(data['boss_active']) is not bool:
        return False
    if type(data['HP']) is not int or not 0<=data['HP']<=20:
        return False
    if type(data['player_x']) is not int or not 0<=data['player_x']<=138:
        return False
    if type(data['player_y']) is not int or not 12<=data['player_y']<=36:
        return False
    if data['direction'] not in ('L','R'):
        return False
    if not isinstance(data['owned'],list) or len(data['owned'])!=4 or any(type(x) is not bool for x in data['owned']):
        return False
    for field in ('gun_owned','skill_owned'):
        if type(data[field]) is not bool:
            return False
    for field,maximum in (('potions',9),('hp_growth',5),('atk_growth',5),('def_growth',5)):
        if type(data[field]) is not int or not 0<=data[field]<=maximum:
            return False
    weapon=data['equipped_weapon']
    if weapon is not None and (type(weapon) is not int or weapon not in (0,1,4)):
        return False
    armor=data['equipped_armor']
    if armor is not None and (type(armor) is not int or armor not in (2,3)):
        return False
    return True


def encode_save(state):
    data={key:state.get(key) for key in (
        'version','money','progress','route','completed_cities','current_city',
        'map_index','wave','owned','equipped_weapon','equipped_armor','gun_owned',
        'skill_owned','potions','hp_growth','atk_growth','def_growth','boss_active',
        'HP','player_x','player_y','direction')}
    data['route']=list(data['route'])
    data['completed_cities']=list(data['completed_cities'])
    data['owned']=list(data['owned'])
    if not valid_save(data):
        raise ValueError('잘못된 도시 진행 저장 데이터입니다.')
    return data


def decode_save(data):
    if not valid_save(data):
        return None
    state=new_game_state()
    for key,value in data.items():
        state[key]=list(value) if key in ('route','completed_cities','owned') else value
    if state['current_city'] is None:
        state['screen_state']='country_select' if len(state['route'])<3 and (
            not state['route'] or all(c//5 in state['route'] for c in state['completed_cities'])) else 'city_select'
    else:
        state['screen_state']='defeat' if state['HP']<=0 else 'explore'
        state['foes']=spawn_wave(state)
    apply_stats(state)
    state['HP']=min(state['HP'],state['maxHP'])
    return state


def migrate_legacy(old):
    """Keep currency and gear while mapping old one-fight cities to the new route."""
    state=new_game_state()
    state['money']=old['money']
    state['route']=list(old.get('route',[]))
    state['owned']=list(old['owned'])
    for key in ('equipped_weapon','equipped_armor','gun_owned','skill_owned',
                'potions','hp_growth','atk_growth','def_growth'):
        if key in old:
            state[key]=old[key]
    count=min(15,old['progress'])
    for region in state['route']:
        remaining=max(0,min(5,count-region*5))
        for city in range(remaining):
            value=region*5+city
            if value not in state['completed_cities']:
                state['completed_cities'].append(value)
    state['progress']=len(state['completed_cities'])
    if state['progress']>=15:
        state['screen_state']='ending'
    elif not state['route'] or all(state['route'][-1]*5+i in state['completed_cities'] for i in range(5)):
        state['screen_state']='country_select'
    else:
        state['screen_state']='city_select'
    apply_stats(state)
    state['HP']=state['maxHP']
    return state


def map_count(state):
    city=state.get('current_city')
    return CITY_MAP_COUNTS[city//5][city%5] if city is not None else 0


def spawn_wave(state):
    if state.get('boss_active'):
        return [spawn_boss(state)]
    count=1+(state['wave']%MAX_ACTIVE_ENEMIES)
    city=max(0,state.get('current_city') or 0)
    map_level=state.get('map_index',0)
    base=(6,9,12,15,18)[min(4,(city%5+map_level)//2)]
    return [dict(x=max(0,min(132,112-16*i)),y=22+6*i,hp=base+state['wave']%4,
        max_hp=base+state['wave']%4,attack=2+min(3,(city%5+map_level)//3),
        defense=min(2,(city%5+map_level)//4),windup=0,cooldown=24+8*i,
        stun=0,flash=0,hp_seen=False,boss=False) for i in range(count)]


def spawn_boss(state):
    power=combat_power(state)
    base=16+state['progress']*2
    target=24+state['progress']*2
    extra=max(0,power-target)
    hp=base+min(22,extra//2)
    return dict(x=112,y=28,hp=hp,max_hp=hp,attack=4+min(2,extra//14),
        defense=2+min(2,extra//20),windup=0,cooldown=40,stun=0,flash=0,
        hp_seen=False,boss=True)


def _select_city(state,inputs):
    region=state['route'][-1]
    options=[region*5+i for i in range(5) if region*5+i not in state['completed_cities']]
    if not options:
        if len(state['route'])==3:
            state['screen_state']='ending'
        else:
            state['screen_state']='country_select'
        state['menu_selection']=0
        return state
    selected=max(0,min(len(options)-1,state['menu_selection']))
    if inputs['U'] and not inputs['D']: selected=max(0,selected-1)
    elif inputs['D'] and not inputs['U']: selected=min(len(options)-1,selected+1)
    state['menu_selection']=selected
    if selected<state.get('menu_scroll',0): state['menu_scroll']=selected
    elif selected>=state.get('menu_scroll',0)+3: state['menu_scroll']=selected-2
    if inputs['A']:
        state['current_city']=options[selected]
        state['map_index']=0
        state['wave']=0
        state['wave_delay']=0
        state['player_x']=16
        state['foes']=spawn_wave(state)
        state['screen_state']='explore'
    elif inputs['B']:
        state['save_requested']=True
    return state


def _finish_city(state):
    city=state['current_city']
    state['completed_cities'].append(city)
    state['progress']=len(state['completed_cities'])
    state['current_city']=None
    state['map_index']=0
    state['wave']=0
    state['boss_active']=False
    state['foes']=[]
    region=city//5
    if all(region*5+i in state['completed_cities'] for i in range(5)):
        if len(state['route'])>=3:
            state['screen_state']='ending'
        else:
            state['screen_state']='country_select'
    else:
        state['screen_state']='city_select'
    state['menu_selection']=0
    state['menu_scroll']=0
    return state


def _open_shop(state):
    state['screen_state']='shop'
    state['shop_return']='explore'
    state['menu_selection']=0
    state['menu_scroll']=0
    state['shop_notice']=''


def shop_catalog(state):
    """Each country's cities sell its weapon plus city-specific goods."""
    city=state.get('current_city')
    if city is None:
        city=5*(state.get('route') or [0])[-1]
    weapon=COUNTRY_WEAPONS[city//5]
    stat=STAT_STOCK[city%len(STAT_STOCK)]
    armor=ARMOR_STOCK[city%len(ARMOR_STOCK)]
    return ((weapon,WEAPON_LABELS[weapon]),
            (stat,ITEM_NAMES[stat]),
            (armor,ARMOR_LABELS[city]),
            (5,FOOD_STOCK[city]),
            (9,'SKILL'))


def _equip_item(state,item):
    if item in (0,1): state['equipped_weapon']=item
    elif item in (2,3): state['equipped_armor']=item
    elif item==4: state['equipped_weapon']=4
    apply_stats(state)
    return state


def _shop_update(state,inputs):
    if inputs['B']:
        state['screen_state']='explore'
        state['menu_selection']=0
        return state
    catalog=shop_catalog(state)
    last=len(catalog)-1
    selected=max(0,min(last,state['menu_selection']))
    if inputs['U'] and not inputs['D']: selected=max(0,selected-1)
    elif inputs['D'] and not inputs['U']: selected=min(last,selected+1)
    state['menu_selection']=selected
    state['menu_scroll']=max(0,min(last-2,selected-2))
    if inputs['A']:
        item=catalog[selected][0]
        if item<5 and item_owned(state,item):
            _equip_item(state,item)
            state['shop_notice']='EQUIPPED'
        elif can_buy(state,item):
            state['money']-=ITEM_PRICES[item]
            if item<4:
                state['owned'][item]=True
                _equip_item(state,item)
            elif item==4:
                state['gun_owned']=True;_equip_item(state,item)
            elif item==5: state['potions']=state.get('potions',0)+1
            elif item in (6,7,8):
                field=('hp_growth','atk_growth','def_growth')[item-6]
                state[field]=state.get(field,0)+1
                apply_stats(state)
                if item==6: state['HP']=min(state['maxHP'],state['HP']+2)
            elif item==9: state['skill_owned']=True
            state['shop_notice']='EQUIPPED' if item in (0,1,4,2,3) else 'BOUGHT'
    return state


def _explore_update(state,inputs):
    state['frame']+=1
    # Existing reactions lose a frame here; new hits later in the update keep
    # their full duration instead of being shortened immediately.
    state['player_stun']=max(0,state.get('player_stun',0)-1)
    state['player_hit_flash']=max(0,state.get('player_hit_flash',0)-1)
    state['player_invuln']=max(0,state.get('player_invuln',0)-1)
    for foe in state['foes']:
        foe['stun']=max(0,foe['stun']-1)
        foe['flash']=max(0,foe['flash']-1)
    if inputs['A'] and inputs['B']:
        state['screen_state']='pause'
        state['menu_selection']=0
        return state
    if (inputs.get('U_held',False) or inputs['U']) and abs(state['player_x']-SHOP_X)<=6 and state['player_y']<=SHOP_DEPTH:
        _open_shop(state)
        return state
    state['command_timer']=max(0,state.get('command_timer',0)-1)
    state['command_ready']=max(0,state.get('command_ready',0)-1)
    if inputs['U'] and not inputs['D']:
        if state['command_timer']:
            state['command_ready']=12
            state['command_timer']=0
        else:
            state['command_timer']=12
    # A always means punch during combat. Potions are used explicitly from
    # the pause menu so carrying one never swallows an attack input.
    right=int(bool(inputs.get('R_tap',False)))*3 or int(bool(inputs['R']))
    left=int(bool(inputs.get('L_tap',False)))*3 or int(bool(inputs['L']))
    down=int(bool(inputs.get('D_tap',False)))*3 or int(bool(inputs.get('D_held',inputs['D'])))
    up=int(bool(inputs.get('U_tap',False)))*3 or int(bool(inputs.get('U_held',inputs['U'])))
    dx=right-left
    dy=down-up
    player_locked=state.get('player_stun',0)>0
    if player_locked:
        dx=dy=0
    if dx: state['direction']='R' if dx>0 else 'L'
    if not player_locked and state['player_attack_cooldown']==0 and (inputs['A'] or inputs['B']):
        kicking=bool(inputs['B'])
        weapon=state.get('equipped_weapon')
        skill=not kicking and state.get('skill_owned',False) and state['command_ready']>0
        shooting=not kicking and not skill and weapon==4
        state['attack_kind']='kick' if kicking else 'skill' if skill else 'shot' if shooting else 'spear' if weapon==0 else 'sword' if weapon==1 else 'punch'
        state['player_attack_cooldown']=12 if kicking else 30 if skill or shooting else 14 if weapon in (0,1) else 10
        state['command_ready']=0
        state['command_timer']=0
        target=None;best=999
        reach=10 if kicking else 12 if skill else 40 if shooting else 16 if weapon==0 else 11 if weapon==1 else 8
        for foe in state['foes']:
            gap=foe['x']-(state['player_x']+6) if state['direction']=='R' else state['player_x']-(foe['x']+6)
            # A small overlap allowance prevents close enemies from slipping
            # through the hitbox and makes a stationary facing attack reliable.
            if abs(state['player_y']-foe['y'])<=3 and -12<=gap<=reach and abs(gap)<best:
                target=foe;best=abs(gap)
        if target is not None:
            power=1+state.get('atk_growth',0) if shooting else state['attack']+(1 if kicking else 4 if skill else 0)
            damage=calculate_damage({'attack':power},{'defense':target['defense']})
            if not kicking and not skill and weapon in (4,0,1):
                # Preserve the intended gun < spear < sword damage order even
                # when a heavily armored target reduces all three hits.
                damage=max(damage,1 if weapon==4 else 2 if weapon==0 else 3)
            target['hp']=max(0,target['hp']-damage)
            target['hp_seen']=True
            target['stun']=10
            target['flash']=6
            # A brief recoil separates fighters after a confirmed close hit.
            target['x']=max(0,min(138,target['x']+(2 if target['x']>=state['player_x'] else -2)))
            if target['hp']==0:
                state['money']+=30 if target['boss'] else 10+state['wave']%3*5
                state['foes'].remove(target)
                if target['boss']:
                    return _finish_city(state)
                if not state['foes']:
                    state['wave']+=1
                    state['wave_delay']=WAVE_DELAY
    state['player_attack_cooldown']=max(0,state['player_attack_cooldown']-1)
    state['player_x']=max(0,min(138,state['player_x']+dx))
    state['player_y']=max(12,min(36,state['player_y']+dy))
    boss_gate=(state['map_index']==map_count(state)-1 and state['player_x']>=132)
    if not state['foes'] and not boss_gate:
        state['wave_delay']=max(0,state.get('wave_delay',0)-1)
        if state['wave_delay']==0:
            state['foes']=spawn_wave(state)
    for foe in state['foes']:
        if state['frame']%2==0 and not foe['stun']:
            foe['x']=max(0,min(138,foe['x']+(1 if state['player_x']>foe['x'] else -1 if state['player_x']<foe['x'] else 0)))
            foe['y']=max(12,min(36,foe['y']+(1 if state['player_y']>foe['y'] else -1 if state['player_y']<foe['y'] else 0)))
        in_range=abs(state['player_x']-foe['x'])<=12 and abs(state['player_y']-foe['y'])<=3
        if foe['stun']>0:
            foe['windup']=0
        elif in_range and foe['cooldown']<=0 and foe['windup']==0:
            foe['windup']=10
        elif foe['windup']>0:
            foe['windup']-=1
            if foe['windup']==0:
                if in_range and state.get('player_invuln',0)==0:
                    state['HP']=max(0,state['HP']-max(1,foe['attack']-state['defense']))
                    state['player_stun']=8
                    state['player_hit_flash']=6
                    state['player_invuln']=24
                    state['direction']='L' if state['player_x']>foe['x'] else 'R'
                    # Knock the player a couple of pixels away from the attacker.
                    state['player_x']=max(0,min(138,state['player_x']+(2 if state['player_x']>foe['x'] else -2)))
                foe['cooldown']=90
        else:
            foe['cooldown']=max(0,foe['cooldown']-1)
    if state['HP']<=0:
        state['screen_state']='defeat'
    # Map exits are bidirectional. The last exit summons the city boss.
    count=map_count(state)
    if dx>0 and state['player_x']>=138:
        if state['map_index']<count-1:
            state['map_index']+=1;state['player_x']=1;state['wave']=0
            state['foes']=spawn_wave(state);state['wave_delay']=0
        elif not state['boss_active'] and not state['foes']:
            state['boss_active']=True;state['foes']=[spawn_boss(state)]
    elif dx<0 and state['player_x']<=0 and state['map_index']>0:
        state['map_index']-=1;state['player_x']=137;state['boss_active']=False
        state['wave']=0;state['foes']=spawn_wave(state);state['wave_delay']=0
    return state


def update(state,inputs):
    s=dict(state)
    for key in ('route','completed_cities','owned'):
        s[key]=list(state[key])
    s['foes']=_copy_foes(state.get('foes',[]))
    s['save_requested']=False
    screen=s['screen_state']
    if screen=='country_select':
        options=[i for i in range(3) if i not in s['route']]
        if not options:
            s['screen_state']='ending';return s
        ix=max(0,min(len(options)-1,s['menu_selection']))
        if inputs['U'] and not inputs['D']: ix=max(0,ix-1)
        elif inputs['D'] and not inputs['U']: ix=min(len(options)-1,ix+1)
        s['menu_selection']=ix
        if inputs['A']:
            s['route'].append(options[ix])
            s['screen_state']='city_select';s['menu_selection']=0
        elif inputs['B']: s['save_requested']=True
        return s
    if screen=='city_select': return _select_city(s,inputs)
    if screen=='shop': return _shop_update(s,inputs)
    if screen=='explore': return _explore_update(s,inputs)
    if screen=='pause':
        ix=max(0,min(2,s['menu_selection']))
        if inputs['U'] and not inputs['D']: ix=max(0,ix-1)
        elif inputs['D'] and not inputs['U']: ix=min(2,ix+1)
        s['menu_selection']=ix
        if inputs['B'] or (inputs['A'] and ix==0): s['screen_state']='explore'
        elif inputs['A'] and ix==1: s['save_requested']=True
        elif inputs['A'] and ix==2 and s.get('potions',0) and s['HP']<s['maxHP']:
            s['potions']-=1;s['HP']=min(s['maxHP'],s['HP']+6)
        return s
    if screen=='defeat':
        if inputs['A']:
            s['HP']=s['maxHP'];s['screen_state']='explore';s['foes']=spawn_wave(s)
        elif inputs['B']: s['save_requested']=True
        return s
    if screen=='ending':
        if inputs['B']: s['save_requested']=True
        elif inputs['A']: return new_game_state()
        return s
    return s


