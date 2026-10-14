"""Render actual game helpers on a CPython display shim; never a device capture."""
import argparse
import importlib
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace, ModuleType
from PIL import Image, ImageDraw, ImageFont

FONT={
'A':[126,17,17,17,126],'B':[127,73,73,73,54],'C':[62,65,65,65,34],
'D':[127,65,65,34,28],'E':[127,73,73,73,65],'F':[127,9,9,9,1],
'G':[62,65,73,73,122],'H':[127,8,8,8,127],'I':[0,65,127,65,0],
'J':[32,64,65,63,1],'K':[127,8,20,34,65],'L':[127,64,64,64,64],
'M':[127,2,12,2,127],'N':[127,4,8,16,127],'O':[62,65,65,65,62],
'P':[127,9,9,9,6],'Q':[62,65,81,33,94],'R':[127,9,25,41,70],
'S':[70,73,73,73,49],'T':[1,1,127,1,1],'U':[63,64,64,64,63],
'V':[31,32,64,32,31],'W':[63,64,56,64,63],'X':[99,20,8,20,99],
'Y':[7,8,112,8,7],'Z':[97,81,73,69,67],
'0':[62,81,73,69,62],'1':[0,66,127,64,0],'2':[66,97,81,73,70],
'3':[33,65,69,75,49],'4':[24,20,18,127,16],'5':[39,69,69,69,57],
'6':[60,74,73,73,48],'7':[1,113,9,5,3],'8':[54,73,73,73,54],
'9':[6,73,73,41,30],':':[0,54,54,0,0],'/':[32,16,8,4,2],
'$':[36,42,127,42,18],'>':[0,65,34,20,8],'-':[8]*5,' ':[0]*5}


class Display:
    def __init__(self):self.fill(0)
    def fill(self,color):
        self.image=Image.new('1',(72,40),color);self.draw=ImageDraw.Draw(self.image)
    def drawFilledRectangle(self,x,y,w,h,color):
        if w>0 and h>0:self.draw.rectangle((x,y,x+w-1,y+h-1),fill=color)
    def drawText(self,text,x,y,color):
        for i,ch in enumerate(str(text)):
            for col,mask in enumerate(FONT.get(ch.upper(),[0]*5)):
                for row in range(7):
                    if mask&(1<<row):self.draw.point((x+i*6+col,y+row),fill=color)
    def blit(self,data,x,y,w,h,key,mx,my):
        for cy in range(h):
            for cx in range(w):
                sx=w-1-cx if mx else cx;sy=h-1-cy if my else cy
                bit=(data[(sy//8)*w+sx]>>(sy%8))&1
                if bit!=key and 0<=x+cx<72 and 0<=y+cy<40:
                    self.draw.point((x+cx,y+cy),fill=bit)
    def update(self):pass
    def setFPS(self,fps):pass


def setup():
    display=Display();device=SimpleNamespace(display=display)
    for name in 'LRABUD':
        setattr(device,'button'+name,SimpleNamespace(pressed=lambda:False,justPressed=lambda:False))
    sys.modules['thumby']=device
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    return importlib.import_module('ThumbyGrowth'),display


def gallery(frames,path,columns=2):
    rows=(len(frames)+columns-1)//columns
    canvas=Image.new('RGB',(columns*325+25,rows*215+90),'#0b1120');d=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    d.text((15,12),'ThumbyGrowth / original 72 x 40 pixels',font=font,fill='white')
    d.text((15,42),'Actual game code; simulated font; nearest-neighbour enlargement.',font=font,fill='#94a3b8')
    for i,(label,image) in enumerate(frames):
        x=15+(i%columns)*325;y=80+(i//columns)*215
        d.text((x,y),label,font=font,fill='#cbd5e1')
        canvas.paste(image.convert('RGB').resize((288,160),Image.Resampling.NEAREST),(x,y+27))
    canvas.save(path)


def scene_animation(game,display,path):
    # PC documentation only: the device still stores four static 72x32 cuts.
    from rules import new_game_state
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    frames=[]
    for frame in range(0,90,6):
        canvas=Image.new('RGB',(650,700),'#0b1120');draw=ImageDraw.Draw(canvas)
        draw.text((15,12),'Opening / ending: actual helpers, PC simulation',font=font,fill='white')
        for region,country in enumerate(('Korea / leaves','China / lanterns','Japan / petals')):
            state=new_game_state();state['route']=[region]
            for column,kind in enumerate(('opening','ending')):
                game.cutscene_frame(kind,frame,state)
                x=15+column*325;y=48+region*215
                draw.text((x,y),country+' / '+kind,font=font,fill='#cbd5e1')
                canvas.paste(display.image.convert('RGB').resize((288,160),Image.Resampling.NEAREST),(x,y+27))
        frames.append(canvas)
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=200,loop=0,optimize=True)


def title_animation(game,display,path):
    frames=[]
    for frame in (0,116):
        game.title_frame(frame)
        frames.append(display.image.convert('RGB').resize((288,160),Image.Resampling.NEAREST))
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=[3860,140],loop=0,optimize=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    parser.add_argument('--scenes',required=True)
    parser.add_argument('--animation',help='PC-only GIF of the real scene helper')
    parser.add_argument('--title-animation',help='PC-only GIF of the frame-driven title blink')
    args=parser.parse_args()
    game,display=setup()
    from rules import new_game_state,decode_save_data
    state=decode_save_data(dict(version=2,money=0,progress=0,route=[0],
        owned=[False]*4,equipped_weapon=None,equipped_armor=None))
    state.update(screen_state='battle',player_x=28,enemy_x=49,active_enemy=True,enemy_hp=6)
    frames=[]
    game.title_frame();frames.append(('Title / scene previews',display.image.copy()))
    for region,label in enumerate(('Korea / shared fighter','China / shared fighter','Japan / shared fighter')):
        state.update(progress=4,route=[region],enemy_hp=16)
        game.draw_game(state);frames.append((label,display.image.copy()))
    state.update(screen_state='shop',menu_selection=9,menu_scroll=7,money=200)
    game.draw_game(state);frames.append(('Shop / growth and skill',display.image.copy()))
    state.update(screen_state='shop_detail',menu_selection=4)
    game.draw_game(state);frames.append(('Merchant / shared portrait',display.image.copy()))
    state.update(screen_state='pause',menu_selection=2,potions=2)
    game.draw_game(state);frames.append(('Status / use healing',display.image.copy()))
    cuts=[]
    for kind,frame,label in (('opening',0,'Departure'),('opening',60,'Three destinations'),
                             ('ending',0,'Victory'),('ending',60,'Return home')):
        game.cutscene_frame(kind,frame,state)
        cuts.append((label,display.image.copy()))
    gallery(cuts,args.scenes)
    gallery(frames+cuts,args.output,3)
    if args.animation:
        scene_animation(game,display,args.animation)
    if args.title_animation:
        title_animation(game,display,args.title_animation)
