"""Background must help orientation without changing combat or obscuring HUD."""
from copy import deepcopy
import unittest

import test_ThumbyGrowth as fixtures
import ThumbyGrowth as game
import campaign


class BackgroundTests(unittest.TestCase):
    def setUp(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby = fixtures.fake_thumby

    def rectangles(self):
        return [call.args for call in game.thumby.display.drawFilledRectangle.call_args_list]

    def test_fifteen_stage_backgrounds_are_distinct_and_deterministic(self):
        scenes=[]
        for stage in range(15):
            game.thumby.display.reset_mock()
            game.draw_background(game.thumby.display,stage,24)
            first=self.rectangles()
            game.thumby.display.reset_mock()
            game.draw_background(game.thumby.display,stage,24)
            self.assertEqual(first,self.rectangles())
            scenes.append(tuple(first))
        self.assertEqual(len(set(scenes)),15)

    def test_all_camera_offsets_keep_background_below_hud_and_in_bounds(self):
        for stage in range(15):
            for camera in range(73):
                game.thumby.display.reset_mock()
                game.draw_background(game.thumby.display,stage,camera)
                for x,y,w,h,color in self.rectangles():
                    self.assertTrue(0<=x<x+w<=72)
                    self.assertTrue(14<=y<y+h<=40)
                    self.assertEqual(color,1)

    def test_scrolling_changes_visible_background(self):
        for stage in range(15):
            game.thumby.display.reset_mock()
            game.draw_background(game.thumby.display,stage,0)
            origin=self.rectangles()
            game.thumby.display.reset_mock()
            game.draw_background(game.thumby.display,stage,24)
            self.assertNotEqual(origin,self.rectangles())

    def test_compact_scenery_leaves_three_depths_of_open_floor(self):
        for stage in range(15):
            game.thumby.display.reset_mock()
            game.draw_background(game.thumby.display,stage,24)
            calls=self.rectangles()
            scenery=[r for r in calls if r[1]<21]
            self.assertTrue(scenery)
            self.assertTrue(all(y+h<=21 for x,y,w,h,color in scenery))
            floor=[r for r in calls if r[1]>=21]
            self.assertEqual({r[1] for r in floor},{23,29,37})
            self.assertTrue(all(r[3]==1 and r[2]<=3 for r in floor))

    def test_actor_sprite_has_no_black_square_backing(self):
        state=fixtures.state(screen_state='battle',progress=4,active_enemy=True,
                             player_x=16,player_y=15,enemy_x=30,enemy_y=28,enemy_hp=16)
        before=deepcopy(state)
        game.draw_game(state)
        self.assertEqual(state,before)
        calls=self.rectangles()
        self.assertNotIn((13,14,12,14,0),calls)
        self.assertNotIn((27,21,12,15,0),calls)
        for x,y,w,h,color in calls:
            if color==0 and h>2:
                self.assertGreaterEqual(y,14)

    def test_scene_rect_clips_edges_and_skips_fully_offscreen(self):
        game.scene_rect(game.thumby.display,-4,10,10,10)
        game.scene_rect(game.thumby.display,70,38,8,9,0)
        game.scene_rect(game.thumby.display,80,20,8,8)
        self.assertEqual(self.rectangles(),[(0,14,6,6,1),(70,38,2,2,0)])

    def test_render_call_budget_and_unchanged_state_all_stages(self):
        for stage in range(15):
            for player_x in (0,16,70,138):
                game.thumby.display.reset_mock()
                state=fixtures.state(screen_state='battle',progress=stage,
                                     active_enemy=True,player_x=player_x,
                                     enemy_x=player_x,player_y=15,enemy_y=33)
                before=deepcopy(state)
                game.draw_game(state)
                self.assertEqual(state,before)
                self.assertLessEqual(len(self.rectangles()),160)

    def test_shop_icons_are_distinct_seven_row_monochrome_sprites(self):
        icons=game.ITEM_ICON_ROWS
        self.assertEqual(len(icons),10)
        self.assertEqual(len(set(icons)),10)
        for icon in icons:
            self.assertEqual(len(icon),7)
            self.assertTrue(all(0<=row<=0x1f for row in icon))

    def test_campaign_shop_shows_short_effect_labels_within_72_by_40(self):
        state=campaign.new_game_state()
        state.update(screen_state='shop',money=125)
        before=deepcopy(state)
        game.draw_campaign_game(state)
        calls=game.thumby.display.drawText.call_args_list
        labels=[call.args[0] for call in calls]
        self.assertIn('SHOP',labels)
        self.assertIn('AT+2',labels)
        self.assertIn('AT+4',labels)
        self.assertIn('DF+1',labels)
        self.assertEqual(state,before)
        for call in calls:
            text,x,y,_=call.args
            self.assertTrue(0<=x and x+6*len(text)<=72)
            self.assertTrue(0<=y and y+7<=40)


if __name__=='__main__':
    unittest.main()
