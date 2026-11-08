import json
import sys
import unittest

import fake_thumby

thumby = fake_thumby.make_module()
sys.modules['thumby'] = thumby
import ThumbyBeat as game_mod  # noqa: E402
import rules  # noqa: E402
from charts import SONGS  # noqa: E402

FRAME = 33
NAMES = ('U', 'D', 'L', 'R', 'A', 'B')
LANE_BUTTON = {rules.SCRATCH: 'U', rules.KEY_L: 'L', rules.KEY_R: 'R',
               rules.KEY_B: 'B', rules.KEY_A: 'A'}


def inputs(taps=(), held=()):
    held = set(held) | set(taps)
    return game_mod.make_inputs({n: n in taps for n in NAMES},
                                {n: n in held for n in NAMES})


def fresh(screen='title'):
    thumby.audio.calls = []
    thumby.display.out_of_bounds = []
    game = game_mod.new_game(now=0)
    game['screen'] = screen
    return game


def run_idle(game, start, stop, step=FRAME):
    now = start
    while now < stop:
        game_mod.step(game, inputs(), now)
        now += step
    return now


class TestInputs(unittest.TestCase):
    def test_up_and_down_share_scratch_lane(self):
        self.assertEqual(inputs(['U'])['lane_taps'], [True, False, False, False, False])
        self.assertEqual(inputs(['D'])['lane_taps'], [True, False, False, False, False])
        self.assertEqual(inputs(['B'])['lane_taps'], [False, False, False, True, False])
        self.assertEqual(inputs(['A'])['lane_taps'], [False, False, False, False, True])

    def test_start_needs_both_held_and_one_new(self):
        self.assertTrue(inputs(['A'], held=['B'])['start'])
        self.assertTrue(inputs(['A', 'B'])['start'])
        self.assertFalse(inputs(['A'])['start'])
        self.assertFalse(inputs(held=['A', 'B'])['start'])

    def test_read_inputs_uses_buttons(self):
        thumby.buttonD.down = True
        try:
            self.assertTrue(game_mod.read_inputs()['lane_taps'][rules.SCRATCH])
            self.assertFalse(game_mod.read_inputs()['lane_taps'][rules.SCRATCH])
            self.assertTrue(game_mod.read_inputs()['lane_held'][rules.SCRATCH])
        finally:
            thumby.buttonD.down = False
            game_mod.read_inputs()


class TestMenus(unittest.TestCase):
    def test_title_start(self):
        game = fresh()
        game_mod.step(game, inputs(['A', 'B']), 10)
        self.assertEqual(game['screen'], 'select')

    def test_select_song_and_speed(self):
        game = fresh('select')
        game_mod.step(game, inputs(['U']), 0)
        self.assertEqual(game['song'], len(SONGS) - 1)
        game_mod.step(game, inputs(['D']), 0)
        self.assertEqual(game['song'], 0)
        for _ in range(10):
            game_mod.step(game, inputs(['R']), 0)
        self.assertEqual(game['speed'], len(game_mod.SPEEDS) - 1)
        for _ in range(10):
            game_mod.step(game, inputs(['L']), 0)
        self.assertEqual(game['speed'], 0)
        self.assertTrue(game['save_dirty'])
        game_mod.step(game, inputs(['B']), 0)
        self.assertEqual(game['screen'], 'title')

    def test_select_starts_song(self):
        game = fresh('select')
        game_mod.step(game, inputs(['A']), 500)
        self.assertEqual(game['screen'], 'play')
        self.assertEqual(game['start'], 500)
        self.assertFalse(game['demo'])


class TestPlay(unittest.TestCase):
    def start(self, song=0):
        game = fresh('select')
        game['song'] = song
        game_mod.step(game, inputs(['A']), 0)
        return game

    def test_hit_on_time_is_great_and_plays_note(self):
        game = self.start()
        note = game['play']['notes'][0]
        run_idle(game, 0, note[0] - 40)
        thumby.audio.calls = []
        game_mod.step(game, inputs([LANE_BUTTON[note[1]]]), note[0] + 10)
        self.assertEqual(game['play']['counts'][rules.GREAT], 1)
        self.assertIn(('play', note[2], game_mod.KEY_MS), thumby.audio.calls)

    def test_bgm_resumes_after_key_sound(self):
        game = self.start()
        play = game['play']
        note = play['notes'][0]
        run_idle(game, 0, note[0] - 5)
        game_mod.step(game, inputs([LANE_BUTTON[note[1]]]), note[0])
        thumby.audio.calls = []
        # Key sound ends; the current accompaniment note continues.
        game_mod.step(game, inputs(), note[0] + game_mod.KEY_MS + 5)
        plays = [c for c in thumby.audio.calls if c[0] == 'play']
        self.assertEqual(len(plays), 1)
        event = game['bgm_event']
        self.assertEqual(plays[0][1], event[1])

    def test_no_input_fails_and_saves_on_menu(self):
        game = self.start()
        end = game['play']['end_ms']
        now = run_idle(game, 0, end + 200)
        self.assertEqual(game['screen'], 'result')
        result = game['result']
        self.assertEqual(result['lamp'], rules.LAMP_FAILED)
        self.assertEqual(result['counts'][rules.POOR], len(game['play']['notes']))
        self.assertEqual(result['grade'], 'F')
        self.assertFalse(result['new_best'])
        self.assertTrue(game['save_dirty'])
        game_mod.step(game, inputs(['A']), now)
        self.assertEqual(game['screen'], 'select')
        self.assertTrue(game_mod.save_game(game))
        saved = json.loads(thumby.saveData.saved['data'])
        self.assertEqual(saved['best']['chop'], [0, rules.LAMP_FAILED])

    def test_short_ab_overlap_does_not_pause(self):
        game = self.start()
        game_mod.step(game, inputs(['A'], held=['B']), 1000)
        game_mod.step(game, inputs(held=['A', 'B']), 1000 + 200)
        game_mod.step(game, inputs(), 1000 + 233)
        game_mod.step(game, inputs(held=['A', 'B']), 1400)
        self.assertEqual(game['screen'], 'play')

    def test_hold_ab_pauses_and_continue_keeps_position(self):
        game = self.start()
        game_mod.step(game, inputs(['A', 'B']), 1000)
        game_mod.step(game, inputs(held=['A', 'B']), 1300)
        self.assertEqual(game['screen'], 'pause')
        game_mod.step(game, inputs(), 5000)
        game_mod.step(game, inputs(['A']), 6300)
        self.assertEqual(game['screen'], 'play')
        self.assertEqual(game_mod.song_time(game, 6300), 1300)

    def test_pause_retry_and_quit(self):
        game = self.start()
        game['screen'] = 'pause'
        game_mod.step(game, inputs(['D']), 2000)
        game_mod.step(game, inputs(['A']), 2000)
        self.assertEqual(game['screen'], 'play')
        self.assertEqual(game['start'], 2000)
        game['screen'] = 'pause'
        game['pause_sel'] = 0
        game_mod.step(game, inputs(['U']), 3000)
        game_mod.step(game, inputs(['A']), 3000)
        self.assertEqual(game['screen'], 'select')

    def test_perfect_play_full_combo_and_new_best(self):
        for index, song in enumerate(SONGS):
            with self.subTest(song=song['id']):
                game = self.start(index)
                play = game['play']
                now = 0
                while game['screen'] == 'play':
                    lanes = rules.auto_lanes(play, now)
                    taps = [LANE_BUTTON[lane] for lane in lanes]
                    game_mod.step(game, inputs(taps), now)
                    now += FRAME
                self.assertEqual(game['screen'], 'result')
                self.assertEqual(game['result']['lamp'], rules.LAMP_FULL_COMBO)
                self.assertEqual(game['result']['grade'], 'AAA')
                self.assertTrue(game['result']['new_best'])


class TestDemo(unittest.TestCase):
    def test_idle_title_starts_demo_and_returns(self):
        game = fresh()
        game['song'] = 2
        now = run_idle(game, 0, game_mod.DEMO_IDLE_MS + FRAME)
        self.assertEqual(game['screen'], 'play')
        self.assertTrue(game['demo'])
        self.assertEqual(game['song'], 0)
        while game['screen'] == 'play':
            game_mod.step(game, inputs(), now)
            now += FRAME
        self.assertEqual(game['screen'], 'title')
        self.assertEqual(game['song'], 2)
        self.assertEqual(game['demo_song'], 1)
        self.assertIsNone(game['result'])

    def test_demo_plays_all_great(self):
        game = fresh()
        game_mod.start_song(game, 0, demo=True)
        play = game['play']
        now = 0
        while play['counts'][rules.GREAT] < len(play['notes']):
            game_mod.step(game, inputs(), now)
            now += FRAME
            self.assertLess(now, 120000)
        self.assertEqual(play['counts'][rules.POOR], 0)

    def test_any_button_leaves_demo(self):
        game = fresh()
        game['menu_song'] = 1
        game_mod.start_song(game, 0, demo=True)
        game_mod.step(game, inputs(['L']), 500)
        self.assertEqual(game['screen'], 'title')
        self.assertEqual(game['song'], 1)

    def test_title_input_resets_idle(self):
        game = fresh()
        run_idle(game, 0, 7000)
        game_mod.step(game, inputs(['L']), 7000)
        run_idle(game, 7000, 7000 + 7000)
        self.assertEqual(game['screen'], 'title')


class TestSave(unittest.TestCase):
    def test_load_defaults_and_corrupt(self):
        thumby.saveData.saved = {}
        self.assertEqual(game_mod.load_save(), ({}, game_mod.DEFAULT_SPEED))
        thumby.saveData.saved = {'data': '{broken'}
        self.assertEqual(game_mod.load_save(), ({}, game_mod.DEFAULT_SPEED))
        thumby.saveData.saved = {'data': json.dumps(
            rules.encode_save({'neon': [10, 2]}, 3))}
        self.assertEqual(game_mod.load_save(), ({'neon': [10, 2]}, 3))
        self.assertEqual(thumby.saveData.name, 'ThumbyBeat')


class TestDraw(unittest.TestCase):
    def check_screen(self, game, now):
        thumby.display.out_of_bounds = []
        game_mod.draw(game, now)
        self.assertEqual(thumby.display.out_of_bounds, [], game['screen'])

    def test_every_screen_stays_on_screen(self):
        game = fresh()
        game['best'] = {'chop': [318, rules.LAMP_FULL_COMBO]}
        for now in range(0, 3000, 97):
            self.check_screen(game, now)
        game['screen'] = 'select'
        for index in range(len(SONGS)):
            game['song'] = index
            self.check_screen(game, 0)
        game['screen'] = 'pause'
        for sel in range(3):
            game['pause_sel'] = sel
            self.check_screen(game, 0)
        game['screen'] = 'result'
        for lamp in range(1, 4):
            game['result'] = {'ex': 9999, 'max_ex': 9999, 'grade': 'AAA',
                              'lamp': lamp, 'counts': [999, 999, 999, 999],
                              'max_combo': 999, 'new_best': True}
            for now in (0, 300):
                self.check_screen(game, now)

    def test_play_screens_stay_on_screen_at_all_speeds(self):
        for index in range(len(SONGS)):
            for speed in range(len(game_mod.SPEEDS)):
                game = fresh('select')
                game['song'] = index
                game['speed'] = speed
                game_mod.step(game, inputs(['A']), 0)
                play = game['play']
                now = 0
                while game['screen'] == 'play':
                    lanes = rules.auto_lanes(play, now)
                    taps = [LANE_BUTTON[lane] for lane in lanes]
                    game_mod.step(game, inputs(taps), now)
                    if game['screen'] == 'play' and now % 5 == 0:
                        self.check_screen(game, now)
                    now += FRAME

    def test_notes_reach_judge_line_on_time(self):
        game = fresh('select')
        game_mod.step(game, inputs(['A']), 0)
        note = game['play']['notes'][0]
        game_mod.draw(game, note[0])
        x = game_mod.LANE_X[note[1]]
        display = thumby.display
        self.assertEqual(display.get(x + 1, game_mod.JUDGE_Y), 1)
        self.assertEqual(display.get(x + 1, game_mod.JUDGE_Y - 1), 1)
        # A judged note is no longer drawn.
        lane_button = LANE_BUTTON[note[1]]
        game_mod.step(game, inputs([lane_button]), note[0])
        game['flash'] = [-10000] * rules.LANE_COUNT
        game_mod.draw(game, note[0])
        self.assertEqual(display.get(x + 1, game_mod.JUDGE_Y - 1), 0)

    def test_dancer_sprites_are_16_by_17(self):
        for frame in (game_mod.DANCER_DOWN, game_mod.DANCER_UP,
                      game_mod.DANCER_SAD):
            data, width, height = frame
            self.assertEqual((width, height), (16, 17))
            self.assertEqual(len(data), 16 * 3)

    def test_panel_judgment_and_gauge(self):
        game = fresh('select')
        game_mod.step(game, inputs(['A']), 0)
        play = game['play']
        play['last_judge'] = rules.GREAT
        play['last_judge_ms'] = 1000
        play['combo'] = 12
        play['gauge'] = rules.GAUGE_MAX
        # 1100 ms is in the visible half of the judgment blink.
        game_mod.draw(game, 1100)
        texts = [t[0] for t in thumby.display.texts]
        self.assertIn('GREAT', texts)
        self.assertIn('12', texts)
        self.assertEqual(thumby.display.get(game_mod.PANEL_X + 31, 37), 1)


if __name__ == '__main__':
    unittest.main()
