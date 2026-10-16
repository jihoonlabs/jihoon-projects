"""State-driven sound feedback and finite single-channel scheduling."""
import unittest
from copy import deepcopy
from unittest.mock import patch
import test_ThumbyGrowth as f
import ThumbyGrowth as game
from rules import update_state, encode_save_data


class AudioFeedbackTests(unittest.TestCase):
    def setUp(self):
        f.TestAdapter.setUp(self)
        game.thumby=f.fake_thumby
        game.thumby.audio.reset_mock()

    def battle(self,**changes):
        return f.state(screen_state='battle',active_enemy=True,enemy_x=22,
                       enemy_hp=30,enemy_attack=2,**changes)

    def test_actual_combat_hit_miss_damage_gun_and_skill(self):
        cases=[(self.battle(),f.inputs(A=True),(659,2)),
               (self.battle(),f.inputs(B=True),(392,2)),
               (self.battle(enemy_y=15),f.inputs(A=True),(330,1)),
               (self.battle(gun_owned=True,equipped_weapon=4),f.inputs(A=True),(880,2)),
               (self.battle(skill_owned=True,command_ready=12),f.inputs(A=True),(1047,2)),
               (self.battle(enemy_windup=1),f.inputs(),(196,3))]
        for before,keys,expected in cases:
            after=update_state(before,keys)
            self.assertEqual(game.sound_effect(before,after),expected)
            self.assertIsNone(game.sound_effect(after,update_state(after,f.inputs())))

    def test_actual_purchase_success_and_refusal(self):
        for money,expected in ((40,(988,2)),(39,None)):
            before=f.state(screen_state='shop',money=money)
            after=update_state(before,f.inputs(A=True))
            self.assertEqual(game.sound_effect(before,after),expected)
            self.assertIsNone(game.sound_effect(after,update_state(after,f.inputs(A=True))))

    def test_save_changes_and_battle_reward_are_not_repeated(self):
        before=f.state()
        for status,expected in (('SAVED',(784,2)),('SAVE ERR',(147,3))):
            after=dict(before,save_status=status)
            self.assertEqual(game.sound_effect(before,after),expected)
            self.assertIsNone(game.sound_effect(after,dict(after)))
        before=self.battle();before['enemy_hp']=1
        after=update_state(before,f.inputs(A=True))
        self.assertEqual(after['progress'],1)
        self.assertEqual(game.sound_effect(before,after),(1047,3))
        self.assertIsNone(game.sound_effect(after,dict(after)))

    def test_finite_cue_resumes_music_without_mutating_game_or_save(self):
        before=self.battle();after=update_state(before,f.inputs(A=True))
        snapshot=deepcopy(after);saved=encode_save_data(after)
        music={'track':1,'tick':7,'next_ms':0};original=dict(music)
        music=game.step_audio(music,before,after,0)
        self.assertEqual(original,{'track':1,'tick':7,'next_ms':0})
        game.thumby.audio.play.assert_called_once_with(659,66)
        music=game.step_audio(music,after,after,33)
        self.assertEqual(game.thumby.audio.play.call_count,1)
        music=game.step_audio(music,after,after,66)
        self.assertNotIn('fx_until',music)
        self.assertEqual(game.thumby.audio.play.call_count,2)
        self.assertEqual(game.thumby.audio.play.call_args.args[1],160)
        music=game.step_audio(music,after,after,198)
        self.assertEqual(game.thumby.audio.play.call_count,2)
        self.assertEqual(game.thumby.audio.play.call_args.args[1],160)
        self.assertEqual(after,snapshot)
        self.assertEqual(encode_save_data(after),saved)
        for name in ('A','B','U','D'):
            getattr(game.thumby,'button'+name).justPressed.assert_not_called()
        game.thumby.saveData.save.assert_not_called()

    def test_pause_defeat_track_change_and_clear_cancel_effect(self):
        before=self.battle()
        for screen in ('pause','defeat'):
            game.thumby.audio.reset_mock()
            after=dict(before,screen_state=screen)
            music=game.step_audio({'track':1,'tick':8,'fx_until':100},before,after,0)
            self.assertEqual(music,{'track':None,'tick':0})
            game.thumby.audio.stop.assert_called_once_with()
            game.thumby.audio.play.assert_not_called()
        after=dict(before,route=[1])
        music=game.step_audio({'track':1,'tick':8,'fx_until':100},after,after,200)
        self.assertEqual(music,{'track':2,'tick':0,'next_ms':230})
        game.thumby.audio.reset_mock()
        after=f.state(progress=15,route=[0,1,2])
        music={'track':1,'tick':8,'fx_left':2}
        for frame in range(200): music=game.step_audio(music,after,after,frame*33)
        self.assertEqual(music,{'track':5,'tick':49})
        self.assertEqual(game.thumby.audio.play.call_count,7)

    def test_main_loop_wires_previous_and_next_to_audio(self):
        before=self.battle();after=update_state(before,f.inputs(A=True))
        with patch.object(game,'title_frame',return_value='new'), \
             patch.object(game.campaign,'new_game_state',return_value=before), \
             patch.object(game,'step_frame',side_effect=[after,RuntimeError('halt')]), \
             patch.object(game,'step_music',side_effect=lambda m,s,*args:m), \
             patch.object(game,'step_audio',side_effect=lambda m,p,s:m) as audio:
            with self.assertRaisesRegex(RuntimeError,'halt'): game.main_loop()
            self.assertEqual(audio.call_args.args[1:],(before,after))

    def test_ending_restart_does_not_replay_country_clear_scene(self):
        before=f.state(progress=15,route=[0,1,2]);after=update_state(before,f.inputs(A=True))
        self.assertEqual((after['progress'],after['screen_state']),(0,'country_select'))
        with patch.object(game,'title_frame',return_value='new'), \
             patch.object(game,'new_game_state',return_value=before), \
             patch.object(game,'step_frame',side_effect=[after,RuntimeError('halt')]), \
             patch.object(game,'step_music',side_effect=lambda m,s,*args:m), \
             patch.object(game,'cutscene_frame',return_value=True) as scene:
            with self.assertRaisesRegex(RuntimeError,'halt'): game.main_loop()
            scene.assert_not_called()


if __name__=='__main__': unittest.main()
