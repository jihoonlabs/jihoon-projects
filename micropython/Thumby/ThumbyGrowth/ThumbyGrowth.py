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
                   CITY_NAMES, stage_index, new_game_state, ITEM_NAMES,
                   ITEM_EFFECTS, get_item_price, item_owned,
                   item_counter, purchase_status)

from scene_art import SCENE_BITMAPS

# Shared 10x14 period fighters; simulation collision remains 6x7.
HERO_HEADS = ((0xfc,0x1fe,0x1fe,0x1fe,0x1fe,0x132,0x1fe,0xfc),
              (0xfc,0x1fe,0xfe,0x1fe,0x1fe,0x132,0x1fe,0xfc),
              (0xfc,0x1fe,0x1ff,0x1fe,0x1fe,0x132,0x1fe,0xfc))
HERO_HEAD = HERO_HEADS[0]
FOE_HEAD = (0x0,0x78,0xfc,0x1fe,0x17a,0x1fe,0x1ce,0xfc)
BODY_ROWS = (0x3ff,0x1fe,0xdc,0xfc,0xcc,0x1ce)
WALK_BODY_ROWS = (0x3ff,0x1fe,0xdc,0xfc,0x6c,0xe6)
PUNCH_BODY = (0x78,0xf8,0x78,0xfc,0xcc,0x1ce)
KICK_BODY = (0xf8,0x78,0x78,0xfe,0xc0,0x1c0)
HURT_BODY = (0xfc,0x78,0xcc,0x78,0x6c,0xe7)
GUARD_BODY = (0x1b6,0x1fe,0x78,0xfc,0xcc,0x1ce)
BOSS_HEADS = ((0x84,0x1fe,0x3ff,0x2fd,0x1fe,0x12e,0x1fe,0xfc),
              (0xfc,0x1fe,0x3ff,0x303,0x1fe,0x16a,0x1fe,0xfc),
              (0x30,0xfc,0x1fe,0x3cf,0x1fe,0x1b6,0x1fe,0xfc))
HEART_ROWS = b'\x0a\x1f\x1f\x0e\x04'
ENEMY_ICON_ROWS = b'\x0e\x1f\x15\x0e\x0a'
# Original large face: shared outline, hair, eyes and collar.
PORTRAIT_ROWS = (0x03c0,0x0ff0,0x1ff8,0x3ffc,0x3ffc,0x3ffc,0x3ffc,0x2aa4,
                0x2224,0x2224,0x2004,0x2184,0x1008,0x0ff0,0x0660,0x0db0)
MERCHANT_HEADS = ((0x03c0,0x0ff0,0x1ff8),(0x0ff0,0x1ff8,0x3ffc),(0x0240,0x0ff0,0x1ff8))
# Three tiny country motifs: leaf, lantern, petal. No per-frame bitmap buffers.
SCENE_MOTIFS = (b'\x04\x0e\x06',b'\x04\x0e\x15\x0e\x04',b'\x0a\x1f\x0e')
SCENE_ANCHORS = (((2,0),(32,2),(64,1)),((2,0),(20,0),(61,0)),
                 ((16,0),(32,0),(62,0)),((3,0),(26,0),(64,0)))


def portrait_rows(state,merchant=False):
    if not merchant:
        return PORTRAIT_ROWS
    # Share face/collar; regional hair and the smiling mouth are small parts.
    return MERCHANT_HEADS[stage_index(state)//5]+PORTRAIT_ROWS[3:11]+(0x23c4,)+PORTRAIT_ROWS[12:]


def draw_rows(display, rows, x, y, width, mirror=False, min_y=0):
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
            if right>left and min_y<=y+row<40:
                display.drawFilledRectangle(left,y+row,right-left,1,1)


def draw_portrait(display,rows,x,y,frame=0):
    draw_rows(display,rows,x,y,16)
    if frame%120>=116:
        # Close only the shared eye area; face, hair and collar remain original.
        for eye in (5,9):
            for top,height,color in ((8,2,0),(9,1,1)):
                left,right=max(0,x+eye),min(72,x+eye+3)
                first,last=max(0,y+top),min(40,y+top+height)
                if right>left and last>first:
                    display.drawFilledRectangle(left,first,right-left,last-first,color)


def hero_region(state):
    # The first chosen country is identity; later route entries are destinations.
    route=state.get('route',())
    return route[0] if route else 0


def character_head(state, player):
    if player:
        return HERO_HEADS[hero_region(state)]
    elif state['progress']%STAGES_PER_REGION == STAGES_PER_REGION-1:
        return BOSS_HEADS[stage_index(state)//STAGES_PER_REGION]
    return FOE_HEAD


def character_pose(state,player):
    if state.get('player_hit_flash' if player else 'enemy_hit_flash',0):
        return 'hurt'
    if not player:
        return 'guard' if state.get('enemy_windup',0) else 'punch' if state['enemy_attack_cooldown']>=114 else 'idle'
    kind=state.get('attack_kind','punch')
    threshold=20 if kind=='skill' else 23 if kind=='shot' else 12 if kind=='kick' else 8
    return kind if state['player_attack_cooldown']>=threshold else 'idle'


def character_body(state,player):
    pose=character_pose(state,player)
    if pose=='hurt': return HURT_BODY
    if pose=='guard': return GUARD_BODY
    if pose=='kick': return KICK_BODY
    if pose in ('punch','shot','skill'): return PUNCH_BODY
    return WALK_BODY_ROWS if (state['combat_frame']//5)%2 else BODY_ROWS


def character_rows(state,player):
    return character_head(state,player)+character_body(state,player)


def actor_screen_y(world_y):
    # Perspective fits the larger figure below the HUD at every floor depth.
    return 21+(world_y-15)*2//3


def draw_hurt_face(display,x,y):
    # One wide cartoon X; leave the lower face plain.
    scene_rect(display,x,y+3,10,4,1)
    for row in (0,2):
        scene_rect(display,x+1,y+3+row,2,1,0)
        scene_rect(display,x+7,y+3+row,2,1,0)
    scene_rect(display,x+3,y+4,4,1,0)


def draw_weapon(display,weapon,x,y,rightward,swing=False):
    if weapon is None: return
    def rect(offset,top,width,height,color=1):
        left=x+6+offset if rightward else x-offset-width
        scene_rect(display,left,top,width,height,color)
    if weapon==4:
        rect(1,y+1,5,2,0);rect(1,y+1,4,1);rect(1,y+2,1,3)
        if swing:
            rect(5,y-1,1,5);rect(4,y+1,3,1);rect(14,y+1,3,1)
    elif swing:
        length=8 if weapon==1 else 5
        for offset in range(length): rect(offset,y+3-offset//2,2,1)
        rect(0,y+1,1,4)
    else:
        length=9 if weapon==1 else 6
        rect(1,y+3-length,3,length+2,0)
        rect(2,y+3-length,1,length);rect(1,y+2,3,1);rect(2,y+3,1,2)


def draw_impact(display,x,y):
    scene_rect(display,x-4,y-4,9,9,0)
    # Six-frame star is drawn only from a real damage latch, never on a miss.
    for dx,dy,w,h in ((-3,0,7,1),(0,-3,1,7),(-2,-2,1,1),(2,-2,1,1),
                       (-2,2,1,1),(2,2,1,1)):
        scene_rect(display,x+dx,y+dy,w,h)


def fighter_positions(state,camera):
    px,ex=state['player_x']-camera,state['enemy_x']-camera
    if (state['active_enemy'] and abs(px-ex)<12
            and abs(state.get('player_y',28)-state.get('enemy_y',28))<=4):
        # Keep large heads distinct at contact without changing world hitboxes.
        left=max(2,min(52,(px+ex-12)//2))
        px,ex=(left,left+12) if px<ex else (left+12,left)
    return px,ex


def draw_hero_hair(display,region,x,y,rightward):
    def rect(offset,dy,width,height,color=1):
        left=x-2-offset-width if rightward else x+8+offset
        scene_rect(display,left,y+dy,width,height,color)
    rect(0,-6,5,12,0)
    if region==0:
        # Long tied hair; a small butterfly bow distinguishes the daenggi.
        rect(2,-2,1,8)
        for dy in (-4,-2):
            rect(0,dy,2,1);rect(3,dy,2,1)
        rect(2,-3,1,1)
    elif region==1:
        # A narrow long braid, alternating sides down to the shoulder.
        for row in range(8): rect(1+row%2,-3+row,1,1)
        rect(1,5,2,1)
    else:
        # Thick high ponytail, hanging as long as the other two styles.
        for offset,dy,width,height in ((0,-6,3,2),(1,-4,3,3),(2,-1,3,4),(3,3,2,3)):
            rect(offset,dy,width,height)


def draw_fighter(display,state,player,x,y):
    rightward=state['direction']=='R' if player else state['player_x']>state['enemy_x']
    pose=character_pose(state,player)
    hurt=pose=='hurt'
    # Visual recoil does not move the simulation hitbox.
    lean=(-2 if rightward else 2) if hurt else 0
    scene_rect(display,x-3,y-8,12,15,0)
    if player: draw_hero_hair(display,hero_region(state),x+lean,y,rightward)
    draw_rows(display,character_head(state,player),x-2+lean,y-7,10,not rightward,14)
    draw_rows(display,character_body(state,player),x-2,y+1,10,not rightward,14)
    if hurt: draw_hurt_face(display,x-2+lean,y-7)
    if player and state['equipped_armor'] is not None:
        scene_rect(display,x+1,y+2,4,2,1);scene_rect(display,x+2,y+2,2,1,0)
    weapon=state['equipped_weapon'] if player else None
    swinging=pose in ('punch','shot','skill')
    draw_weapon(display,weapon,x,y,rightward,swinging and (weapon!=4 or pose=='shot'))
    front=x+6 if rightward else x-5
    if pose=='kick':
        scene_rect(display,front,y+4,5,2);scene_rect(display,front+(3 if rightward else 0),y+3,2,3)
    elif swinging and weapon is None:
        scene_rect(display,front,y+2,5,2)
        scene_rect(display,front+(3 if rightward else 0),y+1,2,3)
    if pose=='skill':
        for offset in range(3):
            left=x+9+offset if rightward else x-5-offset
            scene_rect(display,left,y-1+offset,1,6-2*offset)
    if pose=='guard':
        scene_rect(display,x+2,y-10,1,2);scene_rect(display,x+2,y-7,1,1)
    if hurt:
        impact_x=x+8 if rightward else x-2
        draw_impact(display,impact_x,y+2)


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
    music = {'track': None, 'tick': 0}
    action = None
    title_tick = 0
    while action is None:
        action = title_frame(title_tick)
        title_tick = (title_tick+1)%120
        music = step_music(music, {'screen_state':'title'})
        if action in ('opening','ending'):
            music = play_scene(action,new_game_state(),music)
            action = None
    state = load_save_data() if action == 'load' else new_game_state()
    while True:
        previous = state
        state = step_frame(state)
        kind = None
        if previous['screen_state']=='country_select' and state['screen_state']=='safe' and state['progress']==0:
            kind = 'opening'
        elif state['progress'] > previous['progress'] and state['progress']%5==0:
            kind = 'ending' if state['progress']==GOAL_STAGES else 'event'
        if kind:
            music = play_scene(kind,state,music)
        music = step_audio(music,previous,state)


def play_scene(kind,state,music):
    # Menu previews reuse the real scenes without touching progress or save data.
    for frame in range(45 if kind=='event' else 90):
        music = step_music(music,dict(state,screen_state='clear' if kind=='ending' else 'title'))
        if cutscene_frame(kind,frame,state):
            break
    return music


# Original single-channel note patterns: rest is 0. No sampled music assets.
NOTES = (262,294,330,349,392,440,494,523)
TUNES = (b'\x01\x03\x05\x08\x05\x03\x02\x00',
         b'\x01\x03\x04\x05\x03\x02\x01\x00',
         b'\x01\x02\x03\x05\x06\x05\x03\x00',
         b'\x01\x02\x04\x05\x04\x02\x01\x00',
         b'\x01\x01\x05\x04\x03\x02\x05\x00',
         b'\x01\x03\x05\x08\x00\x08\x05\x08')


def music_track(state):
    screen = state['screen_state']
    track = None
    if screen in ('title','country_select'):
        track = 0
    elif screen=='clear' or (screen=='safe' and state['progress']>=GOAL_STAGES):
        track = 5
    elif screen in ('battle','safe','shop','shop_detail','equip','equip_detail'):
        track = 4 if screen=='battle' and state['progress']%5==4 else 1+stage_index(state)//5
    return track


def step_music(music,state):
    track=music_track(state)
    changed = track != music['track']
    if changed:
        thumby.audio.stop()
    tick = 0 if changed else music['tick']
    if track is None:
        return {'track':None,'tick':0}
    if track==5 and tick>=48:
        if tick==48:
            thumby.audio.stop()
        return {'track':track,'tick':49}
    if tick%6==0:
        note = TUNES[track][(tick//6)%8]
        if note:
            thumby.audio.play(NOTES[note-1],160)
        else:
            thumby.audio.stop()
    return {'track':track,'tick':tick+1 if track==5 else (tick+1)%48}


def sound_effect(previous,state):
    # Cues come from real state changes; refused actions and held buttons are silent.
    screen=state['screen_state']
    if screen in ('pause','defeat','clear') or state['progress']>=GOAL_STAGES:
        return None
    if screen=='battle' and previous['screen_state']=='battle':
        if state['HP']<previous['HP']:
            return (196,3)
        if state['enemy_hp']<previous['enemy_hp']:
            kind=state.get('attack_kind','punch')
            return (1047 if kind=='skill' else 880 if kind=='shot' else 392 if kind=='kick' else 659,2)
        if state['player_attack_cooldown']>previous['player_attack_cooldown']:
            kind=state.get('attack_kind','punch')
            return (1318,2) if kind=='skill' else (880,2) if kind=='shot' else (330,1)
    if state['progress']>previous['progress']:
        return (1047,3)
    if screen in ('shop','shop_detail') and state['money']<previous['money']:
        return (988,2)
    if state['save_status']!=previous['save_status']:
        if state['save_status']=='SAVED':
            return (784,2)
        if state['save_status']=='SAVE ERR':
            return (147,3)
    return None


def step_audio(music,previous,state):
    track=music_track(state)
    if track is None or track==5:
        return step_music(music,state)
    effect=sound_effect(previous,state)
    if effect:
        changed=track!=music['track']
        if changed:
            thumby.audio.stop()
        tick=0 if changed else music['tick']
        result={'track':track,'tick':(tick+1)%48}
        frequency,frames=effect
        thumby.audio.play(frequency,1000*frames//30)
        result['fx_left']=frames-1
        return result
    if music['track']==track and music.get('fx_left',0)>0:
        return dict(music,fx_left=music['fx_left']-1)
    if 'fx_left' in music and music['track']==track:
        # Resume at a note edge after the finite cue, without copying sound assets.
        music={'track':track,'tick':((music['tick']+5)//6*6)%48}
    return step_music(music,state)


def draw_scene_details(display,picture,frame,region):
    rows = SCENE_MOTIFS[region]
    for index,(x,y) in enumerate(SCENE_ANCHORS[picture]):
        phase = (frame//6+index*3)%8
        # A lantern sways; leaves/petals drift. Victory motifs gently twinkle.
        if picture==2 and phase in (2,3):
            continue
        offset = phase if phase<4 else 7-phase
        draw_rows(display,rows,x+offset,y+(phase//2 if region!=1 else 0),5,phase>=4)


def cutscene_frame(kind,frame,state):
    display = thumby.display
    display.fill(0)
    second = frame>=45
    picture = int(second) if kind=='opening' else 2+int(second) if kind=='ending' else 2
    display.blit(SCENE_BITMAPS[picture],0,0,72,32,-1,0,0)
    draw_scene_details(display,picture,frame,stage_index(state)//STAGES_PER_REGION)
    # A tiny travelling silhouette animates the static cuts without frame buffers.
    x = 8+(frame%45)//2 if picture in (0,1) else 48-(frame%45)//2
    display.drawFilledRectangle(x-2,17,13,15,0)
    draw_hero_hair(display,hero_region(state),x+2,25,picture!=3)
    draw_rows(display,character_head(state,True),x,18,10,picture==3)
    draw_rows(display,WALK_BODY_ROWS if (frame//5)%2 else BODY_ROWS,x,26,10,picture==3)
    if picture==1:
        for label,x,y in (('KR',3,18),('CN',30,2),('JP',57,18)):
            display.drawText(label,x,y,1)
    display.drawText('GO' if kind=='opening' else 'HOME' if picture==3 else 'CLEAR',0,33,1)
    display.drawText('A/B',54,33,1)
    display.update()
    # Sample both edges even when A skips, so a latched B cannot save next screen.
    a=thumby.buttonA.justPressed()
    b=thumby.buttonB.justPressed()
    thumby.buttonU.justPressed()
    thumby.buttonD.justPressed()
    return bool(a or b)


def title_frame(frame=0):
    display = thumby.display
    display.fill(0)
    draw_portrait(display,PORTRAIT_ROWS,1,0,frame)
    display.drawText('GROWTH', 24, 0, 1)
    display.drawText('U:INTRO', 24, 8, 1)
    display.drawText('D:ENDING', 24, 16, 1)
    display.drawText('A:NEW', 0, 23, 1)
    display.drawText('B:LOAD', 0, 33, 1)
    display.update()
    # Consume every menu edge once; unchosen buttons must not leak into the game.
    a=thumby.buttonA.justPressed()
    b=thumby.buttonB.justPressed()
    u=thumby.buttonU.justPressed()
    d=thumby.buttonD.justPressed()
    # Loading takes priority if both buttons are pressed; it cannot erase a save.
    if b:
        return 'load'
    if a:
        return 'new'
    if u:
        return 'opening'
    if d:
        return 'ending'
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
        display.drawText('YOUR COUNTRY' if not state['route'] else 'NEXT COUNTRY',0,0,1)
        choices = [region for region in range(3) if region not in state['route']]
        for row,region in enumerate(choices):
            y=10+row*10
            selected=row==state['menu_selection']
            if selected:
                display.drawFilledRectangle(0,y,72,8,1)
            display.drawText(('>' if selected else ' ')+('KOREA','CHINA','JAPAN')[region],0,y,0 if selected else 1)
        if not state['route']:
            # A full figure shows the long back hair; the real route stays empty.
            preview=dict(state,route=[choices[state['menu_selection']]])
            display.drawFilledRectangle(50,10,22,30,0)
            draw_fighter(display,preview,True,59,25)
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
        px,ex=fighter_positions(state,camera)
        actors = [(True,px,state.get('player_y',28))]
        if state['active_enemy']:
            actors.append((False,ex,state.get('enemy_y',28)))
        actors.sort(key=lambda actor: actor[2])
        for player,x,world_y in actors:
            draw_fighter(display,state,player,x,actor_screen_y(world_y))
    elif screen == 'pause':
        stats='HP'+str(state['HP'])+' AT'+str(state['attack'])+' DF'+str(state['defense'])
        if len(stats)>12:
            stats='H'+str(state['HP'])+' A'+str(state['attack'])+' D'+str(state['defense'])
        display.drawText(stats,0,0,1)
        index=stage_index(state)
        display.drawText(CITY_NAMES[index//5][index%5],0,10,1)
        cash=str(state['money']) if state['money']<1000 else str(min(999,state['money']//1000))+'k'
        display.drawText(status if status in ('SAVED','SAVE ERR') else '$'+cash+' '+stage_code(state),0,20,1)
        display.drawText('P'+str(state.get('potions',0)),60,20,1)
        healing='NONE' if not state.get('potions',0) else 'FULL' if state['HP']>=state['maxHP'] else 'HEAL'
        for row,label in enumerate(('BACK','SAVE',healing)):
            x=row*24
            selected=row==state['menu_selection']
            if selected:
                display.drawFilledRectangle(x,30,24,8,1)
            display.drawText(label,x,30,0 if selected else 1)
    elif screen in ('shop_detail', 'equip_detail'):
        item = state['menu_selection']
        names = ITEM_NAMES
        draw_portrait(display,portrait_rows(state,True),0,0)
        display.drawText(names[item], 20, 0, 1)
        display.drawText('P:'+str(get_item_price(item)), 20, 8, 1)
        effect = ITEM_EFFECTS[item]
        display.drawText(effect, 0, 16, 1)
        cash = str(state['money']) if state['money']<1000 else str(min(999,state['money']//1000))+'k'
        display.drawText('$'+cash, 72-6*(len(cash)+1), 16, 1)
        owned = 'Y' if item_owned(state,item) else 'N'
        equipped = item in (state['equipped_weapon'], state['equipped_armor'])
        if screen == 'shop_detail':
            action = purchase_status(state,item)
        else:
            action = 'BUY FIRST' if not item_owned(state,item) else ('A:REMOVE' if equipped else 'A:EQUIP')
        display.drawText(action, 0, 24, 1)
        if item==5:
            detail='QTY'+str(item_counter(state,item))+'/9'
        elif item in (6,7,8):
            detail='LV'+str(item_counter(state,item))+'/5'
        elif item==9:
            detail='UU+A READY' if item_owned(state,item) else 'BUY TO LEARN'
        else:
            detail='O:'+owned+' E:'+('Y' if equipped else 'N')
        display.drawText(detail, 0, 32, 1)
    elif screen == 'defeat':
        display.drawText('DEFEAT', 0, 0, 1)
        display.drawText('A:RETRY', 0, 20, 1)
    else:
        if screen == 'safe':
            choices = ('NEXT', 'SHOP', 'EQUIP', 'SAVE')
        elif screen == 'pause':
            choices = ('RESUME', 'SAVE')
        else:
            choices = ITEM_NAMES if screen=='shop' else ITEM_NAMES[:5]
        index=stage_index(state)
        header = CITY_NAMES[index//5][index%5] if screen == 'safe' else screen.upper()
        cash = str(state['money']) if state['money']<1000 else str(min(999,state['money']//1000))+'k'
        if screen in ('shop','equip'):
            header = 'AT'+str(state['attack'])+' DF'+str(state['defense'])
            if len(header)+len(cash)+1>12:
                header='A'+str(state['attack'])+' D'+str(state['defense'])
        if status in ('SAVED','SAVE ERR'):
            header = status
        display.drawText(header, 0, 0, 1)
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
                if screen in ('shop','equip') and item_owned(state,index):
                    label += '+'
                display.drawText(label, 0, 10+row*10, ink)
                if screen == 'shop':
                    counter=item_counter(state,index)
                    if counter is not None:
                        display.drawText(str(counter),42,10+row*10,ink)
                    display.drawText(str(get_item_price(index)), 54, 10+row*10, ink)
                elif screen == 'equip':
                    on = index in (state['equipped_weapon'],state['equipped_armor'])
                    display.drawText('ON' if on else ('OK' if item_owned(state,index) else '--'), 54, 10+row*10, ink)
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
