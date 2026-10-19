"""The first country chooses identity; travelling never changes the hero's hair."""
from copy import deepcopy
from itertools import permutations
from unittest.mock import patch
import unittest
import test_ThumbyBrawlBase as f
import ThumbyBrawlBase as game
from rules import new_game_state,update_state,encode_save_data,decode_save_data


class HeroOriginTests(unittest.TestCase):
    def setUp(self):
        f.TestAdapter.setUp(self);game.thumby=f.fake_thumby

    def test_initial_country_inputs_choose_three_heads_without_changing_abilities(self):
        stats=[]
        for region in range(3):
            state=new_game_state()
            for _ in range(region): state=update_state(state,f.inputs(D=True))
            state=update_state(state,f.inputs(A=True))
            self.assertEqual(state['route'],[region])
            self.assertIs(game.character_head(state,True),game.HERO_HEAD)
            self.assertEqual(game.character_body(state,True),game.BODY_ROWS)
            stats.append((state['HP'],state['maxHP'],state['attack'],state['defense'],state['money']))
        self.assertEqual(game.HERO_HEAD[:2],(0xfc,0x1fe))
        self.assertEqual(stats,[(10,10,2,0,0)]*3)

    def test_six_routes_and_save_load_preserve_first_country_not_destination(self):
        for order in permutations(range(3)):
            for chapter in range(3):
                for city in (0,4):
                    state=f.state(progress=chapter*5+city,route=list(order[:chapter+1]))
                    before=deepcopy(state)
                    self.assertEqual(game.hero_region(state),order[0])
                    self.assertIs(game.character_head(state,True),game.HERO_HEAD)
                    if city==4:
                        self.assertIs(game.character_head(state,False),game.BOSS_HEADS[game.boss_variant(state)])
                    loaded=decode_save_data(encode_save_data(state))
                    self.assertIs(game.character_head(loaded,True),game.HERO_HEAD)
                    self.assertEqual(state,before)

    def test_national_hair_accents_mirror_around_the_same_body(self):
        original=(game.HERO_HEAD,game.BRAID_ROWS,game.HERO_FRINGE,game.PONY_ROWS);designs=[]
        for region in range(3):
            versions=[]
            for rightward in (True,False):
                game.thumby.display.reset_mock()
                game.draw_hero_hair(game.thumby.display,region,28,29,rightward)
                game.draw_hero_hair_accents(game.thumby.display,region,28,29,rightward)
                pixels=set()
                for call in game.thumby.display.drawFilledRectangle.call_args_list:
                    x,y,w,h,ink=call.args
                    self.assertTrue(0<=x<x+w<=72 and 14<=y<y+h<=40)
                    area={(px,py) for px in range(x,x+w) for py in range(y,y+h)}
                    if ink:pixels.update(area)
                    else:pixels.difference_update(area)
                versions.append(pixels)
            self.assertEqual({(61-x,y) for x,y in versions[0]},versions[1])
            self.assertTrue(versions[0])
            designs.append(frozenset(versions[0]))
        self.assertEqual(len(set(designs)),3)
        self.assertEqual((game.HERO_HEAD,game.BRAID_ROWS,game.HERO_FRINGE,game.PONY_ROWS),original)

    def test_korea_uses_a_topknot_china_a_queue_and_japan_a_ponytail(self):
        self.assertEqual(game.BRAID_ROWS,b'\x03\x03\x00'*3+b'\x03\x03')
        for region in range(3):
            for direction in ('R','L'):
                state=f.state(route=[region],direction=direction)
                with patch.object(game,'draw_rows',wraps=game.draw_rows) as rows:
                    game.draw_fighter(game.thumby.display,state,True,28,29)
                    braids=[c for c in rows.call_args_list if c.args[1] is game.BRAID_ROWS]
                    fringes=[c for c in rows.call_args_list if c.args[1] is game.HERO_FRINGE]
                    self.assertEqual(len(braids),1 if region==1 else 0)
                    self.assertEqual(len(fringes),1 if region==2 else 0)
                    if fringes:
                        self.assertEqual(fringes[0].args[4],2)
                        self.assertEqual(fringes[0].args[2],35 if direction=='R' else 25)
                game.thumby.display.reset_mock()
                game.draw_hero_hair_accents(game.thumby.display,region,28,29,direction=='R')
                rects=[call.args for call in game.thumby.display.drawFilledRectangle.call_args_list]
                if region==0:
                    self.assertIn((29,28,4,1,0),rects)
                    self.assertIn((29 if direction=='R' else 32,28,1,1,1),rects)
                    self.assertIn((29 if direction=='R' else 32,29,1,1,1),rects)
                    self.assertIn((27 if direction=='R' else 34,27,1,1,1),rects)
                    self.assertIn((26 if direction=='R' else 35,28,1,1,1),rects)
                    self.assertFalse(any(call[1]<27 and call[4]==1 for call in rects))
                elif region==1:
                    self.assertEqual(sum(1 for call in rects if call[2:4]==(1,1)),5)
                else:
                    self.assertTrue(any(call[2:4]==(2,1) for call in rects))

    def test_only_initial_country_menu_previews_different_hero_heads(self):
        for state,expected in ((new_game_state(),1),(f.state(progress=5,route=[2]),0)):
            with patch.object(game,'draw_rows',wraps=game.draw_rows) as rows:
                game.draw_game(state)
                heads=[c.args[1] for c in rows.call_args_list if c.args[1]==game.HERO_HEAD]
                self.assertEqual(len(heads),expected)
        texts=[c.args[0] for c in game.thumby.display.drawText.call_args_list]
        self.assertIn('YOUR COUNTRY',texts);self.assertIn('NEXT COUNTRY',texts)
        for region in range(3):
            state=new_game_state();state['menu_selection']=region;before=deepcopy(state)
            with patch.object(game,'draw_hero_hair',wraps=game.draw_hero_hair) as hair:
                game.draw_game(state)
                self.assertEqual(hair.call_args.args[1],region)
            self.assertEqual(state,before)


    def test_damage_and_cutscenes_use_the_origin_hair(self):
        state=f.state(screen_state='battle',progress=10,route=[2,0,1],active_enemy=True,
                      enemy_x=24,enemy_hp=30,enemy_attack=2,enemy_windup=1)
        hit=update_state(state,f.inputs())
        self.assertLess(hit['HP'],state['HP'])
        self.assertIs(game.character_head(hit,True),game.HERO_HEAD)
        with patch.object(game,'draw_hero_hair',wraps=game.draw_hero_hair) as hair:
            game.draw_game(hit)
            for kind in ('opening','event','ending'): game.cutscene_frame(kind,20,hit)
            self.assertEqual([c.args[1] for c in hair.call_args_list],[2]*4)

    def test_legacy_routes_keep_identity_without_new_save_fields(self):
        base=dict(money=0,progress=7,owned=[False]*4,equipped_weapon=None,equipped_armor=None)
        first=decode_save_data(dict(base,version=1))
        second=decode_save_data(dict(base,version=2,route=[2,0]))
        self.assertEqual(game.hero_region(first),0)
        self.assertEqual(game.hero_region(second),2)
        self.assertEqual(set(encode_save_data(second)),set(encode_save_data(new_game_state())))
        self.assertEqual(encode_save_data(second)['version'],3)

    def test_all_hairstyles_clip_at_edges_in_both_directions_and_during_hits(self):
        for region in range(3):
            for x in (0,32,66):
                for y in (15,33):
                    for direction in ('L','R'):
                        for flash in (0,6):
                            state=f.state(route=[region],direction=direction,player_hit_flash=flash,equipped_weapon=1)
                            before=deepcopy(state);game.thumby.display.reset_mock()
                            game.draw_fighter(game.thumby.display,state,True,x,game.actor_screen_y(y))
                            for c in game.thumby.display.drawFilledRectangle.call_args_list:
                                px,py,w,h,_=c.args
                                self.assertTrue(0<=px<px+w<=72 and 14<=py<py+h<=40)
                            self.assertLessEqual(game.thumby.display.drawFilledRectangle.call_count,100)
                            self.assertEqual(state,before)


if __name__=='__main__': unittest.main()
