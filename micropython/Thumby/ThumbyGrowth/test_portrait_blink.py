"""Local frame-driven eye animation preserves title input and shared artwork."""
import unittest
from unittest.mock import patch
import test_ThumbyGrowth as f
import ThumbyGrowth as game


class PortraitBlinkTests(unittest.TestCase):
    def setUp(self):
        f.TestAdapter.setUp(self);game.thumby=f.fake_thumby

    def pixels(self,frame):
        game.thumby.display.reset_mock();game.title_frame(frame)
        result=set()
        for call in game.thumby.display.drawFilledRectangle.call_args_list:
            x,y,w,h,color=call.args
            area={(x+dx,y+dy) for dx in range(w) for dy in range(h)}
            if color:result.update(area)
            else:result.difference_update(area)
        return result

    def test_four_frame_blink_changes_only_eyes_and_reopens_without_bitmap_mutation(self):
        original=tuple(game.PORTRAIT_ROWS)
        open_eye=self.pixels(115)
        closed=self.pixels(116)
        self.assertNotEqual(open_eye,closed)
        self.assertEqual(closed,self.pixels(119))
        self.assertEqual(open_eye,self.pixels(120))
        changed=open_eye^closed
        self.assertTrue(all(6<=x<=12 and 8<=y<=9 for x,y in changed))
        self.assertEqual(tuple(game.PORTRAIT_ROWS),original)

    def test_blink_keeps_new_load_intro_and_ending_inputs_and_save_untouched(self):
        for frame in (0,116):
            for button,action in (('A','new'),('B','load'),('U','opening'),('D','ending')):
                value=getattr(game.thumby,'button'+button)
                value.justPressed.return_value=True
                self.assertEqual(game.title_frame(frame),action)
                value.justPressed.return_value=False
            game.thumby.buttonA.justPressed.return_value=True
            game.thumby.buttonB.justPressed.return_value=True
            self.assertEqual(game.title_frame(frame),'load')
            game.thumby.buttonA.justPressed.return_value=False
            game.thumby.buttonB.justPressed.return_value=False
        game.thumby.saveData.save.assert_not_called()
        game.thumby.saveData.getItem.assert_not_called()

    def test_portrait_clips_overlay_at_all_screen_edges(self):
        for x,y in ((-10,-10),(0,0),(70,35),(80,50)):
            game.thumby.display.reset_mock()
            game.draw_portrait(game.thumby.display,game.PORTRAIT_ROWS,x,y,116)
            for call in game.thumby.display.drawFilledRectangle.call_args_list:
                cx,cy,w,h,_=call.args
                self.assertTrue(0<=cx<cx+w<=72 and 0<=cy<cy+h<=40)

    def test_real_main_loop_advances_title_frame_without_global_state(self):
        actions=[None]*120+['new']
        with patch.object(game,'title_frame',side_effect=actions) as title, \
             patch.object(game,'step_music',side_effect=lambda m,s:m), \
             patch.object(game,'step_frame',side_effect=RuntimeError('halt')):
            with self.assertRaisesRegex(RuntimeError,'halt'):game.main_loop()
        frames=[call.args[0] for call in title.call_args_list]
        self.assertEqual(frames,list(range(120))+[0])


if __name__=='__main__':unittest.main()
