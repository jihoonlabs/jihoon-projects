"""Shared 8x10 visuals preserve the existing collision body and foot position."""
import unittest
from copy import deepcopy
import test_ThumbyGrowth as fixtures
import ThumbyGrowth as game


class CharacterDesignTests(unittest.TestCase):
    def test_row_runs_preserve_every_pixel_and_mirror_without_edge_escape(self):
        fixtures.TestAdapter.setUp(self)
        display=fixtures.fake_thumby.display
        for rows,width in ((game.HERO_HEAD,8),(game.FOE_HEAD,8),
                           (game.BOSS_HEADS[0],8),(game.BOSS_HEADS[1],8),(game.BOSS_HEADS[2],8),
                           (game.BODY_ROWS,8),(game.WALK_BODY_ROWS,8),
                           (game.HEART_ROWS,5),(game.ENEMY_ICON_ROWS,5)):
            for mirror in (False,True):
                for x,y in ((0,0),(-3,14),(70,37),(80,20)):
                    display.reset_mock()
                    game.draw_rows(display,rows,x,y,width,mirror)
                    actual=set()
                    for call in display.drawFilledRectangle.call_args_list:
                        cx,cy,w,h,color=call.args
                        self.assertTrue(0<=cx<cx+w<=72 and 0<=cy<cy+h<=40)
                        self.assertEqual((h,color),(1,1))
                        actual.update((px,cy) for px in range(cx,cx+w))
                    expected={(x+col,y+row) for row,mask in enumerate(rows)
                              for col in range(width) if 0<=x+col<72 and 0<=y+row<40
                              and mask & (1<<(col if mirror else width-1-col))}
                    self.assertEqual(actual,expected)

    def test_battle_hud_has_only_two_health_numbers(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby=fixtures.fake_thumby
        state=fixtures.state(screen_state='battle',active_enemy=True,enemy_hp=6)
        game.draw_game(state)
        texts=[call.args[0] for call in game.thumby.display.drawText.call_args_list]
        self.assertEqual(texts,['10','6'])

    def test_hero_foe_and_three_bosses_are_distinct(self):
        state=fixtures.state(combat_frame=0)
        designs=[game.character_rows(state,True),game.character_rows(state,False)]
        for country in range(3):
            state.update(progress=4,route=[country])
            designs.append(game.character_rows(state,False))
        self.assertEqual(len(set(designs)),5)
        for rows in designs:
            self.assertEqual(len(rows),10)
            self.assertTrue(all(type(mask) is int and 0<=mask<256 for mask in rows))
            self.assertEqual(rows[5:],game.BODY_ROWS)

    def test_walk_changes_legs_not_identity_or_state(self):
        for player in (True,False):
            for country in range(3):
                state=fixtures.state(progress=4,route=[country],combat_frame=0)
                still=game.character_rows(state,player)
                state['combat_frame']=5
                before=deepcopy(state)
                walking=game.character_rows(state,player)
                self.assertEqual(state,before)
                self.assertEqual(still[:8],walking[:8])
                self.assertNotEqual(still[8:],walking[8:])

    def test_boss_design_follows_selected_country_not_total_chapter(self):
        for progress in (4,9,14):
            for country in range(3):
                others=[r for r in range(3) if r!=country]
                route=others[:progress//5]+[country]
                state=fixtures.state(progress=progress,route=route)
                self.assertIs(game.character_head(state,False),game.BOSS_HEADS[country])
                self.assertEqual(game.character_rows(state,False)[5:],game.BODY_ROWS)

    def test_design_render_keeps_bounds_call_budget_and_state(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby=fixtures.fake_thumby
        for country in range(3):
            for x in (0,70,138):
                for y in (15,33):
                    state=fixtures.state(progress=4,route=[country],screen_state='battle',
                        player_x=x,enemy_x=x,player_y=y,enemy_y=y,active_enemy=True,enemy_hp=16)
                    before=deepcopy(state)
                    game.thumby.display.reset_mock()
                    game.draw_game(state)
                    calls=game.thumby.display.drawFilledRectangle.call_args_list
                    self.assertEqual(state,before)
                    self.assertLessEqual(len(calls),160)
                    for call in calls:
                        cx,cy,w,h,_=call.args
                        self.assertTrue(0<=cx<cx+w<=72 and 0<=cy<cy+h<=40)


if __name__=='__main__':
    unittest.main()
