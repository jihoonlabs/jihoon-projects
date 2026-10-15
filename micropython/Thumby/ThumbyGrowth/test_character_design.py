"""Shared 10x14 visuals preserve simulation collision with a floor projection."""
import unittest
from copy import deepcopy
import test_ThumbyGrowth as fixtures
import ThumbyGrowth as game


class CharacterDesignTests(unittest.TestCase):
    def test_regular_enemies_change_only_hair_pixels_and_share_all_poses(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby=fixtures.fake_thumby
        faces=[]
        for head in game.FOE_HEADS+game.BOSS_HEADS:
            self.assertEqual(head[4:],game.HERO_HEAD[4:])
        for city in range(4):
            state=fixtures.state(progress=city,route=[0],combat_frame=0)
            before=deepcopy(state)
            display=game.thumby.display;display.reset_mock()
            game.draw_fighter(display,state,False,28,29)
            pixels=set()
            for call in display.drawFilledRectangle.call_args_list:
                x,y,w,h,ink=call.args
                area={(px,py) for px in range(x,x+w) for py in range(y,y+h)}
                if ink:pixels.update(area)
                else:pixels.difference_update(area)
            faces.append(pixels)
            self.assertEqual(state,before)
            self.assertIs(game.character_head(state,False),game.FOE_HEADS[city])
            for changes,expected in (({},game.BODY_ROWS),({'combat_frame':5},game.WALK_BODY_ROWS),
                                     ({'enemy_windup':1},game.GUARD_BODY),
                                     ({'enemy_attack_cooldown':114},game.PUNCH_BODY),
                                     ({'enemy_hit_flash':6},game.HURT_BODY)):
                self.assertIs(game.character_body(dict(state,**changes),False),expected)
        self.assertEqual(len({frozenset(p) for p in faces}),4)
        self.assertEqual(tuple(len(rows) for rows in game.FOE_SIDE_HAIR),(2,3,4,5))
        for pixels in faces[1:]:
            self.assertTrue(all(24<=x<38 and 22<=y<28 for x,y in pixels^faces[0]))

    def test_regular_enemy_faces_mirror_around_shared_body(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby=fixtures.fake_thumby
        for city in range(4):
            versions=[]
            for right in (True,False):
                state=fixtures.state(progress=city,route=[0],player_x=50 if right else 0,enemy_x=28)
                game.thumby.display.reset_mock()
                game.draw_fighter(game.thumby.display,state,False,28,29)
                pixels=set()
                for call in game.thumby.display.drawFilledRectangle.call_args_list:
                    x,y,w,h,ink=call.args
                    area={(px,py) for px in range(x,x+w) for py in range(y,y+h)}
                    if ink:pixels.update(area)
                    else:pixels.difference_update(area)
                versions.append(pixels)
            self.assertEqual({(61-x,y) for x,y in versions[0]},versions[1])

    def test_row_runs_preserve_every_pixel_and_mirror_without_edge_escape(self):
        fixtures.TestAdapter.setUp(self)
        display=fixtures.fake_thumby.display
        for rows,width in ((game.HERO_HEAD,10),(game.FOE_HEAD,10),
                           (game.BOSS_HEADS[0],10),(game.BOSS_HEADS[1],10),(game.BOSS_HEADS[2],10),
                           (game.BODY_ROWS,10),(game.WALK_BODY_ROWS,10),
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
        for build in ((10,2,0),(20,2,0),(20,6,2)):
            state=fixtures.state(progress=4,route=[0],maxHP=build[0],attack=build[1],defense=build[2])
            designs.append(game.character_rows(state,False))
        self.assertEqual(len(set(designs)),5)
        for rows in designs:
            self.assertEqual(len(rows),14)
            self.assertTrue(all(type(mask) is int and 0<=mask<1024 for mask in rows))
            self.assertEqual(rows[8:],game.BODY_ROWS)

    def test_walk_changes_legs_not_identity_or_state(self):
        for player in (True,False):
            for country in range(3):
                state=fixtures.state(progress=4,route=[country],combat_frame=0)
                still=game.character_rows(state,player)
                state['combat_frame']=5
                before=deepcopy(state)
                walking=game.character_rows(state,player)
                self.assertEqual(state,before)
                self.assertEqual(still[:12],walking[:12])
                self.assertNotEqual(still[12:],walking[12:])

    def test_boss_design_ignores_country_and_changes_with_player_power(self):
        for progress in (4,9,14):
            appearances=[]
            for country in range(3):
                others=[r for r in range(3) if r!=country]
                route=others[:progress//5]+[country]
                state=fixtures.state(progress=progress,route=route)
                appearances.append(game.character_head(state,False))
                self.assertEqual(game.character_rows(state,False)[8:],game.BODY_ROWS)
            self.assertEqual(len(set(appearances)),1)
            weak=fixtures.state(progress=progress,route=[0],maxHP=10,attack=2,defense=0)
            strong=fixtures.state(progress=progress,route=[0],maxHP=20,attack=10,defense=4)
            self.assertNotEqual(game.boss_variant(weak),game.boss_variant(strong))

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
