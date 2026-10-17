"""Readable attacks: warning, interruption, dodge, impact and pause timing."""
import unittest
from copy import deepcopy
import test_ThumbyGrowth as fixtures
import ThumbyGrowth as game
from rules import update_state, encode_save_data, decode_save_data, ENEMY_WINDUP_FRAMES


class CombatFeedbackTests(unittest.TestCase):
    def battle(self,**changes):
        values=dict(screen_state='battle',active_enemy=True,enemy_x=24,
                    enemy_hp=10,enemy_attack=2)
        values.update(changes)
        return fixtures.state(**values)

    def step(self,state,**keys):
        before=deepcopy(state)
        result=update_state(state,fixtures.inputs(**keys))
        self.assertEqual(state,before)
        return result

    def test_warning_precedes_damage_and_stops_pursuit(self):
        state=self.step(self.battle())
        self.assertEqual((state['HP'],state['enemy_windup']),(10,ENEMY_WINDUP_FRAMES))
        for remaining in range(ENEMY_WINDUP_FRAMES-1,0,-1):
            state=self.step(state)
            self.assertEqual((state['HP'],state['enemy_windup'],state['enemy_x']),(10,remaining,24))
        state=self.step(state)
        self.assertEqual((state['HP'],state['enemy_windup'],state['enemy_attack_cooldown']),(8,0,120))
        self.assertEqual(state['player_hit_flash'],6)
        state=self.step(state)
        self.assertEqual(state['HP'],8)

    def test_side_step_dodges_committed_swing_and_still_causes_recovery(self):
        state=self.step(self.battle())
        for _ in range(4):
            state=self.step(state,U_held=True)
        for _ in range(8):
            state=self.step(state)
        self.assertEqual((state['HP'],state['player_y'],state['enemy_y']),(10,20,28))
        self.assertEqual((state['enemy_windup'],state['enemy_attack_cooldown']),(0,120))

    def test_both_attacks_interrupt_warning_and_stun_only_on_hit(self):
        for button,stun in (('A',8),('B',12)):
            state=self.step(self.battle(enemy_windup=1),**{button:True})
            self.assertEqual((state['HP'],state['enemy_hp'],state['enemy_windup']),(10,8,0))
            self.assertEqual((state['enemy_stun'],state['enemy_hit_flash']),(stun,6))
            for _ in range(stun-1):
                x=state['enemy_x']
                state=self.step(state)
                self.assertEqual((state['enemy_x'],state['HP']),(x,10))
            missed=self.step(self.battle(enemy_x=80,enemy_windup=1),**{button:True})
            self.assertEqual((missed['enemy_stun'],missed['enemy_hit_flash']),(0,0))

    def test_kick_pushes_away_in_both_directions_and_clamps_world_edges(self):
        for px,ex,direction,expected in ((16,24,'R',27),(24,16,'L',13),
                                       (130,138,'R',138),(8,0,'L',0)):
            state=self.step(self.battle(player_x=px,enemy_x=ex,direction=direction),B=True)
            self.assertEqual(state['enemy_x'],expected)
            self.assertGreaterEqual(abs(state['player_x']-state['enemy_x']),6)
            self.assertEqual(state['enemy_stun'],12)

    def test_pause_and_resume_freeze_all_feedback_timers(self):
        state=self.battle(enemy_windup=5,enemy_stun=3,enemy_hit_flash=4,player_hit_flash=2)
        paused=self.step(state,A=True,B=True)
        for _ in range(20):
            paused=self.step(paused)
        for field in ('enemy_windup','enemy_stun','enemy_hit_flash','player_hit_flash','combat_frame'):
            self.assertEqual(paused[field],state[field])
        resumed=self.step(paused,B=True)
        self.assertEqual(resumed['screen_state'],'battle')
        self.assertEqual(resumed['enemy_windup'],5)

    def test_retry_and_load_clear_transient_effects_without_saving_transient_effects(self):
        state=self.battle(enemy_windup=5,enemy_stun=3,enemy_hit_flash=4,player_hit_flash=2,
                          screen_state='defeat')
        retried=self.step(state,A=True)
        saved=encode_save_data(state)
        self.assertEqual(set(saved),{'version','money','progress','owned','equipped_weapon','equipped_armor','route','gun_owned','skill_owned','potions','hp_growth','atk_growth','def_growth'})
        loaded=decode_save_data(saved)
        for field in ('enemy_windup','enemy_stun','enemy_hit_flash','player_hit_flash'):
            self.assertEqual((retried[field],loaded[field]),(0,0))

    def test_warning_render_changes_frame_and_stays_clipped(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby=fixtures.fake_thumby
        for px,ex,y in ((0,8,15),(130,138,33),(70,62,28)):
            state=self.battle(player_x=px,enemy_x=ex,enemy_y=y)
            game.thumby.display.reset_mock()
            game.draw_game(state)
            normal=list(game.thumby.display.drawFilledRectangle.call_args_list)
            state['enemy_windup']=12
            before=deepcopy(state)
            game.thumby.display.reset_mock()
            game.draw_game(state)
            warned=list(game.thumby.display.drawFilledRectangle.call_args_list)
            self.assertEqual(state,before)
            self.assertNotEqual(normal,warned)
            for call in warned:
                x,y,w,h,color=call.args
                self.assertTrue(0<=x<x+w<=72 and 0<=y<y+h<=40)
            self.assertLessEqual(len(warned),160)

    def test_flash_uses_actual_hits_instead_of_attack_recovery(self):
        fixtures.TestAdapter.setUp(self)
        game.thumby=fixtures.fake_thumby
        state=self.battle(combat_frame=2,enemy_attack_cooldown=120)
        game.draw_game(state)
        recovery=list(game.thumby.display.drawFilledRectangle.call_args_list)
        game.thumby.display.reset_mock()
        state['player_hit_flash']=6
        game.draw_game(state)
        hit=list(game.thumby.display.drawFilledRectangle.call_args_list)
        self.assertNotEqual(hit,recovery)
        self.assertEqual(game.character_pose(state,True),'hurt')
        self.assertEqual(game.character_pose(dict(state,player_hit_flash=0),True),'idle')

if __name__=='__main__':
    unittest.main()
