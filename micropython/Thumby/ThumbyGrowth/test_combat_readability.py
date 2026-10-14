"""Visible equipment, distinct attacks and hit-only X faces at native resolution."""
from copy import deepcopy
from unittest.mock import patch
import unittest
import test_ThumbyGrowth as f
import ThumbyGrowth as game
from rules import update_state


class CombatReadabilityTests(unittest.TestCase):
    def setUp(self):
        f.TestAdapter.setUp(self);game.thumby=f.fake_thumby

    def state(self,**changes):
        data=dict(screen_state='battle',active_enemy=True,player_x=28,enemy_x=36,
                  enemy_hp=30,enemy_attack=2,enemy_attack_cooldown=20)
        data.update(changes);return f.state(**data)

    def render(self,state):
        game.thumby.display.reset_mock();game.draw_game(state)
        return [c.args for c in game.thumby.display.drawFilledRectangle.call_args_list]

    def test_equipped_weapons_are_distinct_even_without_attacking(self):
        for direction in ('L','R'):
            images=[]
            for weapon in (None,0,1,4):
                state=self.state(direction=direction,equipped_weapon=weapon)
                before=deepcopy(state);images.append(tuple(self.render(state)))
                self.assertEqual(state,before)
                self.assertEqual(game.character_pose(state,True),'idle')
            self.assertEqual(len(set(images)),4)

    def test_real_attack_buttons_have_distinct_extended_poses_and_recovery(self):
        for button,kind in (('A','punch'),('B','kick')):
            before=self.state(enemy_x=70)
            after=update_state(before,f.inputs(**{button:True}))
            self.assertEqual(game.character_pose(after,True),kind)
            self.assertNotEqual(self.render(after),self.render(before))
            for _ in range(31): after=update_state(after,f.inputs())
            self.assertEqual(game.character_pose(after,True),'idle')
        self.assertNotEqual(game.PUNCH_BODY,game.KICK_BODY)
        skilled=update_state(self.state(equipped_weapon=4,gun_owned=True,skill_owned=True,command_ready=12),f.inputs(A=True))
        self.assertEqual(game.character_pose(skilled,True),'skill')
        with patch.object(game,'draw_weapon',wraps=game.draw_weapon) as weapon:
            self.render(skilled)
            # The skill keeps the pistol visible but must not show a gun muzzle flash.
            self.assertFalse(weapon.call_args_list[0].args[-1])

    def test_actual_damage_only_marks_the_actor_who_was_hit(self):
        for target,changes,keys in (
            (False,{},dict(A=True)),
            (True,dict(enemy_windup=1,enemy_attack_cooldown=0),{}),
            (None,dict(enemy_x=100),dict(A=True))):
            before=self.state(**changes);after=update_state(before,f.inputs(**keys))
            with patch.object(game,'draw_hurt_face',wraps=game.draw_hurt_face) as face, \
                 patch.object(game,'draw_impact',wraps=game.draw_impact) as impact:
                self.render(after)
                self.assertEqual(face.call_count,0 if target is None else 1)
                self.assertEqual(impact.call_count,face.call_count)
                if target is not None: self.assertEqual(game.character_pose(after,target),'hurt')
            if target is None: self.assertEqual(after['enemy_hp'],before['enemy_hp'])

    def test_x_eyes_and_flat_mouth_have_the_expected_native_pixels(self):
        game.thumby.display.reset_mock()
        game.draw_hurt_face(game.thumby.display,10,20)
        pixels={}
        for c in game.thumby.display.drawFilledRectangle.call_args_list:
            x,y,w,h,ink=c.args
            for px in range(x,x+w):
                for py in range(y,y+h): pixels[px,py]=ink
        for eye in (1,6):
            for row in range(3):
                for col in range(3):
                    self.assertEqual(pixels[10+eye+col,23+row],0 if col in (row,2-row) else 1)
        self.assertEqual([pixels[x,26] for x in range(13,17)],[0]*4)

    def test_hurt_face_expires_with_the_real_latch(self):
        state=update_state(self.state(),f.inputs(A=True))
        for remaining in range(6,0,-1):
            self.assertEqual(state['enemy_hit_flash'],remaining)
            self.assertEqual(game.character_pose(state,False),'hurt')
            state=update_state(state,f.inputs())
        self.assertNotEqual(game.character_pose(state,False),'hurt')

    def test_larger_figures_fit_all_floor_depths_without_changing_world_state(self):
        for y in range(15,34):
            self.assertTrue(14<=game.actor_screen_y(y)-7)
            self.assertTrue(game.actor_screen_y(y)+6<40)
        for x,enemy in ((0,6),(28,34),(132,138)):
            for direction in ('L','R'):
                state=self.state(player_x=x,enemy_x=enemy,direction=direction)
                before=deepcopy(state);camera=max(0,min(72,x-32))
                px,ex=game.fighter_positions(state,camera)
                self.assertGreaterEqual(abs(px-ex),12)
                self.assertTrue(2<=px<=64 and 2<=ex<=64)
                self.render(state);self.assertEqual(state,before)

    def test_effects_weapons_and_poses_stay_below_hud_at_both_edges(self):
        maximum=0
        for weapon in (None,0,1,4):
            for x,enemy in ((0,8),(70,62),(130,138)):
                for y in (15,33):
                    for change in ({},{'player_hit_flash':6},{'enemy_hit_flash':6},
                                   {'enemy_windup':12},{'player_attack_cooldown':15},
                                   {'attack_kind':'kick','player_attack_cooldown':20},
                                   {'attack_kind':'skill','player_attack_cooldown':30}):
                        state=self.state(player_x=x,enemy_x=enemy,player_y=y,enemy_y=y,
                                         equipped_weapon=weapon,**change)
                        before=deepcopy(state);rects=self.render(state)
                        maximum=max(maximum,len(rects));self.assertEqual(state,before)
                        for cx,cy,w,h,_ in rects: self.assertTrue(0<=cx<cx+w<=72 and 0<=cy<cy+h<=40)
        self.assertLessEqual(maximum,180)


if __name__=='__main__': unittest.main()
