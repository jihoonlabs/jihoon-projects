"""Controlled equipment/attack setups, real damage rules, silent slowed PC replay."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont
from render_preview import setup, gallery


def render(animation,overview,report):
    game,display=setup();game.thumby=sys.modules['thumby']
    from rules import new_game_state,encode_save_data,decode_save_data,update_state
    frames=[];stills=[];results=[]
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)

    def capture(label,duration):
        canvas=Image.new('RGB',(464,300),'#0b1120');draw=ImageDraw.Draw(canvas)
        draw.text((16,10),'PC simulation / slowed combat / silent',font=font,fill='white')
        canvas.paste(display.image.convert('RGB').resize((432,240),Image.Resampling.NEAREST),(16,36))
        draw.text((16,280),label,font=font,fill='#cbd5e1')
        frames.append((canvas,duration))

    def state(weapon=None,player_hit=False):
        start=new_game_state()
        if weapon is not None:
            if weapon==4: start['gun_owned']=True
            else: start['owned'][weapon]=True
            start['equipped_weapon']=weapon
        start=decode_save_data(encode_save_data(start))
        start.update(route=[0],screen_state='battle',player_x=28,enemy_x=36 if player_hit else 44,
                     player_y=28,enemy_y=28,active_enemy=True,enemy_hp=30,enemy_attack=2,
                     enemy_attack_cooldown=0 if player_hit else 120,enemy_windup=6 if player_hit else 0)
        return start

    for weapon,name in ((None,'Bare hands'),(0,'Blade'),(1,'Sword'),(4,'Pistol')):
        value=state(weapon);game.draw_game(value)
        label=name+' / idle'
        stills.append((label,display.image.copy()));capture(label,1000)
    for name,weapon,button,victim in (('Punch',None,'A','enemy'),('Kick',None,'B','enemy'),
                                    ('Sword swing',1,'A','enemy'),('Pistol shot',4,'A','enemy'),
                                    ('Player takes a hit',None,None,'player')):
        value=state(weapon,victim=='player');before=dict(value)
        seen_hit=False
        for tick in range(30):
            keys=dict.fromkeys(('L','R','A','B','U','D','U_held','D_held','A_held','B_held'),False)
            if tick==6 and button: keys[button]=True
            value=update_state(value,keys)
            game.draw_game(value)
            hit=value['player_hit_flash' if victim=='player' else 'enemy_hit_flash']>0
            if hit and not seen_hit:
                stills.append((name.replace('Player takes a hit','Player').replace('Sword swing','Sword').replace('Pistol shot','Shot')+' / hit',display.image.copy()));seen_hit=True
            capture(name+(' / X eyes: hit' if hit else ''),60)
        field='HP' if victim=='player' else 'enemy_hp'
        damage=before[field]-value[field]
        if not seen_hit or damage<=0: raise RuntimeError(name+' did not cause real damage')
        results.append({'action':name,'victim':victim,'damage':damage})
    gallery(stills,overview,3)
    frames[0][0].save(animation,save_all=True,append_images=[i for i,_ in frames[1:]],
                      duration=[d for _,d in frames],loop=0,optimize=True)
    root=Path(__file__).resolve().parents[1]
    data={'kind':__doc__,'clips':results,'native_pixels':[72,40],
          'source_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest()
                           for n in ('ThumbyGrowth.py','rules.py','scene_art.py')}}
    report.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--animation',type=Path,required=True)
    parser.add_argument('--overview',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();render(args.animation,args.overview,args.report)
