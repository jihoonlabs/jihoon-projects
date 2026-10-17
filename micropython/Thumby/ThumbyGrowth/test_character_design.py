"""Shared 10x14 visuals preserve simulation collision with a floor projection."""
import unittest
from copy import deepcopy
from unittest.mock import patch
import test_ThumbyGrowth as fixtures
import ThumbyGrowth as game


class CharacterDesignTests(unittest.TestCase):
    def test_fighter_rectangles_shrink_around_the_foot_anchor(self):
        fixtures.TestAdapter.setUp(self)
        display=fixtures.fake_thumby.display
        display.reset_mock()
        scaled=game.ScaledFighterDisplay(display,23,36)
        scaled.drawFilledRectangle(18,22,10,14,1)
        x,y,width,height,color=display.drawFilledRectangle.call_args.args
        self.assertEqual((x,y,width,height),(20,27,6,9))
        self.assertEqual(color,1)
        self.assertGreaterEqual(y+height,34)

    def test_idle_face_uses_eyes_without_a_mouth(self):
        fixtures.TestAdapter.setUp(self)
        display=fixtures.fake_thumby.display
        display.reset_mock()
        game.draw_fighter_details(display,10,20,'idle',True)
        calls=[call.args for call in display.drawFilledRectangle.call_args_list]
        self.assertIn((11,17,1,1,0),calls)
        self.assertIn((16,17,1,1,0),calls)
        self.assertNotIn((14,19,2,1,0),calls)

    def test_attack_limb_frames_extend_from_the_old_character_silhouette(self):
        punch0=game.attack_limb_runs('punch',0,True,20,20)
        punch1=game.attack_limb_runs('punch',2,True,20,20)
        kick0=game.attack_limb_runs('kick',0,True,20,20)
        kick1=game.attack_limb_runs('kick',2,True,20,20)
        self.assertNotEqual(punch0,punch1)
        self.assertNotEqual(kick0,kick1)
        for shapes,expected_components in ((punch0,1),(punch1,1),
                                           (kick0,2),(kick1,2)):
            lit=[(x+offset,y) for x,y,width,height,color in shapes if color
                 for offset in range(width) for _ in range(height)]
            self.assertEqual(self.pixel_component_count(lit),expected_components)
        self.assertGreater(max(x+w for x,y,w,h,color in punch1 if color),
                           max(x+w for x,y,w,h,color in punch0 if color))

    @staticmethod
    def pixel_component_count(pixel_list):
        pixels=set(pixel_list)
        count=0
        while pixels:
            count+=1
            stack=[pixels.pop()]
            while stack:
                x,y=stack.pop()
                for neighbor in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if neighbor in pixels:
                        pixels.remove(neighbor)
                        stack.append(neighbor)
        return count

    def test_country_weapon_sprites_are_visibly_distinct(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby=fixtures.fake_thumby
        renders=[]
        for weapon in (4,1,0):
            game.thumby.display.reset_mock()
            game.draw_weapon(game.thumby.display,weapon,30,25,True,True)
            renders.append(repr(game.thumby.display.drawFilledRectangle.call_args_list))
        self.assertEqual(len(set(renders)),3)

    def test_three_country_fighters_have_distinct_sprite_silhouettes(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby=fixtures.fake_thumby
        faces=[]
        for head in game.FOE_HEADS+game.BOSS_HEADS:
            self.assertEqual(head[4:],game.HERO_HEAD[4:])
        for city in range(3):
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
        self.assertEqual(len({frozenset(p) for p in faces}),3)

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
            mirrored={(61-x,y) for x,y in versions[0]}
            # Integer pixel scaling can round a single edge pixel either way.
            self.assertLessEqual(len(mirrored^versions[1]),8)

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

    def test_campaign_movement_has_a_visible_walk_pose_only_while_moving(self):
        from campaign import new_game_state, update
        state=new_game_state()
        state.update(screen_state='explore',current_city=0,route=[0],
                     foes=[dict(x=112,y=22,hp=6,max_hp=6,attack=2,defense=0,
                         windup=0,cooldown=40,stun=0,flash=0,hp_seen=False,boss=False)])
        stopped=update(state,fixtures.inputs())
        self.assertFalse(stopped['player_moving'])
        self.assertIs(game.character_body(stopped,True),game.BODY_ROWS)
        moving=update(stopped,fixtures.inputs(R=True))
        self.assertTrue(moving['player_moving'])
        moving['frame']=4
        self.assertIs(game.character_body(moving,True),game.WALK_BODY_ROWS)

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

    def test_upper_lane_fighter_keeps_its_head_visible_after_scale_clipping(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby=fixtures.fake_thumby
        state=fixtures.state(screen_state='battle',player_y=12,enemy_y=12,
                             player_x=24,enemy_x=80,active_enemy=True)
        display=game.thumby.display
        display.reset_mock()
        game.draw_fighter(display,state,False,28,17)
        white=[call.args for call in display.drawFilledRectangle.call_args_list
               if call.args[4]==1]
        self.assertTrue(any(y==16 for x,y,width,height,color in white),white)
        self.assertTrue(all(14<=y<40 for x,y,width,height,color in white),white)


if __name__=='__main__':
    unittest.main()

