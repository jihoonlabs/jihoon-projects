"""Free country order, city identity, route persistence and hand/foot controls."""
from copy import deepcopy
from itertools import permutations
import unittest

import test_ThumbyGrowth as fixtures
import test_game_completion as completion
import ThumbyGrowth as game
from rules import (new_game_state, update_state, encode_save_data, decode_save_data,
                   is_valid_save_data, stage_index, CITY_NAMES)


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
                state=new_game_state()
                self.assertEqual(state['route'],[])
                for chapter,country in enumerate(order):
                    state=self.choose(state,country)
                    self.assertEqual(state['route'],list(order[:chapter+1]))
                    for city in range(5):
                        self.assertEqual(stage_index(state),country*5+city)
                        self.assertEqual(game.stage_code(state),('KR','CN','JP')[country]+str(city+1))
                        total=state['progress']
                        state=self.finish_fight(state)
                        self.assertEqual(state['progress'],total+1)
                        if total in (1,3,7,11):
                            state=self.buy_and_equip(state,{1:0,3:2,7:1,11:3}[total])
                    if chapter<2:
                        self.assertEqual(state['screen_state'],'country_select')
                        before=encode_save_data(state)
                        state=self.frame(state,B=True)
                        self.assertEqual(state['save_status'],'SAVED')
                        state=game.load_save_data()
                        self.assertEqual(encode_save_data(state),before)
                        self.assertEqual(state['screen_state'],'country_select')
                self.assertEqual((state['progress'],state['money'],state['attack'],state['defense']),
                                 (15,130,6,2))
                self.assertEqual(state['route'],list(order))
                saved=self.frame(state,B=True)
                restored=game.load_save_data()
                self.assertEqual(encode_save_data(restored),encode_save_data(saved))
                self.assertEqual(self.frame(restored,A=True),new_game_state())

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
            self.assertEqual(upgraded['version'],2)
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
        self.assertIn('GAEGYEONG',texts)
        self.assertIn('$50 KR1',texts)
        resumed=update_state(state,fixtures.inputs(B=True))
        self.assertEqual(resumed['screen_state'],'battle')
        self.assertEqual(resumed['enemy_hp'],6)
        self.assertEqual(resumed['player_attack_cooldown'],0)


if __name__=='__main__':
    unittest.main()
