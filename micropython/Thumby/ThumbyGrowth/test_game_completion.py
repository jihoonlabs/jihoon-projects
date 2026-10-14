"""Title, fifteen encounters, shopping, persistence and ending as one game."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_ThumbyGrowth as fixtures
import ThumbyGrowth as game
from rules import update_state, decode_save_data, encode_save_data, new_game_state


def initial():
    return decode_save_data(dict(version=1, money=0, progress=0,
        owned=[False]*4, equipped_weapon=None, equipped_armor=None))


class GameCompletionTests(unittest.TestCase):
    def setUp(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby = fixtures.fake_thumby
        self.memory = {}
        device = game.thumby.saveData
        device.hasItem.side_effect = lambda key: key in self.memory
        device.getItem.side_effect = lambda key: deepcopy(self.memory[key])
        device.setItem.side_effect = lambda key, value: self.memory.update({key: value})

    def frame(self, state, **buttons):
        with patch.object(game, 'handle_inputs', return_value=fixtures.inputs(**buttons)):
            return game.step_frame(state)

    def finish_fight(self, state):
        # Exercise real input/rules/save flow; render only the resulting screen.
        with patch.object(game, 'draw_game'):
            state = self.frame(state, A=True)
            self.assertEqual(state['screen_state'], 'battle')
            for _ in range(2000):
                state = self.frame(state, R=state['enemy_x'] > state['player_x']+6,
                                   L=state['enemy_x'] < state['player_x']-6, A=True)
                self.assertNotEqual(state['screen_state'], 'defeat')
                if state['screen_state'] in ('safe','country_select'):
                    break
            else:
                self.fail('Encounter did not finish within 2000 frames')
        game.draw_game(state)
        return state

    def buy_and_equip(self, state, item):
        state=self.frame(state,D=True)
        state=self.frame(state,A=True)
        for _ in range(item):
            state=self.frame(state,D=True)
        before=state['money']
        state=self.frame(state,A=True)
        self.assertTrue(state['owned'][item])
        self.assertEqual(state['money'],before-(40,80,40,80)[item])
        state=self.frame(state,B=True)
        for _ in range(2):
            state=self.frame(state,D=True)
        state=self.frame(state,A=True)
        for _ in range(item):
            state=self.frame(state,D=True)
        state=self.frame(state,A=True)
        self.assertEqual(state['equipped_weapon' if item<2 else 'equipped_armor'],item)
        return self.frame(state,B=True)

    def test_fifteen_stage_game_purchase_equip_save_load_and_ending(self):
        state = initial()
        rewards = (20,30,20,30,20,30,20,30,20,30,20,30,20,30,20)
        shopping = {1:0, 3:2, 7:1, 11:3}
        expected_money = 0
        for stage in range(15):
            before = state['money']
            state = self.finish_fight(state)
            self.assertEqual(state['progress'], stage+1)
            self.assertEqual(state['money'], before+rewards[stage])
            self.assertEqual(state['HP'], 10)
            expected_money += rewards[stage]
            if stage in shopping:
                item=shopping[stage]
                state=self.buy_and_equip(state,item)
                expected_money-=(40,80,40,80)[item]
            if stage in (1,4,9):
                if state['screen_state']=='country_select':
                    state=self.frame(state,B=True)
                else:
                    for _ in range(3):
                        state = self.frame(state, D=True)
                    state = self.frame(state, A=True)
                self.assertEqual(state['save_status'], 'SAVED')
                state = game.load_save_data()
                self.assertEqual(state['progress'], stage+1)
                self.assertEqual(state['money'], expected_money)
                if stage==4:
                    self.assertEqual(game.stage_code(state['progress']),'CN1')
                elif stage==9:
                    self.assertEqual(game.stage_code(state['progress']),'JP1')
                if stage in (4,9):
                    self.assertEqual(state['screen_state'],'country_select')
                    state=self.frame(state,A=True)
        self.assertEqual(state['money'], expected_money)
        self.assertEqual((state['attack'],state['defense']),(6,2))
        texts = [c.args[0] for c in game.thumby.display.drawText.call_args_list]
        self.assertIn('QUEST CLEAR', texts)
        for _ in range(5):
            after = self.frame(state, R=True, U_held=True)
            self.assertEqual(encode_save_data(after),encode_save_data(state))
            self.assertEqual(after['screen_state'], 'safe')
        saved = self.frame(state, B=True)
        self.assertEqual(saved['save_status'], 'SAVED')
        restored = game.load_save_data()
        self.assertEqual(restored['progress'], 15)
        self.assertEqual(self.frame(restored, A=True), new_game_state())

    def test_encounter_stats_and_boss(self):
        expected = ((6,2,0),(10,3,1),(8,3,0),(12,3,1),(16,4,2),
                    (10,3,1),(12,3,1),(12,4,1),(16,4,2),(20,4,2),
                    (14,4,2),(16,4,2),(18,4,2),(18,5,2),(24,5,3))
        for progress, stats in enumerate(expected):
            state = initial()
            state['progress'] = progress
            result = update_state(state, fixtures.inputs(A=True))
            self.assertEqual(tuple(result[k] for k in ('enemy_hp','enemy_attack','enemy_defense')),stats)

    def test_completed_game_new_resets_progress_equipment_and_money(self):
        state = initial()
        state.update(progress=15,route=[0,1,2],money=80,owned=[True]*4,equipped_weapon=1,
                     equipped_armor=3,attack=6,defense=2)
        before = deepcopy(state)
        self.assertEqual(update_state(state, fixtures.inputs(A=True)),new_game_state())
        self.assertEqual(state, before)

    def test_ending_save_is_one_pulse_and_load_still_shows_ending(self):
        state = initial()
        state['progress'] = 15
        state['route'] = [0,1,2]
        saved = self.frame(state, B=True)
        self.assertEqual(game.thumby.saveData.save.call_count,1)
        later = self.frame(saved)
        self.assertEqual(game.thumby.saveData.save.call_count,1)
        self.assertEqual(later['save_status'],'SAVED')
        restored = game.load_save_data()
        game.thumby.display.reset_mock()
        game.draw_game(restored)
        self.assertIn('QUEST CLEAR',[c.args[0] for c in game.thumby.display.drawText.call_args_list])

    def test_title_wait_new_load_and_load_priority(self):
        self.assertIsNone(game.title_frame())
        self.assertEqual(game.thumby.saveData.mock_calls,[])
        game.thumby.buttonA.justPressed.return_value=True
        self.assertEqual(game.title_frame(),'new')
        game.thumby.buttonB.justPressed.return_value=True
        self.assertEqual(game.title_frame(),'load')

    def test_new_game_start_does_not_read_or_overwrite_existing_save(self):
        captured=[]
        def stop(state):
            captured.append(deepcopy(state))
            raise StopIteration()
        with patch.object(game,'title_frame',return_value='new'), \
             patch.object(game,'step_frame',side_effect=stop):
            with self.assertRaises(StopIteration):
                game.main_loop()
        self.assertEqual(captured,[new_game_state()])
        self.assertEqual(game.thumby.saveData.mock_calls,[])
        game.thumby.display.setFPS.assert_called_once_with(30)

    def test_load_start_uses_existing_progress(self):
        state=initial()
        state['progress']=3
        game.save_game(state)
        captured=[]
        def stop(restored):
            captured.append(restored['progress'])
            raise StopIteration()
        with patch.object(game,'title_frame',return_value='load'), \
             patch.object(game,'step_frame',side_effect=stop):
            with self.assertRaises(StopIteration):
                game.main_loop()
        self.assertEqual(captured,[3])

    def test_old_five_stage_clear_save_continues_in_china(self):
        state=initial()
        state.update(progress=5,money=80,owned=[True,False,True,False],
                     equipped_weapon=0,equipped_armor=2,attack=4,defense=1)
        game.save_game(state)
        restored=game.load_save_data()
        self.assertEqual(encode_save_data(restored),encode_save_data(state))
        self.assertEqual(restored['screen_state'],'country_select')
        chosen=self.frame(restored,A=True)
        self.assertEqual(chosen['route'],[0,1])
        self.assertEqual(game.stage_code(chosen),'CN1')
        entered=self.frame(chosen,A=True)
        self.assertEqual((entered['screen_state'],entered['progress'],entered['money']),
                         ('battle',5,80))
        self.assertEqual((entered['enemy_hp'],entered['enemy_attack'],entered['enemy_defense']),
                         (10,3,1))

    def test_region_boundaries_do_not_reset_equipment_or_show_final_ending(self):
        for progress,code in ((4,'KR5'),(5,'CN1'),(9,'CN5'),(10,'JP1'),(14,'JP5')):
            state=initial()
            state.update(progress=progress,owned=[True,False,True,False],
                         equipped_weapon=0,equipped_armor=2,attack=4,defense=1)
            self.assertEqual(game.stage_code(progress),code)
            entered=self.frame(state,A=True)
            self.assertEqual(entered['screen_state'],'battle')
            self.assertEqual((entered['attack'],entered['defense'],entered['progress']),(4,1,progress))
            game.thumby.display.reset_mock()
            game.draw_game(state)
            self.assertNotIn('QUEST CLEAR',[c.args[0] for c in game.thumby.display.drawText.call_args_list])

    def test_retry_preserves_stage_and_equipment_without_granting_reward(self):
        state=initial()
        state.update(screen_state='defeat',HP=0,progress=4,money=10,
                     owned=[True,False,True,False],equipped_weapon=0,equipped_armor=2,
                     attack=4,defense=1)
        retry=update_state(state,fixtures.inputs(A=True))
        self.assertEqual((retry['progress'],retry['money'],retry['attack'],retry['defense'],retry['HP']),
                         (4,10,4,1,10))
        self.assertEqual((retry['enemy_hp'],retry['enemy_attack'],retry['enemy_defense']),(16,4,2))


if __name__ == '__main__':
    unittest.main()
