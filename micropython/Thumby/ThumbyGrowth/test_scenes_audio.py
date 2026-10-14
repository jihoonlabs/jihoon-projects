"""Finite two-cut scenes and nonblocking single-channel music."""
import unittest
from copy import deepcopy
from unittest.mock import patch
import test_ThumbyGrowth as f
import ThumbyGrowth as game


class SceneAudioTests(unittest.TestCase):
    def setUp(self):
        f.TestAdapter.setUp(self)
        game.thumby=f.fake_thumby
        game.thumby.audio.reset_mock()

    def test_two_cuts_reuse_pixels_stay_in_bounds_and_do_not_change_state(self):
        for kind in ('opening','ending','event'):
            frames=[]
            for frame in (0,44,45,89):
                state=f.state(progress=15 if kind=='ending' else 5 if kind=='event' else 0)
                before=deepcopy(state)
                game.thumby.display.reset_mock()
                self.assertFalse(game.cutscene_frame(kind,frame,state))
                self.assertEqual(state,before)
                calls=game.thumby.display.drawFilledRectangle.call_args_list
                for call in calls:
                    x,y,w,h,_=call.args
                    self.assertTrue(0<=x<x+w<=72 and 0<=y<y+h<=40)
                frames.append(tuple(str(c) for c in calls))
            if kind!='event':
                self.assertNotEqual(frames[0],frames[2])

    def test_either_button_skips_and_does_not_touch_save(self):
        for button in ('A','B'):
            for b in ('A','B'):
                getattr(game.thumby,'button'+b).justPressed.return_value=b==button
            self.assertTrue(game.cutscene_frame('opening',0,f.state()))
            game.thumby.saveData.save.assert_not_called()

    def test_music_plays_on_note_edges_only_and_leaves_inputs_immutable(self):
        music={'track':None,'tick':0};state=f.state(screen_state='battle')
        before=deepcopy(state)
        for frame in range(7):
            old=deepcopy(music)
            result=game.step_music(music,state)
            self.assertEqual(music,old)
            music=result
        self.assertEqual(game.thumby.audio.play.call_count,2)
        self.assertEqual(state,before)
        for call in game.thumby.audio.play.call_args_list:
            self.assertTrue(20<=call.args[0]<=20000)
            self.assertEqual(call.args[1],160)

    def test_pause_defeat_stop_music_without_repeated_device_calls(self):
        for screen in ('pause','defeat'):
            game.thumby.audio.reset_mock()
            music=game.step_music({'track':1,'tick':7},f.state(screen_state=screen))
            game.thumby.audio.stop.assert_called_once_with()
            game.thumby.audio.play.assert_not_called()
            self.assertEqual(music,{'track':None,'tick':0})
            game.step_music(music,f.state(screen_state=screen))
            self.assertEqual(game.thumby.audio.stop.call_count,1)

    def test_region_boss_and_clear_tracks_and_clear_plays_once(self):
        for region in range(3):
            self.assertEqual(game.step_music({'track':None,'tick':0},
                f.state(screen_state='battle',route=[region]))['track'],region+1)
        self.assertEqual(game.step_music({'track':None,'tick':0},
            f.state(screen_state='battle',progress=4))['track'],4)
        game.thumby.audio.reset_mock()
        music={'track':None,'tick':0}
        for _ in range(200):
            music=game.step_music(music,f.state(progress=15,route=[0,1,2]))
        self.assertEqual(music,{'track':5,'tick':49})
        self.assertEqual(game.thumby.audio.play.call_count,7)

    def test_main_loop_triggers_opening_event_and_ending_at_real_transitions(self):
        for kind,previous,result in (
            ('opening',f.state(screen_state='country_select',route=[]),f.state()),
            ('event',f.state(screen_state='battle',progress=4),f.state(progress=5)),
            ('ending',f.state(screen_state='battle',progress=14,route=[0,1,2]),
             f.state(progress=15,route=[0,1,2]))):
            with patch.object(game,'title_frame',return_value='new'), \
                 patch.object(game,'new_game_state',return_value=previous), \
                 patch.object(game,'step_frame',side_effect=[result,RuntimeError('halt')]), \
                 patch.object(game,'step_music',side_effect=lambda m,s:m), \
                 patch.object(game,'cutscene_frame',return_value=True) as scene:
                with self.assertRaisesRegex(RuntimeError,'halt'):
                    game.main_loop()
                scene.assert_called_once_with(kind,0,result)


if __name__=='__main__':
    unittest.main()
