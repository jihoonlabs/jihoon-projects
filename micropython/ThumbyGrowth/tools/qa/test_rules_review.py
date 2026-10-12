import unittest
from copy import deepcopy
from itertools import product
from rules import update_state
from test_rules import state, inputs, battle

class ReviewBoundaries(unittest.TestCase):
    def test_r_does_not_confirm_safe_or_pause(self):
        for screen,selection in product(('safe','pause'),(0,1)):
            result=update_state(state(screen_state=screen,menu_selection=selection),inputs(R=True))
            self.assertEqual(result['screen_state'],screen)
            self.assertFalse(result['save_requested'])

    def test_save_is_a_pulse_on_every_screen(self):
        for screen in ('safe','battle','pause','shop','equip','shop_detail','equip_detail','defeat'):
            result=update_state(state(screen_state=screen,save_requested=True),inputs(B=True))
            self.assertFalse(result['save_requested'])
            self.assertFalse(result['menu_r_held'])

    def test_detail_preserves_selection_without_owned(self):
        for screen in ('shop','equip'):
            original=state(screen_state=screen,menu_selection=3,menu_scroll=1)
            result=update_state(original,inputs(R=True))
            self.assertEqual(result['screen_state'],screen+'_detail')
            self.assertEqual((result['menu_selection'],result['menu_scroll']),(3,1))
            detailed=update_state(result,inputs(U=True,D=True,L=True,R=True))
            self.assertEqual(detailed,result)

    def test_retry_recalculates_equipment(self):
        result=update_state(state(screen_state='defeat',HP=0,attack=99,defense=99,
            owned=[False,True,False,True],equipped_weapon=1,equipped_armor=3,progress=1),inputs(A=True))
        self.assertEqual((result['attack'],result['defense'],result['HP'],result['combat_frame']),(6,2,10,0))

    def test_pause_limits_and_resume_time(self):
        original=battle(screen_state='pause',combat_frame=5,player_attack_cooldown=7,enemy_attack_cooldown=8)
        held=update_state(original,inputs(U=True,D=True))
        self.assertEqual(held,original)
        resumed=update_state(original,inputs(A=True))
        self.assertEqual(resumed['screen_state'],'battle')
        self.assertEqual((resumed['combat_frame'],resumed['player_attack_cooldown'],resumed['enemy_attack_cooldown']),(5,7,8))
        end=update_state(state(screen_state='pause',menu_selection=1),inputs(D=True))
        self.assertEqual((end['menu_selection'],end['menu_scroll']),(1,0))

    def test_b_priority_prevents_purchase(self):
        original=state(screen_state='shop_detail',money=80,menu_selection=1)
        result=update_state(original,inputs(A=True,B=True,R=True))
        self.assertEqual((result['screen_state'],result['money'],result['owned']),('shop',80,[False]*4))
        self.assertTrue(result['menu_r_held'])

    def test_even_enemy_motion_changes_attack_range_before_hit(self):
        original=battle(enemy_x=33,combat_frame=1)
        result=update_state(original,inputs(A=True))
        self.assertEqual((result['enemy_x'],result['enemy_hp'],result['combat_frame']),(32,4,2))
        result=update_state(battle(player_x=33,enemy_x=16,combat_frame=1,direction='L'),inputs(A=True))
        self.assertEqual((result['enemy_x'],result['enemy_hp']),(17,4))

    def test_valid_battle_positions_never_overlap_or_mutate(self):
        positions=(0,8,16,64,128,136)
        for player,enemy in product(positions,positions):
            if abs(player-enemy)<8: continue
            for frame in (0,1):
                for l,r,a,b in product((False,True),repeat=4):
                    original=battle(player_x=player,enemy_x=enemy,combat_frame=frame,enemy_hp=10)
                    before=deepcopy(original)
                    result=update_state(original,inputs(L=l,R=r,A=a,B=b))
                    self.assertEqual(original,before)
                    self.assertIsNot(result['owned'],original['owned'])
                    self.assertTrue(0<=result['player_x']<=136)
                    self.assertTrue(0<=result['enemy_x']<=136)
                    self.assertGreaterEqual(abs(result['player_x']-result['enemy_x']),8)
