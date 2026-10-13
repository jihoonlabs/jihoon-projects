import unittest
from test_rules import state, inputs
from rules import update_state

class CombatPlaythrough(unittest.TestCase):
    def contact(self, progress):
        current = update_state(state(progress=progress, money=20*progress), inputs(A=True))
        current['enemy_x'] = 24
        hits = 0
        for frame in range(1, 241):
            old = current
            current = update_state(current, inputs(A=(frame-1)%18 == 0))
            if current['enemy_hp'] < old['enemy_hp']:
                hits += 1
            if current['screen_state'] != 'battle':
                break
        return current, hits

    def test_first_enemy_can_be_defeated_at_contact(self):
        current, hits = self.contact(0)
        self.assertEqual((current['screen_state'], current['HP'], current['money'], current['progress'], hits), ('safe', 10, 20, 1, 3))

    def test_second_enemy_contact_wins_with_repeated_hits(self):
        current, hits = self.contact(1)
        self.assertEqual((current['screen_state'], current['HP'], current['enemy_hp'], current['money'], hits), ('safe', 10, 0, 50, 10))

    def test_second_enemy_can_be_defeated_by_spacing(self):
        current = update_state(state(progress=1, money=20), inputs(A=True))
        for frame in range(1, 401):
            gap = current['enemy_x']-current['player_x']-8
            ready = current['player_attack_cooldown'] <= 1
            if ready and gap <= 8:
                keys = inputs(A=True, R=True)
            elif gap < 5:
                keys = inputs(L=True)
            elif gap > 8 and current['player_x'] < 65:
                keys = inputs(R=True)
            else:
                keys = inputs()
            current = update_state(current, keys)
            if current['screen_state'] != 'battle':
                break
        self.assertEqual((current['screen_state'], current['HP'], current['money'], current['progress']), ('safe', 10, 50, 2))

    def test_enemy_attacks_again_only_after_120_battle_frames(self):
        current = update_state(state(progress=1), inputs(A=True))
        current['enemy_x'] = 24
        current = update_state(current, inputs())
        self.assertEqual((current['HP'], current['enemy_attack_cooldown']), (7, 120))
        for _ in range(119):
            current = update_state(current, inputs())
        self.assertEqual((current['HP'], current['enemy_attack_cooldown']), (7, 1))
        current = update_state(current, inputs())
        self.assertEqual((current['HP'], current['enemy_attack_cooldown']), (4, 120))

    def test_waiting_without_attacking_still_causes_defeat(self):
        current = update_state(state(progress=1), inputs(A=True))
        current['enemy_x'] = 24
        for _ in range(361):
            current = update_state(current, inputs())
            if current['screen_state'] == 'defeat':
                break
        self.assertEqual((current['screen_state'], current['HP'], current['enemy_hp']), ('defeat', 0, 10))

    def test_one_hp_enemy_dies_before_fatal_counterattack(self):
        current = state(screen_state='battle', active_enemy=True, HP=1,
            progress=1, money=20, player_x=16, enemy_x=24,
            enemy_hp=1, enemy_attack=3, enemy_defense=1,
            player_attack_cooldown=1, enemy_attack_cooldown=0)
        result = update_state(current, inputs(A=True))
        self.assertEqual((result['screen_state'], result['HP'], result['enemy_hp'],
            result['money'], result['progress'], result['active_enemy']), ('safe',10,0,50,2,False))

    def test_one_hp_kill_does_not_reward_twice(self):
        current = state(screen_state='battle', active_enemy=True, progress=1,
            money=20, player_x=16, enemy_x=24, enemy_hp=1,
            enemy_attack=3, enemy_defense=1)
        result = update_state(current, inputs(A=True))
        later = update_state(result, inputs())
        self.assertEqual((later['money'],later['progress']), (50,2))

    def test_last_hit_waits_for_player_cooldown(self):
        current = state(screen_state='battle', active_enemy=True,
            player_x=16, enemy_x=27, enemy_hp=1, enemy_attack=3,
            enemy_defense=1, player_attack_cooldown=2)
        first = update_state(current, inputs(A=True))
        self.assertEqual((first['enemy_hp'],first['player_attack_cooldown']), (1,1))
        second = update_state(first, inputs(A=True))
        self.assertEqual((second['screen_state'],second['enemy_hp']), ('safe',0))

    def test_second_enemy_can_be_defeated_with_1_2_second_taps(self):
        current = update_state(state(progress=1,money=20), inputs(A=True))
        current['enemy_x'] = 24
        minimum_hp = 10
        for frame in range(1, 401):
            current = update_state(current, inputs(A=(frame-1)%36==0))
            minimum_hp = min(minimum_hp,current['HP'])
            if current['screen_state']!='battle':
                break
        self.assertEqual((current['screen_state'], current['HP'], current['money'], current['progress']), ('safe',10,50,2))
        self.assertGreaterEqual(minimum_hp,1)
