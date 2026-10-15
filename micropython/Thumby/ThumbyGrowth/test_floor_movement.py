import unittest, sys, json, random
from copy import deepcopy
from unittest.mock import Mock
sys.modules['thumby'] = Mock()
import ThumbyGrowth as game
from rules import update_state, decode_save_data, encode_save_data

def state(**kw):
    s=decode_save_data(dict(version=1,money=0,progress=0,owned=[False]*4,equipped_weapon=None,equipped_armor=None))
    s.update(kw)
    return s

def keys(**kw):
    k=dict.fromkeys(('L','R','U','D','A','B','U_held','D_held'),False)
    k.update(kw)
    return k

class FloorTests(unittest.TestCase):
    def test_start_and_retry_reset_floor(self):
        for screen in ('safe','defeat'):
            s=update_state(state(screen_state=screen,player_y=15,enemy_y=33),keys(A=True))
            self.assertEqual((s['screen_state'],s['player_y'],s['enemy_y']),('battle',28,28))
    def test_held_vertical_movement_and_release(self):
        s=state(screen_state='battle')
        for _ in range(5):s=update_state(s,keys(U_held=True))
        self.assertEqual(s['player_y'],23)
        s=update_state(s,keys());self.assertEqual(s['player_y'],23)
        for _ in range(5):s=update_state(s,keys(D_held=True))
        self.assertEqual(s['player_y'],28)
    def test_world_bounds_all_axes(self):
        s=state(screen_state='battle')
        for _ in range(160):s=update_state(s,keys(R=True,D_held=True))
        self.assertEqual((s['player_x'],s['player_y']),(138,33))
        for _ in range(160):s=update_state(s,keys(L=True,U_held=True))
        self.assertEqual((s['player_x'],s['player_y']),(0,15))
    def test_opposite_inputs_cancel(self):
        s=state(screen_state='battle')
        t=update_state(s,keys(L=True,R=True,U_held=True,D_held=True))
        self.assertEqual((t['player_x'],t['player_y']),(16,28))
    def test_menu_uses_edges_not_held(self):
        s=state()
        for _ in range(5):s=update_state(s,keys(D_held=True))
        self.assertEqual(s['menu_selection'],0)
        self.assertEqual(update_state(s,keys(D=True))['menu_selection'],1)
    def test_body_collision_six_by_seven(self):
        s=state(screen_state='battle',active_enemy=True,enemy_x=22,enemy_y=28,enemy_hp=6)
        t=update_state(s,keys(R=True));self.assertEqual(t['player_x'],16)
        s.update(player_y=21,enemy_x=16)
        t=update_state(s,keys(D_held=True));self.assertEqual(t['player_y'],21)
    def test_pass_on_separate_lane(self):
        s=state(screen_state='battle',active_enemy=True,enemy_x=22,enemy_y=28,player_y=15,enemy_hp=6)
        t=update_state(s,keys(R=True));self.assertEqual(t['player_x'],17)
    def test_enemy_follows_both_axes(self):
        s=state(screen_state='battle',active_enemy=True,enemy_x=100,enemy_y=33,player_y=15,enemy_hp=6)
        for _ in range(2):s=update_state(s,keys())
        self.assertEqual((s['enemy_x'],s['enemy_y']),(99,32))
    def test_player_hit_height_threshold_both_directions(self):
        for direction,x in (('R',22),('L',10)):
            for dy,damage in ((0,2),(3,2),(4,0)):
                s=state(screen_state='battle',active_enemy=True,enemy_x=x,enemy_y=28-dy,enemy_hp=6,direction=direction,enemy_attack_cooldown=20)
                t=update_state(s,keys(A=True))
                self.assertEqual(t['enemy_hp'],6-damage)
    def test_enemy_hit_height_and_cooldown(self):
        for dy,hp in ((0,8),(3,8),(4,10)):
            s=state(screen_state='battle',active_enemy=True,enemy_x=22,enemy_y=28-dy,enemy_hp=6,enemy_attack=2,enemy_windup=1)
            t=update_state(s,keys());self.assertEqual(t['HP'],hp)
            if dy==0:
                self.assertEqual(t['enemy_attack_cooldown'],120)
                self.assertEqual(update_state(t,keys())['HP'],8)
    def test_pause_freezes_combat(self):
        s=state(screen_state='pause',active_enemy=True,enemy_x=22,enemy_hp=6)
        t=update_state(s,keys(R=True,D_held=True))
        self.assertEqual((t['combat_frame'],t['player_x'],t['player_y'],t['HP']),(0,16,28,10))
    def test_victory_defeat_and_reward_once(self):
        s=state(screen_state='battle',active_enemy=True,enemy_x=22,enemy_hp=2)
        t=update_state(s,keys(A=True))
        self.assertEqual((t['screen_state'],t['money'],t['progress']),('safe',20,1))
        self.assertEqual(update_state(t,keys())['money'],20)
        s.update(HP=1,enemy_attack=2,enemy_windup=1)
        self.assertEqual(update_state(s,keys())['screen_state'],'defeat')
    def test_shop_equip_and_save_roundtrip(self):
        s=state(screen_state='shop',money=120)
        s=update_state(s,keys(A=True));self.assertEqual((s['money'],s['owned'][0]),(80,True))
        s=update_state(s,keys(A=True));self.assertEqual(s['money'],80)
        s.update(screen_state='equip')
        s=update_state(s,keys(A=True));self.assertEqual(s['attack'],4)
        game.thumby.saveData.reset_mock();memory={}
        game.thumby.saveData.setItem.side_effect=lambda k,v:memory.update({k:v})
        game.thumby.saveData.hasItem.side_effect=lambda k:k in memory
        game.thumby.saveData.getItem.side_effect=lambda k:memory[k]
        self.assertEqual(game.save_game(s),'SAVED')
        t=game.load_save_data()
        self.assertEqual((t['money'],t['attack'],t['equipped_weapon']),(80,4,0))
        self.assertEqual((t['player_y'],t['current_city'],t['screen_state']),(28,None,'city_select'))
        self.assertEqual(game.campaign.encode_save(t)['money'],80)
    def test_update_does_not_mutate_input(self):
        s=state(screen_state='battle');before=deepcopy(s)
        update_state(s,keys(R=True,U_held=True,A=True));self.assertEqual(s,before)
    def test_adapter_held_input(self):
        for name in ('L','R','U','D','A','B'):
            button=getattr(game.thumby,'button'+name)
            button.pressed.return_value=True;button.justPressed.return_value=False
        k=game.handle_inputs()
        self.assertTrue(k['U_held'] and k['D_held'] and k['L'] and k['R'])
        self.assertFalse(k['U'] or k['D'] or k['A'] or k['B'])
    def test_hud_and_all_render_bounds(self):
        for px in (0,16,70,138):
            for ex in (0,32,71,138):
                for py,ey in ((15,33),(33,15),(28,28)):
                    s=state(screen_state='battle',active_enemy=True,player_x=px,enemy_x=ex,player_y=py,enemy_y=ey,enemy_hp=6,player_attack_cooldown=15)
                    game.thumby.display.reset_mock();before=deepcopy(s);game.draw_game(s)
                    self.assertEqual(s,before)
                    texts=[c.args[0] for c in game.thumby.display.drawText.call_args_list]
                    self.assertEqual(texts[-2:],['10','6'])
                    self.assertTrue(all(label in ('SHOP','10','6') for label in texts))
                    for c in game.thumby.display.drawFilledRectangle.call_args_list:
                        x,y,w,h,_=c.args
                        self.assertTrue(0<=x<x+w<=72 and 0<=y<y+h<=40)
    def test_random_play_has_no_overlap_or_escape(self):
        rng=random.Random(19)
        s=state(screen_state='battle',active_enemy=True,enemy_x=100,enemy_y=15,enemy_hp=1000,HP=1000,maxHP=1000)
        for _ in range(3000):
            s=update_state(s,keys(**{k:bool(rng.randrange(2)) for k in ('L','R','U_held','D_held')}))
            self.assertTrue(0<=s['player_x']<=138 and 15<=s['player_y']<=33)
            self.assertTrue(0<=s['enemy_x']<=138 and 15<=s['enemy_y']<=33)
            self.assertFalse(abs(s['player_x']-s['enemy_x'])<6 and abs(s['player_y']-s['enemy_y'])<7)

if __name__=='__main__':unittest.main(verbosity=2)
