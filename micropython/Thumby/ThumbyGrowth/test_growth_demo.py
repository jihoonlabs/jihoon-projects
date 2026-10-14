"""Purchase/growth/save contracts and real title-to-scene entry points."""
import unittest
from copy import deepcopy
from unittest.mock import patch
import test_ThumbyGrowth as f
import ThumbyGrowth as game
from rules import (update_state,new_game_state,encode_save_data,decode_save_data,
                   is_valid_save_data,GROWTH_LIMIT)


class GrowthDemoTests(unittest.TestCase):
    def step(self,state,**keys):
        old=deepcopy(state)
        result=update_state(state,f.inputs(**keys))
        self.assertEqual(state,old)
        return result

    def buy(self,state,item):
        return self.step(dict(state,screen_state='shop',menu_selection=item),A=True)

    def test_all_purchases_are_reachable_and_scroll_within_three_rows(self):
        state=dict(new_game_state(),screen_state='shop')
        for selection in range(1,10):
            state=self.step(state,D=True)
            self.assertEqual(state['menu_selection'],selection)
            self.assertLess(selection-state['menu_scroll'],3)
        state=self.step(state,D=True)
        self.assertEqual((state['menu_selection'],state['menu_scroll']),(9,7))

    def test_pistol_is_owned_then_equipped_and_uses_long_low_damage_attack(self):
        state=self.buy(dict(new_game_state(),money=100),4)
        self.assertEqual((state['money'],state['gun_owned'],state['equipped_weapon']),(40,True,None))
        equipped=self.step(dict(state,screen_state='equip',menu_selection=4),A=True)
        self.assertEqual(equipped['equipped_weapon'],4)
        state=dict(equipped,screen_state='battle',player_x=16,enemy_x=48,enemy_y=28,
                   active_enemy=True,enemy_hp=10,enemy_defense=0,enemy_attack=2)
        shot=self.step(state,A=True)
        self.assertEqual((shot['enemy_hp'],shot['attack_kind']),(9,'shot'))
        wrong_lane=self.step(dict(state,enemy_y=15),A=True)
        self.assertEqual(wrong_lane['enemy_hp'],10)
        backwards=self.step(dict(state,direction='L'),A=True)
        self.assertEqual(backwards['enemy_hp'],10)

    def test_potion_purchase_and_pause_use_never_heal_or_charge_at_full_health(self):
        state=self.buy(dict(new_game_state(),money=30),5)
        self.assertEqual((state['money'],state['potions']),(15,1))
        full=self.step(dict(state,screen_state='pause',menu_selection=2),A=True)
        self.assertEqual(full['potions'],1)
        healed=self.step(dict(full,HP=2),A=True)
        self.assertEqual((healed['HP'],healed['potions'],healed['screen_state']),(8,0,'pause'))
        empty=self.step(healed,A=True)
        self.assertEqual(empty['HP'],8)
        capped=self.buy(dict(state,potions=9),5)
        self.assertEqual((capped['potions'],capped['money']),(9,15))

    def test_growth_caps_and_recalculated_stats_survive_equipment_and_battles(self):
        state=dict(new_game_state(),money=10000)
        for item,field in ((6,'hp_growth'),(7,'atk_growth'),(8,'def_growth')):
            for _ in range(GROWTH_LIMIT):
                state=self.buy(state,item)
            before=state['money']
            state=self.buy(state,item)
            self.assertEqual((state[field],state['money']),(GROWTH_LIMIT,before))
        self.assertEqual((state['maxHP'],state['attack'],state['defense']),(20,7,5))
        state.update(screen_state='safe',menu_selection=0,route=[0])
        battle=self.step(state,A=True)
        self.assertEqual((battle['maxHP'],battle['attack'],battle['defense']),(20,7,5))

    def test_skill_requires_purchase_two_edges_and_unexpired_window(self):
        base=f.state(screen_state='battle',enemy_x=28,enemy_hp=20,active_enemy=True,enemy_defense=0)
        def command(state):
            state=self.step(state,U=True)
            state=self.step(state)
            state=self.step(state,U=True)
            return self.step(state,A=True)
        self.assertEqual(command(base)['attack_kind'],'punch')
        owned=dict(base,skill_owned=True)
        skilled=command(owned)
        self.assertEqual((skilled['attack_kind'],skilled['enemy_hp']),('skill',14))
        held=self.step(owned,U_held=True)
        held=self.step(held,U_held=True,A=True)
        self.assertEqual(held['attack_kind'],'punch')
        expired=self.step(owned,U=True)
        for _ in range(13): expired=self.step(expired)
        expired=self.step(expired,U=True,A=True)
        self.assertEqual(expired['attack_kind'],'punch')
        paused=self.step(dict(owned,command_ready=12),A=True,B=True)
        self.assertEqual((paused['screen_state'],paused['command_ready']),('pause',0))

    def test_v3_roundtrip_and_old_v1_v2_defaults_and_invalid_growth(self):
        state=dict(new_game_state(),gun_owned=True,skill_owned=True,potions=3,
                   hp_growth=2,atk_growth=1,def_growth=3,equipped_weapon=4)
        data=encode_save_data(state)
        self.assertEqual(data['version'],3)
        loaded=decode_save_data(data)
        self.assertEqual(encode_save_data(loaded),data)
        self.assertEqual((loaded['HP'],loaded['maxHP'],loaded['attack'],loaded['defense']),(14,14,3,3))
        for version in (1,2):
            old=dict(version=version,money=35,progress=0,owned=[False]*4,
                     equipped_weapon=None,equipped_armor=None)
            if version==2:old['route']=[]
            restored=decode_save_data(old)
            self.assertEqual((restored['gun_owned'],restored['skill_owned'],restored['potions']),(False,False,0))
        for field,value in (('potions',10),('hp_growth',True),('atk_growth',6),('gun_owned',1)):
            self.assertFalse(is_valid_save_data(dict(data,**{field:value})))
        self.assertFalse(is_valid_save_data(dict(data,gun_owned=False)))

    def test_title_previews_return_without_loading_or_saving(self):
        f.TestAdapter.setUp(self)
        game.thumby=f.fake_thumby
        for key,kind in (('U','opening'),('D','ending')):
            button=getattr(game.thumby,'button'+key)
            button.justPressed.return_value=True
            self.assertEqual(game.title_frame(),kind)
            button.justPressed.return_value=False
            game.thumby.saveData.save.assert_not_called()
            game.thumby.saveData.getItem.assert_not_called()
        with patch.object(game,'title_frame',side_effect=['ending','new']), \
             patch.object(game,'play_scene',return_value={'track':None,'tick':0}) as scene, \
             patch.object(game,'step_music',side_effect=lambda m,s:m), \
             patch.object(game,'step_frame',side_effect=RuntimeError('halt')):
            with self.assertRaisesRegex(RuntimeError,'halt'):game.main_loop()
            self.assertEqual(scene.call_args.args[0],'ending')

    def test_new_items_render_and_scenes_animate_without_mutating_state(self):
        f.TestAdapter.setUp(self)
        game.thumby=f.fake_thumby
        for item in range(10):
            game.draw_game(f.state(screen_state='shop_detail',menu_selection=item,money=200))
        state=new_game_state();old=deepcopy(state)
        game.cutscene_frame('opening',0,state)
        initial=game.thumby.display.drawFilledRectangle.call_args_list[:]
        game.thumby.display.reset_mock()
        game.cutscene_frame('opening',20,state)
        self.assertNotEqual(initial,game.thumby.display.drawFilledRectangle.call_args_list)
        self.assertEqual(state,old)

    def test_portraits_share_face_and_collar_but_have_three_regional_heads(self):
        faces=[]
        for region in range(3):
            rows=game.portrait_rows(f.state(route=[region]),True)
            self.assertEqual(len(rows),16)
            self.assertEqual(rows[3:11],game.PORTRAIT_ROWS[3:11])
            self.assertEqual(rows[12:],game.PORTRAIT_ROWS[12:])
            faces.append(rows)
        self.assertEqual(len(set(faces)),3)

    def test_maximum_growth_text_and_portrait_rectangles_stay_inside_screen(self):
        f.TestAdapter.setUp(self);game.thumby=f.fake_thumby
        for screen in ('pause','shop_detail'):
            state=f.state(screen_state=screen,HP=20,maxHP=20,attack=11,defense=7,
                          money=10000000,menu_selection=9 if screen=='shop_detail' else 2)
            game.thumby.display.reset_mock();game.draw_game(state)
            for call in game.thumby.display.drawText.call_args_list:
                text,x,y,_=call.args
                self.assertLessEqual(x+len(str(text))*6,72)
                self.assertLessEqual(y+7,40)
            for call in game.thumby.display.drawFilledRectangle.call_args_list:
                x,y,w,h,_=call.args
                self.assertTrue(0<=x<x+w<=72 and 0<=y<y+h<=40)


if __name__=='__main__':unittest.main()
