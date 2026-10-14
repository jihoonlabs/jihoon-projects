"""Original silhouettes stay within the existing 6x7 combat body."""
import unittest
from copy import deepcopy
import test_ThumbyGrowth as fixtures
import ThumbyGrowth as game


class CharacterDesignTests(unittest.TestCase):
    def test_hero_foe_and_three_bosses_are_distinct(self):
        state=fixtures.state(combat_frame=0)
        designs=[game.character_rows(state,True),game.character_rows(state,False)]
        for country in range(3):
            state.update(progress=4,route=[country])
            designs.append(game.character_rows(state,False))
        self.assertEqual(len(set(designs)),5)
        for rows in designs:
            self.assertEqual(len(rows),7)
            self.assertTrue(all(type(mask) is int and 0<=mask<64 for mask in rows))

    def test_walk_changes_legs_not_identity_or_state(self):
        for player in (True,False):
            for country in range(3):
                state=fixtures.state(progress=4,route=[country],combat_frame=0)
                still=game.character_rows(state,player)
                state['combat_frame']=5
                before=deepcopy(state)
                walking=game.character_rows(state,player)
                self.assertEqual(state,before)
                self.assertEqual(still[:5],walking[:5])
                self.assertNotEqual(still[5:],walking[5:])

    def test_boss_design_follows_selected_country_not_total_chapter(self):
        for progress in (4,9,14):
            for country in range(3):
                others=[r for r in range(3) if r!=country]
                route=others[:progress//5]+[country]
                state=fixtures.state(progress=progress,route=route)
                self.assertEqual(game.character_rows(state,False),game.BOSS_ROWS[country])

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
