"""Actual cutscene pixels, finite decoration cost, skip/save and timing contracts."""
import unittest
from copy import deepcopy
from unittest.mock import patch
import test_ThumbyGrowth as f
import ThumbyGrowth as game


class SceneDetailTests(unittest.TestCase):
    def setUp(self):
        f.TestAdapter.setUp(self)
        game.thumby=f.fake_thumby
        game.thumby.audio.reset_mock()

    def pixels(self,calls):
        return {(x+dx,y+dy) for call in calls for x,y,w,h,color in [call.args]
                for dx in range(w) for dy in range(h) if color}

    def test_three_countries_have_distinct_motifs_and_no_frame_arrays(self):
        self.assertEqual(sum(map(len,game.SCENE_MOTIFS)),11)
        self.assertEqual(len(set(game.SCENE_MOTIFS)),3)
        result=[]
        for region in range(3):
            game.thumby.display.reset_mock()
            game.draw_scene_details(game.thumby.display,0,0,region)
            result.append(self.pixels(game.thumby.display.drawFilledRectangle.call_args_list))
        self.assertEqual(len({frozenset(value) for value in result}),3)

    def test_all_real_frames_stay_in_picture_and_small_call_budget(self):
        for picture in range(4):
            for region in range(3):
                for frame in range(90):
                    game.thumby.display.reset_mock()
                    game.draw_scene_details(game.thumby.display,picture,frame,region)
                    calls=game.thumby.display.drawFilledRectangle.call_args_list
                    self.assertLessEqual(len(calls),24)
                    for call in calls:
                        x,y,w,h,color=call.args
                        self.assertTrue(0<=x<x+w<=72 and 0<=y<y+h<=32)
                        self.assertEqual((h,color),(1,1))

    def test_motion_is_repeatable_and_changes_real_pixel_positions(self):
        for region in range(3):
            frames=[]
            for frame in (0,12,0):
                game.thumby.display.reset_mock()
                game.draw_scene_details(game.thumby.display,0,frame,region)
                frames.append(self.pixels(game.thumby.display.drawFilledRectangle.call_args_list))
            self.assertEqual(frames[0],frames[2])
            self.assertNotEqual(frames[0],frames[1])

    def test_actual_scene_uses_selected_country_without_mutating_game_or_art(self):
        art=tuple(bytes(b) for b in game.SCENE_BITMAPS)
        for region in range(3):
            state=f.state(progress=4,route=[region])
            before=deepcopy(state)
            with patch.object(game,'draw_scene_details') as details:
                game.cutscene_frame('opening',12,state)
                details.assert_called_once_with(game.thumby.display,0,12,region)
            self.assertEqual(state,before)
        self.assertEqual(tuple(bytes(b) for b in game.SCENE_BITMAPS),art)

    def test_preview_scene_still_has_three_second_limit_and_one_bitmap_blit(self):
        for kind,duration in (('opening',90),('ending',90),('event',45)):
            game.thumby.display.reset_mock()
            state=f.state();before=deepcopy(state)
            music={'track':None,'tick':0}
            game.play_scene(kind,state,music)
            self.assertEqual(game.thumby.display.update.call_count,duration)
            self.assertEqual(game.thumby.display.blit.call_count,duration)
            self.assertEqual(state,before)
            game.thumby.saveData.save.assert_not_called()
        for button in ('A','B'):
            game.thumby.display.reset_mock()
            getattr(game.thumby,'button'+button).justPressed.return_value=True
            game.play_scene('opening',f.state(),{'track':None,'tick':0})
            self.assertEqual(game.thumby.display.update.call_count,1)
            getattr(game.thumby,'button'+button).justPressed.return_value=False


if __name__=='__main__':unittest.main()
