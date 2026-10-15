"""Free country order, city identity, route persistence and hand/foot controls."""
from copy import deepcopy
from itertools import permutations
import unittest

import test_ThumbyGrowth as fixtures
import test_game_completion as completion
import ThumbyGrowth as game
import campaign
from rules import (new_game_state, update_state, encode_save_data, decode_save_data,
                   is_valid_save_data, stage_index, CITY_NAMES, CITY_MAP_COUNTS,
                   MAX_ACTIVE_ENEMIES)


class CountryRouteTests(unittest.TestCase):
    setUp = completion.GameCompletionTests.setUp
    frame = completion.GameCompletionTests.frame
    finish_fight = completion.GameCompletionTests.finish_fight
    buy_and_equip = completion.GameCompletionTests.buy_and_equip

    def choose(self, state, country):
        self.assertEqual(state['screen_state'],'country_select')
        choices=[r for r in range(3) if r not in state['route']]
        for _ in range(choices.index(country)):
            state=self.frame(state,D=True)
        state=self.frame(state,A=True)
        self.assertEqual(state['screen_state'],'safe')
        self.assertEqual(state['route'][-1],country)
        return state

    def test_all_six_country_orders_complete_with_shopping_and_saved_choices(self):
        for order in permutations((0,1,2)):
            with self.subTest(order=order):
                state=campaign.new_game_state()
                for country in order:
                    options=[r for r in range(3) if r not in state['route']]
                    state['menu_selection']=options.index(country)
                    state=campaign.update(state,fixtures.inputs(A=True))
                    self.assertEqual(state['route'],list(order[:len(state['route'])]))
                    for _ in range(5):
                        state['menu_selection']=0
                        state=campaign.update(state,fixtures.inputs(A=True))
                        self.assertEqual(state['current_city']//5,country)
                        state['foes']=[]
                        state=campaign._finish_city(state)
                    self.assertEqual(state['screen_state'],'country_select' if len(state['route'])<3 else 'ending')
                    if len(state['route'])<3:
                        restored=campaign.decode_save(campaign.encode_save(state))
                        self.assertEqual(restored['route'],list(order[:len(state['route'])]))
                self.assertEqual((state['progress'],state['route']),(15,list(order)))

    def test_start_selection_save_and_reload_do_not_choose_a_country(self):
        state=self.frame(new_game_state(),B=True)
        self.assertEqual(state['screen_state'],'country_select')
        self.assertEqual(state['route'],[])
        restored=game.load_save_data()
        self.assertEqual(restored['screen_state'],'country_select')
        self.assertEqual(restored['route'],[])

    def test_cleared_country_is_not_offered_and_choice_does_not_mutate_input(self):
        state=decode_save_data(dict(version=2,money=80,progress=5,route=[2],
            owned=[True,False,False,False],equipped_weapon=0,equipped_armor=None))
        game.thumby.display.reset_mock()
        game.draw_game(state)
        texts=[call.args[0] for call in game.thumby.display.drawText.call_args_list]
        self.assertIn('>KOREA',texts)
        self.assertIn(' CHINA',texts)
        self.assertFalse(any('JAPAN' in text for text in texts))
        before=deepcopy(state)
        chosen=update_state(state,fixtures.inputs(D=True,A=True))
        self.assertEqual(state,before)
        self.assertEqual(chosen['route'],[2,1])
        self.assertEqual(stage_index(chosen),5)
        self.assertEqual((chosen['money'],chosen['attack']),(80,4))

    def test_legacy_saves_migrate_with_clear_boundaries_waiting_for_choice(self):
        for progress,route,screen in (
            (0,[0],'safe'),(5,[0],'country_select'),(7,[0,1],'safe'),
            (10,[0,1],'country_select'),(15,[0,1,2],'safe'),(42,[0,1,2],'safe'),
        ):
            payload=dict(version=1,money=70,progress=progress,owned=[True,False,True,False],
                         equipped_weapon=0,equipped_armor=2)
            before=deepcopy(payload)
            restored=decode_save_data(payload)
            self.assertEqual(payload,before)
            self.assertEqual(restored['route'],route)
            self.assertEqual(restored['screen_state'],screen)
            self.assertEqual((restored['money'],restored['attack'],restored['defense']),(70,4,1))
            upgraded=encode_save_data(restored)
            self.assertEqual(upgraded['version'],3)
            self.assertEqual(encode_save_data(decode_save_data(upgraded)),upgraded)

    def test_invalid_route_records_are_rejected(self):
        base=encode_save_data(new_game_state())
        invalid=[dict(base,route=[True]),dict(base,route=[3]),dict(base,route=[{}]),
                 dict(base,route=[0,0]),dict(base,route=[0,1,2,0]),dict(base,route=(0,)),
                 dict(base,progress=1,route=[]),dict(base,progress=5,route=[]),
                 dict(base,progress=6,route=[2]),dict(base,progress=16,route=[0,1,2]),
                 dict(base,progress=15,route=[0,1]),dict(base,route=[0,1]),dict(base,extra=1)]
        for value in invalid:
            with self.subTest(value=value):
                self.assertFalse(is_valid_save_data(value))
                self.assertIsNone(decode_save_data(value))

    def test_invalid_state_cannot_overwrite_saved_data(self):
        good=new_game_state()
        game.save_game(good)
        memory=deepcopy(self.memory)
        bad=deepcopy(good)
        bad['progress']=6
        self.assertEqual(game.save_game(bad),'SAVE ERR')
        self.assertEqual(self.memory,memory)

    def test_fifteen_city_names_fit_device_and_match_city_index(self):
        names=[]
        for country in range(3):
            for city in range(5):
                state=decode_save_data(dict(version=2,money=0,progress=city,route=[country],
                    owned=[False]*4,equipped_weapon=None,equipped_armor=None))
                index=stage_index(state)
                name=CITY_NAMES[index//5][index%5]
                self.assertTrue(name.isascii() and len(name)<=12)
                names.append(name)
                game.thumby.display.reset_mock()
                game.draw_game(state)
                self.assertIn(name,[call.args[0] for call in game.thumby.display.drawText.call_args_list])
        self.assertEqual(len(set(names)),15)

    def test_each_city_has_two_to_five_maps_and_enemy_cap_is_three(self):
        self.assertEqual(len(CITY_MAP_COUNTS),3)
        self.assertTrue(all(len(cities)==5 for cities in CITY_MAP_COUNTS))
        self.assertTrue(all(2<=count<=5 for cities in CITY_MAP_COUNTS for count in cities))
        self.assertEqual(MAX_ACTIVE_ENEMIES,3)


class HandFootControlTests(unittest.TestCase):
    def battle(self, **changes):
        state=decode_save_data(dict(version=2,money=50,progress=0,route=[0],owned=[False]*4,
                                   equipped_weapon=None,equipped_armor=None))
        state.update(screen_state='battle',active_enemy=True,enemy_x=30,enemy_hp=6,
                     enemy_attack=2,enemy_attack_cooldown=100)
        state.update(changes)
        return state

    def test_hand_and_foot_have_different_reach_and_shared_cooldown(self):
        state=self.battle(enemy_x=32)
        punch=update_state(state,fixtures.inputs(A=True))
        kick=update_state(state,fixtures.inputs(B=True))
        self.assertEqual((punch['enemy_hp'],punch['player_attack_cooldown'],punch['attack_kind']),(6,15,'punch'))
        self.assertEqual((kick['enemy_hp'],kick['player_attack_cooldown'],kick['attack_kind']),(4,20,'kick'))
        later=update_state(kick,fixtures.inputs(A=True))
        self.assertEqual((later['enemy_hp'],later['player_attack_cooldown']),(4,19))
        self.assertEqual(kick['screen_state'],'battle')

    def test_both_buttons_open_status_without_advancing_combat_or_attacking(self):
        state=self.battle(combat_frame=8,player_attack_cooldown=7)
        before=deepcopy(state)
        for keys in (fixtures.inputs(A=True,B=True),
                     fixtures.inputs(B=True,A_held=True,B_held=True)):
            result=update_state(state,keys)
            self.assertEqual(result['screen_state'],'pause')
            for field in ('combat_frame','enemy_hp','HP','player_x','player_y','player_attack_cooldown'):
                self.assertEqual(result[field],state[field])
            self.assertEqual(state,before)

    def test_status_shows_stats_money_city_and_b_returns_without_kicking(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby=fixtures.fake_thumby
        state=update_state(self.battle(),fixtures.inputs(A=True,B=True))
        game.draw_game(state)
        texts=[call.args[0] for call in game.thumby.display.drawText.call_args_list]
        self.assertIn('HP10 AT2 DF0',texts)
        self.assertIn('SEOUL',texts)
        self.assertIn('$50 KR1',texts)
        resumed=update_state(state,fixtures.inputs(B=True))
        self.assertEqual(resumed['screen_state'],'battle')
        self.assertEqual(resumed['enemy_hp'],6)
        self.assertEqual(resumed['player_attack_cooldown'],0)

    def test_shop_is_entered_from_storefront_and_returns_to_the_same_map(self):
        state=self.battle(player_x=104)
        entered=update_state(state,fixtures.inputs(U=True))
        self.assertEqual((entered['screen_state'],entered['shop_return']),('shop','battle'))
        returned=update_state(entered,fixtures.inputs(B=True))
        self.assertEqual(returned['screen_state'],'battle')
        self.assertEqual(returned['player_x'],104)

    def test_shop_cannot_be_opened_from_elsewhere_on_the_map(self):
        state=self.battle(player_x=16)
        unchanged=update_state(state,fixtures.inputs(U=True))
        self.assertEqual(unchanged['screen_state'],'battle')


if __name__=='__main__':
    unittest.main()
