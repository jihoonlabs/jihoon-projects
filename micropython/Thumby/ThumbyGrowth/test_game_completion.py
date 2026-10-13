"""Title, five encounters, shopping, persistence and ending as one game."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_ThumbyGrowth as fixtures
import ThumbyGrowth as game
from rules import update_state, decode_save_data, encode_save_data


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
        state = self.frame(state, A=True)
        self.assertEqual(state['screen_state'], 'battle')
        # Fight through the same inputs as a player; do not teleport or change HP.
        for _ in range(2000):
            state = self.frame(state, R=state['enemy_x'] > state['player_x']+6,
                               L=state['enemy_x'] < state['player_x']-6, A=True)
            self.assertNotEqual(state['screen_state'], 'defeat')
            if state['screen_state'] == 'safe':
                return state
        self.fail('Encounter did not finish within 2000 frames')

    def test_five_stage_game_purchase_equip_save_load_and_ending(self):
        state = initial()
        rewards = (20, 30, 20, 30, 20)
        expected_money = 0
        for stage in range(5):
            before = state['money']
            state = self.finish_fight(state)
            self.assertEqual(state['progress'], stage+1)
            self.assertEqual(state['money'], before+rewards[stage])
            self.assertEqual(state['HP'], 10)
            expected_money += rewards[stage]
            if stage == 1:
                # Use the real menu to buy/equip Blade, then save and reload.
                state = self.frame(state, D=True)
                state = self.frame(state, A=True)
                state = self.frame(state, A=True)
                self.assertEqual((state['owned'][0], state['money']), (True, 10))
                state = self.frame(state, B=True)
                for _ in range(2):
                    state = self.frame(state, D=True)
                state = self.frame(state, A=True)
                state = self.frame(state, A=True)
                self.assertEqual((state['equipped_weapon'],state['attack']), (0,4))
                state = self.frame(state, B=True)
                for _ in range(3):
                    state = self.frame(state, D=True)
                state = self.frame(state, A=True)
                self.assertEqual(state['save_status'], 'SAVED')
                state = game.load_save_data()
                self.assertEqual((state['progress'],state['attack'],state['money']), (2,4,10))
                expected_money -= 40
        self.assertEqual(state['money'], expected_money)
        texts = [c.args[0] for c in game.thumby.display.drawText.call_args_list]
        self.assertIn('QUEST CLEAR', texts)
        for _ in range(5):
            after = self.frame(state, R=True, U_held=True)
            self.assertEqual(encode_save_data(after),encode_save_data(state))
            self.assertEqual(after['screen_state'], 'safe')
        saved = self.frame(state, B=True)
        self.assertEqual(saved['save_status'], 'SAVED')
        restored = game.load_save_data()
        self.assertEqual(restored['progress'], 5)
        self.assertEqual(self.frame(restored, A=True), initial())

    def test_encounter_stats_and_boss(self):
        expected = ((6,2,0),(10,3,1),(8,3,0),(12,3,1),(16,4,2))
        for progress, stats in enumerate(expected):
            state = initial()
            state['progress'] = progress
            result = update_state(state, fixtures.inputs(A=True))
            self.assertEqual(tuple(result[k] for k in ('enemy_hp','enemy_attack','enemy_defense')),stats)

    def test_completed_game_new_resets_progress_equipment_and_money(self):
        state = initial()
        state.update(progress=5,money=80,owned=[True]*4,equipped_weapon=1,
                     equipped_armor=3,attack=6,defense=2)
        before = deepcopy(state)
        self.assertEqual(update_state(state, fixtures.inputs(A=True)),initial())
        self.assertEqual(state, before)

    def test_ending_save_is_one_pulse_and_load_still_shows_ending(self):
        state = initial()
        state['progress'] = 5
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
        self.assertEqual(captured,[initial()])
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
