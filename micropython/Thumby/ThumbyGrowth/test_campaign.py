import unittest

import campaign


def buttons(**pressed):
    keys=('L','R','A','B','U','D','L_tap','R_tap','U_tap','D_tap','U_held','D_held')
    return {key:key in pressed for key in keys}


class CampaignTests(unittest.TestCase):
    def test_country_and_city_are_player_selected(self):
        state=campaign.new_game_state()
        state=campaign.update(state,buttons(D=True))
        state=campaign.update(state,buttons(A=True))
        self.assertEqual(state['route'],[1])
        self.assertEqual(state['screen_state'],'city_select')
        state=campaign.update(state,buttons(D=True))
        state=campaign.update(state,buttons(A=True))
        self.assertEqual(state['current_city'],6)
        self.assertEqual(state['screen_state'],'explore')

    def test_each_city_has_multiple_maps_and_each_wave_is_capped(self):
        for region in range(3):
            for city in range(5):
                count=campaign.map_count(dict(current_city=region*5+city))
                self.assertGreaterEqual(count,2)
                self.assertLessEqual(count,5)
        state=campaign.new_game_state()
        state.update(route=[0],current_city=0,screen_state='explore',wave=2)
        self.assertLessEqual(len(campaign.spawn_wave(state)),3)

    def test_cleared_wave_respawns_after_delay_with_maximum_three(self):
        state=campaign.new_game_state()
        state.update(route=[0],current_city=0,screen_state='explore',
                     foes=[dict(x=24,y=28,hp=1,max_hp=1,attack=1,defense=0,
                                windup=0,cooldown=99,stun=0,flash=0,boss=False)])
        state=campaign.update(state,buttons(R=True,A=True))
        self.assertEqual(state['foes'],[])
        self.assertEqual(state['wave_delay'],campaign.WAVE_DELAY-1)
        for _ in range(campaign.WAVE_DELAY):
            state=campaign.update(state,buttons())
        self.assertTrue(state['foes'])
        self.assertLessEqual(len(state['foes']),3)

    def test_store_opens_at_building_and_returns_to_same_map(self):
        state=campaign.new_game_state()
        state.update(route=[0],current_city=0,map_index=2,screen_state='explore',player_x=104)
        state=campaign.update(state,buttons(U=True))
        self.assertEqual(state['screen_state'],'explore')
        self.assertEqual(state['player_y'],28)
        for _ in range(3):
            state=campaign.update(state,buttons(U=True,U_tap=True))
        self.assertEqual(state['player_y'],campaign.SHOP_DEPTH)
        state=campaign.update(state,buttons(U=True))
        self.assertEqual(state['screen_state'],'shop')
        state=campaign.update(state,buttons(B=True))
        self.assertEqual((state['screen_state'],state['current_city'],state['map_index']),('explore',0,2))

    def test_mouse_direction_tap_moves_three_pixels_and_hold_moves_one(self):
        state=campaign.new_game_state()
        state.update(route=[0],current_city=0,screen_state='explore',player_x=16)
        state=campaign.update(state,buttons(R=True,R_tap=True))
        self.assertEqual(state['player_x'],19)
        state=campaign.update(state,buttons(R=True))
        self.assertEqual(state['player_x'],20)

    def test_exploration_uses_wider_vertical_floor_lanes(self):
        state=campaign.new_game_state()
        state.update(route=[0],current_city=0,screen_state='explore',player_y=12,
                     foes=[dict(x=130,y=28,hp=20,max_hp=20,attack=0,defense=0,
                                windup=0,cooldown=999,stun=0,flash=0,boss=False)])
        state=campaign.update(state,buttons(D=True,D_held=True))
        self.assertEqual(state['player_y'],13)
        state.update(player_y=36)
        state=campaign.update(state,buttons(D=True,D_held=True))
        self.assertEqual(state['player_y'],36)
        state.update(player_y=12)
        state=campaign.update(state,buttons(U=True,U_held=True))
        self.assertEqual(state['player_y'],12)

    def test_campaign_save_accepts_the_expanded_floor_range(self):
        state=campaign.new_game_state()
        state.update(route=[0],current_city=0,player_y=12)
        self.assertEqual(campaign.decode_save(campaign.encode_save(state))['player_y'],12)
        state['player_y']=36
        self.assertEqual(campaign.decode_save(campaign.encode_save(state))['player_y'],36)

    def test_boss_strength_is_independent_of_country_and_tracks_build(self):
        a=campaign.new_game_state();a.update(route=[0],current_city=4,progress=4)
        b=campaign.new_game_state();b.update(route=[1],current_city=9,progress=4)
        self.assertEqual(campaign.spawn_boss(a),campaign.spawn_boss(b))
        a['attack']=12
        self.assertGreater(campaign.spawn_boss(a)['max_hp'],campaign.spawn_boss(b)['max_hp'])

    def test_campaign_save_round_trip_preserves_route_and_map(self):
        state=campaign.new_game_state()
        state.update(route=[2,0],completed_cities=[10,11,12],progress=3,
                     current_city=3,map_index=1,wave=7,boss_active=False)
        loaded=campaign.decode_save(campaign.encode_save(state))
        self.assertEqual((loaded['route'],loaded['current_city'],loaded['map_index'],loaded['wave']),
                         ([2,0],3,1,7))
        self.assertEqual(loaded['screen_state'],'explore')

    def test_pause_can_save_and_use_a_potion_without_returning_to_fight(self):
        state=campaign.new_game_state()
        state.update(route=[0],current_city=0,screen_state='pause',menu_selection=1)
        state=campaign.update(state,buttons(A=True))
        self.assertTrue(state['save_requested'])
        state.update(save_requested=False,menu_selection=2,potions=1,HP=4)
        state=campaign.update(state,buttons(A=True))
        self.assertEqual((state['HP'],state['potions'],state['screen_state']),(10,0,'pause'))

    def test_stationary_attack_hits_enemy_in_front(self):
        state=campaign.new_game_state()
        foe=dict(x=24,y=28,hp=20,max_hp=20,attack=1,defense=0,
                 windup=0,cooldown=99,stun=0,flash=0,boss=False)
        state.update(route=[0],current_city=0,screen_state='explore',
                     player_x=16,player_y=28,direction='R',foes=[foe],
                     HP=4,potions=1)
        state=campaign.update(state,buttons(A=True))
        self.assertLess(state['foes'][0]['hp'],20)
        self.assertEqual(state['attack_kind'],'punch')
        self.assertEqual((state['HP'],state['potions']),(4,1))

    def test_country_weapon_and_city_stock_vary_by_shop(self):
        expected=((4,'GUN'),(0,'SPEAR'),(1,'SWORD'))
        for region,(weapon,label) in enumerate(expected):
            state=campaign.new_game_state()
            state.update(route=[region],current_city=region*5,screen_state='shop',money=160)
            self.assertEqual(campaign.shop_catalog(state)[0],(weapon,label))
            state=campaign.update(state,buttons(A=True))
            self.assertEqual(state['equipped_weapon'],weapon)
        korea=campaign.shop_catalog(dict(current_city=0,route=[0]))
        busan=campaign.shop_catalog(dict(current_city=1,route=[0]))
        self.assertEqual([x[0] for x in korea],[4,6,2,5,9])
        self.assertEqual([x[0] for x in busan],[4,7,3,5,9])
        self.assertNotEqual(korea[1:4],busan[1:4])

    def test_spear_sword_and_gun_have_distinct_attack_ranges(self):
        for weapon,x,kind in ((0,34,'spear'),(1,29,'sword'),(4,60,'shot')):
            state=campaign.new_game_state()
            foe=dict(x=x,y=28,hp=20,max_hp=20,attack=1,defense=0,
                     windup=0,cooldown=99,stun=0,flash=0,boss=False)
            state.update(route=[0],current_city=0,screen_state='explore',
                         equipped_weapon=weapon,player_x=16,player_y=28,
                         direction='R',foes=[foe])
            state=campaign.update(state,buttons(A=True))
            self.assertEqual(state['attack_kind'],kind)
            self.assertLess(state['foes'][0]['hp'],20)
            self.assertTrue(state['foes'][0]['hp_seen'])

    def test_a_hit_reveals_only_the_target_enemy_health(self):
        state=campaign.new_game_state()
        near=dict(x=24,y=28,hp=20,max_hp=20,attack=1,defense=0,
                  windup=0,cooldown=99,stun=0,flash=0,boss=False,hp_seen=False)
        far=dict(x=50,y=28,hp=20,max_hp=20,attack=1,defense=0,
                 windup=0,cooldown=99,stun=0,flash=0,boss=False,hp_seen=False)
        state.update(route=[0],current_city=0,screen_state='explore',
                     player_x=16,player_y=28,direction='R',foes=[near,far])
        state=campaign.update(state,buttons(A=True))
        self.assertTrue(state['foes'][0]['hp_seen'])
        self.assertFalse(state['foes'][1]['hp_seen'])


if __name__=='__main__':
    unittest.main()

