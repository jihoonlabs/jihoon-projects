"""PC-only, silent showcase of real input frames; no injected game resources."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys

from render_preview import setup, gallery
from PIL import Image, ImageDraw, ImageFont


class Button:
    def __init__(self):
        self.held=False
        self.edge=False

    def pressed(self):
        return self.held

    def justPressed(self):
        value=self.edge
        self.edge=False
        return value


class MemorySave:
    def __init__(self):
        self.data={}
        self.writes=0

    def setName(self,name):
        assert name=='ThumbyGrowth'

    def setItem(self,key,value):
        self.data[key]=deepcopy(value)

    def getItem(self,key):
        return deepcopy(self.data[key])

    def hasItem(self,key):
        return key in self.data

    def save(self):
        self.writes+=1


class Replay:
    def __init__(self):
        self.game,self.display=setup()
        self.device=sys.modules['thumby']
        self.game.thumby=self.device
        for name in 'LRABUD': setattr(self.device,'button'+name,Button())
        self.memory=MemorySave()
        self.device.saveData=self.memory
        self.audio_calls=0
        self.device.audio=SimpleNamespace(play=self.sound,stop=lambda:None)
        from rules import new_game_state
        self.state=new_game_state()
        self.music={'track':None,'tick':0}
        self.frames=[]
        self.overview=[]
        self.inputs=[]
        self.purchases=[]
        self.wins=[]
        self.shown_regions=set()
        self.healed=False
        self.skill_used=False

    def sound(self,frequency,duration):
        assert 20<=frequency<=20000 and duration>0
        self.audio_calls+=1

    def buttons(self,keys):
        for name in 'LRABUD':
            button=getattr(self.device,'button'+name)
            button.edge=bool(keys.get(name,False)) and not button.held
            button.held=bool(keys.get(name+'_held',keys.get(name,False)))

    def capture(self,label,duration=150,overview=False):
        image=self.display.image.copy()
        self.frames.append((label,image,duration))
        if overview: self.overview.append((label,image))

    def scene(self,kind):
        self.buttons({})
        for frame in range(45 if kind=='event' else 90):
            self.game.cutscene_frame(kind,frame,self.state)
            if frame%6==0:
                self.capture(kind.title()+' / '+self.game.stage_code(self.state),200)

    def step(self,**keys):
        # Release repeated action/direction presses before another physical edge.
        if any(keys.get(n,False) and getattr(self.device,'button'+n).held for n in 'ABUD'):
            self.step()
        previous=self.state
        self.buttons(keys)
        self.inputs.append(keys)
        self.state=self.game.step_frame(previous)
        self.music=self.game.step_audio(self.music,previous,self.state)
        if self.state['screen_state']=='defeat':
            raise RuntimeError('Showcase player was defeated')
        if previous['screen_state']=='country_select' and self.state['screen_state']=='safe' and self.state['progress']==0:
            self.scene('opening')
        elif self.state['progress']>previous['progress']:
            self.wins.append(self.state['progress'])
            if self.state['progress']%5==0:
                self.scene('ending' if self.state['progress']==15 else 'event')
            self.game.draw_game(self.state)
        if (previous['screen_state']=='battle' and self.state['screen_state']=='battle'
                and self.state['enemy_hp']<previous['enemy_hp']
                and self.state['progress'] in (0,5,10) and self.state['progress'] not in self.shown_regions):
            self.shown_regions.add(self.state['progress'])
            self.capture(self.game.stage_code(self.state)+' / first landed hit',500,True)
        # A shortened visual replay: only selected fights and every sixth frame.
        if (self.state['screen_state']=='battle' and self.state['progress'] in (0,5,10,14)
                and self.state['combat_frame']%6==0):
            self.capture(self.game.stage_code(self.state)+' / ground combat',100)
        return self.state

    def menu(self,selection):
        while self.state['menu_selection']>selection: self.step(U=True)
        while self.state['menu_selection']<selection: self.step(D=True)

    def purchase(self,item,price):
        self.menu(1);self.step(A=True);self.menu(item)
        self.step(R=True)  # Show the actual detail screen before buying.
        before=self.state['money']
        self.capture('Buy / '+self.game.ITEM_NAMES[item],500)
        self.step(A=True)
        if self.state['money']!=before-price: raise RuntimeError('Purchase did not charge its price')
        self.purchases.append({'item':item,'price':price,'money_after':self.state['money']})
        self.capture('Bought / '+self.game.ITEM_NAMES[item],500,True)
        self.step(B=True);self.step(B=True)
        if item==4:
            self.menu(2);self.step(A=True);self.menu(4);self.step(A=True)
            if self.state['equipped_weapon']!=4: raise RuntimeError('Pistol not equipped')
            self.capture('Equipped / pistol',500)
            self.step(B=True)

    def fight(self):
        self.menu(0);self.step(A=True)
        shot=False
        for tick in range(2000):
            gap=self.state['enemy_x']-self.state['player_x']-6
            if (self.state['skill_owned'] and not self.skill_used and gap<=12
                    and self.state['player_attack_cooldown']<=1):
                for keys in ({'U':True,'U_held':True},{},{'U':True,'U_held':True},{},{'A':True}): self.step(**keys)
                if self.state['attack_kind']!='skill': raise RuntimeError('Skill not triggered')
                self.skill_used=True
                self.capture('Learned skill / UP UP A',500,True)
            elif self.state['HP']<self.state['maxHP'] and self.state['potions']:
                self.step(A=True,B=True);self.menu(2)
                before=self.state['HP'];self.step(A=True)
                if self.state['HP']<=before: raise RuntimeError('Potion did not heal')
                self.healed=True
                self.capture('Status / healing potion',500,True)
                self.step(B=True)
            else:
                shooting=(self.state['equipped_weapon']==4 and not shot and 0<=gap<=38
                          and self.state['player_attack_cooldown']<=1)
                self.step(R=gap>2,L=gap<0,A=shooting,B=not shooting and tick%2==0)
                if shooting: shot=True
            if self.state['screen_state']!='battle': return
        raise RuntimeError('Encounter exceeded 2000 input frames')

    def run(self):
        self.buttons({});self.game.title_frame(0)
        self.capture('Title / PC simulation',1000,True)
        self.buttons({'A':True})
        if self.game.title_frame(1)!='new': raise RuntimeError('New game title action failed')
        self.buttons({});self.game.draw_game(self.state)
        self.capture('Choose starting country',700)
        pending=[(4,60),(6,50),(7,60),(8,60),(5,15),(9,80)]
        for stage in range(15):
            if self.state['screen_state']=='country_select': self.step(A=True)
            self.fight()
            if self.state['progress']!=stage+1: raise RuntimeError('Progress skipped')
            if self.state['screen_state']=='country_select':
                self.capture('Choose next country',700)
                self.step(A=True)
            while pending and self.state['money']>=pending[0][1] and stage<14:
                self.purchase(*pending.pop(0))
            if stage==6:
                self.menu(3);self.step(A=True)
                saved=self.game.encode_save_data(self.state)
                self.capture('Save / mid-game',700)
                self.state=self.game.load_save_data()
                if self.game.encode_save_data(self.state)!=saved: raise RuntimeError('Save round trip changed data')
                self.game.draw_game(self.state)
                self.capture('Load / same progress',700)
        self.capture('Quest clear / earned money',1000,True)
        self.step(B=True)
        saved=self.game.encode_save_data(self.state)
        restored=self.game.load_save_data()
        if self.game.encode_save_data(restored)!=saved: raise RuntimeError('Ending save changed data')
        self.state=restored;self.step(A=True)
        self.capture('New game / country selection',800,True)
        if pending or not self.healed or not self.skill_used or saved['money']!=45:
            raise RuntimeError('Showcase missed economy, skill or healing')
        if self.memory.writes!=2: raise RuntimeError('Unexpected save count')
        root=Path(__file__).resolve().parents[1]
        return {'kind':'silent PC simulation; selected frames, not device capture',
                'source_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest()
                                 for n in ('ThumbyGrowth.py','rules.py','scene_art.py')},
                'input_frames':len(self.inputs),'input_sha256':hashlib.sha256(json.dumps(self.inputs,sort_keys=True).encode()).hexdigest(),
                'cleared_stages':self.wins,'route':saved['route'],'earned_money':370,
                'purchases':self.purchases,'final_money':saved['money'],
                'skill_used':self.skill_used,'healed':self.healed,'save_load_round_trips':2,
                'restart_progress':self.state['progress'],'audio_api_calls':self.audio_calls,
                'selected_visual_frames':len(self.frames)}

    def export(self,path,overview):
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
        frames=[]
        for label,image,_ in self.frames:
            canvas=Image.new('RGB',(464,300),'#0b1120');draw=ImageDraw.Draw(canvas)
            draw.text((16,10),'ThumbyGrowth / PC replay / silent highlights',font=font,fill='white')
            canvas.paste(image.convert('RGB').resize((432,240),Image.Resampling.NEAREST),(16,36))
            draw.text((16,280),label,font=font,fill='#cbd5e1');frames.append(canvas)
        frames[0].save(path,save_all=True,append_images=frames[1:],
                       duration=[f[2] for f in self.frames],loop=0,optimize=True)
        gallery(self.overview,overview,3)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--overview',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    replay=Replay();report=replay.run()
    replay.export(args.output,args.overview)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
