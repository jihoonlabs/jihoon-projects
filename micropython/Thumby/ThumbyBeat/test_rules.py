import unittest

import charts
import rules
from rules import (SCRATCH, KEY_L, KEY_R, KEY_B, KEY_A, GREAT, GOOD, BAD,
                   POOR, LAMP_NONE, LAMP_FAILED, LAMP_CLEAR, LAMP_FULL_COMBO)


def play_of(text, bpm=120, div=2, bgm=''):
    return rules.new_play(rules.parse_chart(text, bpm, div),
                          rules.parse_bgm(bgm, bpm, div))


class TestNotes(unittest.TestCase):
    def test_note_freq(self):
        self.assertEqual(rules.note_freq('A4'), 440)
        self.assertEqual(rules.note_freq('A5'), 880)
        self.assertEqual(rules.note_freq('C4'), 262)
        self.assertEqual(rules.note_freq('F#5'), 740)
        self.assertEqual(rules.note_freq('Bb4'), rules.note_freq('A#4'))

    def test_bad_note_names(self):
        for name in ('H4', 'A', 'A44', 'A#', 'a4', 'A9'):
            with self.assertRaises(ValueError):
                rules.note_freq(name)


class TestParse(unittest.TestCase):
    def test_chart_steps_lanes_and_bars(self):
        notes = rules.parse_chart('LC5 . | RE5 S', 120, 2)
        self.assertEqual(notes, [[0, KEY_L, 523], [500, KEY_R, 659],
                                 [750, SCRATCH, rules.SCRATCH_FREQ]])

    def test_chart_rejects_bad_tokens(self):
        for text in ('X', 'L', 'LZ5', 'L+'):
            with self.assertRaises(ValueError):
                rules.parse_chart(text, 120, 2)

    def test_bgm_hold_and_rest(self):
        events = rules.parse_bgm('C4 - . E4', 120, 2)
        self.assertEqual(events, [(0, 262, 485), (750, 330, 235)])
        with self.assertRaises(ValueError):
            rules.parse_bgm('- C4', 120, 2)

    def test_step_ms_has_no_drift(self):
        self.assertEqual(rules.step_ms(150, 4, 600), 60000)
        self.assertEqual(rules.step_ms(128, 4, 512), 60000)


class TestChartProblems(unittest.TestCase):
    def test_no_simultaneous_notes(self):
        notes = rules.parse_chart('BC5+AC6', 120, 2)
        self.assertTrue(rules.chart_problems(notes))
        notes = rules.parse_chart('LC5+BC5', 120, 2)
        self.assertTrue(rules.chart_problems(notes))

    def test_same_lane_needs_gap(self):
        notes = rules.parse_chart('LC5 LC5', 120, 8)  # 62 ms apart
        self.assertTrue(rules.chart_problems(notes))
        notes = rules.parse_chart('S S S', 150, 4)  # exactly 100 ms
        self.assertEqual(rules.chart_problems(notes), [])

    def test_all_songs_are_playable(self):
        ids = set()
        for song in charts.SONGS:
            with self.subTest(song=song['id']):
                data = rules.load_song(song)
                self.assertEqual(rules.chart_problems(data['notes']), [])
                self.assertGreater(len(data['notes']), 50)
                # Titles fit the 72 px screen with the 6 px default font.
                self.assertLessEqual(len(song['title']), 12)
                self.assertNotIn(song['id'], ids)
                ids.add(song['id'])
                per_bar = song['step_div'] * song['beats_per_bar']
                for key in ('chart', 'bgm'):
                    steps = [t for t in song[key].split() if t != '|']
                    self.assertEqual(len(steps) % per_bar, 0, key)
                # First note leaves time for it to scroll in.
                self.assertGreaterEqual(data['notes'][0][0], 1000)
                for _t, freq, dur in data['bgm']:
                    self.assertTrue(20 <= freq <= 20000)
                    self.assertGreater(dur, 0)

    def test_songs_get_harder(self):
        levels = [s['level'] for s in charts.SONGS]
        self.assertEqual(levels, sorted(levels))


class TestJudge(unittest.TestCase):
    def test_windows(self):
        self.assertEqual(rules.judge_for_offset(0), GREAT)
        self.assertEqual(rules.judge_for_offset(-50), GREAT)
        self.assertEqual(rules.judge_for_offset(51), GOOD)
        self.assertEqual(rules.judge_for_offset(-100), GOOD)
        self.assertEqual(rules.judge_for_offset(150), BAD)
        self.assertIsNone(rules.judge_for_offset(151))

    def test_press_hits_and_scores(self):
        play = play_of('LC5 RE5 LG5')
        self.assertEqual(rules.press(play, KEY_L, 10), (GREAT, 523))
        self.assertEqual(rules.press(play, KEY_R, 250 + 80), (GOOD, 659))
        self.assertEqual(play['combo'], 2)
        self.assertEqual(rules.ex_score(play['counts']), 3)

    def test_early_press_makes_sound_without_judgment(self):
        play = play_of('. . . . LC5')
        self.assertEqual(rules.press(play, KEY_L, 0), (None, 523))
        self.assertEqual(play['counts'], [0, 0, 0, 0])
        self.assertEqual(rules.press(play, KEY_L, 1000), (GREAT, 523))

    def test_empty_lane_press(self):
        play = play_of('LC5')
        self.assertEqual(rules.press(play, KEY_A, 0), (None, None))
        self.assertEqual(rules.press(play, SCRATCH, 0),
                         (None, rules.SCRATCH_FREQ))

    def test_keysound_follows_last_note_after_end(self):
        play = play_of('LC5 . LE5')
        rules.press(play, KEY_L, 0)
        rules.press(play, KEY_L, 500)
        self.assertEqual(rules.press(play, KEY_L, 2000), (None, 659))

    def test_miss_gives_poor_and_breaks_combo(self):
        play = play_of('LC5 RE5')
        rules.press(play, KEY_L, 0)
        self.assertEqual(rules.update_misses(play, 250 + 150), 0)
        self.assertEqual(rules.update_misses(play, 250 + 151), 1)
        self.assertEqual(play['counts'][POOR], 1)
        self.assertEqual(play['combo'], 0)
        self.assertEqual(play['max_combo'], 1)
        # The missed note cannot be hit afterwards.
        self.assertEqual(rules.press(play, KEY_R, 260)[0], None)

    def test_one_press_judges_only_one_note(self):
        play = play_of('LC5 . LC5')
        self.assertEqual(rules.press(play, KEY_L, 0)[0], GREAT)
        self.assertEqual(play['lane_pos'][KEY_L], 1)

    def test_auto_lanes_play_everything_great(self):
        data = rules.load_song(charts.CHOPSTICKS)
        play = rules.new_play(data['notes'], data['bgm'])
        now = 0
        while not rules.is_finished(play, now):
            for lane in rules.auto_lanes(play, now):
                rules.press(play, lane, now)
            rules.update_misses(play, now)
            now += 33
        n = len(data['notes'])
        self.assertEqual(play['counts'], [n, 0, 0, 0])
        self.assertEqual(play['max_combo'], n)
        self.assertEqual(rules.lamp(play), LAMP_FULL_COMBO)
        self.assertEqual(rules.grade(rules.ex_score(play['counts']), n), 'AAA')

    def test_finish_waits_for_notes_and_tail(self):
        play = play_of('LC5', bgm='C4 - - -')
        self.assertFalse(rules.is_finished(play, 1200))
        rules.update_misses(play, 1200)
        self.assertFalse(rules.is_finished(play, 1200))
        self.assertTrue(rules.is_finished(play, play['end_ms']))


class TestGaugeScore(unittest.TestCase):
    def test_gauge_changes_and_limits(self):
        play = play_of('LC5 RE5 LG5 RE5')
        start = play['gauge']
        rules.press(play, KEY_L, 0)
        self.assertEqual(play['gauge'], start + play['gain'])
        rules.press(play, KEY_R, 250 + 120)
        self.assertEqual(play['gauge'], start + play['gain'] - rules.BAD_LOSS)
        play['gauge'] = 5
        rules.update_misses(play, 5000)
        self.assertEqual(play['gauge'], 0)
        play['gauge'] = rules.GAUGE_MAX
        play['gain'] = 50
        play['lane_pos'] = [0] * 5
        play['lanes'] = [[], [0], [], [], []]
        rules.press(play, KEY_L, 0)
        self.assertEqual(play['gauge'], rules.GAUGE_MAX)

    def test_gain_scales_with_note_count(self):
        self.assertEqual(rules.gauge_gain(100), 18)
        self.assertEqual(rules.gauge_gain(10000), 4)
        self.assertEqual(rules.gauge_gain(0), rules.GAUGE_TOTAL)

    def test_grade_boundaries(self):
        self.assertEqual(rules.grade(160, 90), 'AAA')
        self.assertEqual(rules.grade(159, 90), 'AA')
        self.assertEqual(rules.grade(120, 90), 'A')
        self.assertEqual(rules.grade(39, 90), 'F')
        self.assertEqual(rules.grade(0, 0), 'F')

    def test_lamps(self):
        play = play_of('LC5')
        play['gauge'] = 799
        self.assertEqual(rules.lamp(play), LAMP_FAILED)
        play['gauge'] = 800
        self.assertEqual(rules.lamp(play), LAMP_FULL_COMBO)
        play['counts'][BAD] = 1
        self.assertEqual(rules.lamp(play), LAMP_CLEAR)


class TestScreenMath(unittest.TestCase):
    def test_note_y(self):
        self.assertEqual(rules.note_y(1000, 1000, 34, 30), 34)
        self.assertEqual(rules.note_y(2000, 1000, 34, 30), 4)
        self.assertEqual(rules.note_y(900, 1000, 34, 30), 37)

    def test_visible_range_matches_brute_force(self):
        data = rules.load_song(charts.NEON_STEPS)
        play = rules.new_play(data['notes'], data['bgm'])
        for now in range(0, 32000, 137):
            for speed in (20, 40, 60):
                start, stop = rules.visible_range(play, now, 34, speed)
                expect = [i for i, n in enumerate(data['notes'])
                          if -2 <= rules.note_y(n[0], now, 34, speed) <= 34 + 23
                          and n[0] >= now - rules.BAD_MS]
                for i in expect:
                    self.assertTrue(start <= i < stop, (now, speed, i))


class TestBgm(unittest.TestCase):
    def test_due_bgm_returns_latest_once(self):
        play = play_of('LC5', bgm='C4 E4 G4')
        self.assertEqual(rules.due_bgm(play, 0)[1], 262)
        self.assertIsNone(rules.due_bgm(play, 100))
        self.assertEqual(rules.due_bgm(play, 600)[1], 392)
        self.assertIsNone(rules.due_bgm(play, 10000))


class TestSave(unittest.TestCase):
    def test_update_best(self):
        best = {}
        self.assertTrue(rules.update_best(best, 'chop', 100, LAMP_FAILED))
        self.assertFalse(rules.update_best(best, 'chop', 90, LAMP_CLEAR))
        self.assertEqual(best['chop'], [100, LAMP_CLEAR])

    def test_round_trip_and_validation(self):
        best = {'chop': [120, LAMP_CLEAR]}
        payload = rules.encode_save(best, 2)
        self.assertEqual(rules.decode_save(payload, ('chop', 'neon'), 5),
                         (best, 2))
        bad = {'version': 1, 'speed': 9,
               'best': {'chop': [-1, 0], 'neon': [5, 9], 'x': [1, 1]}}
        self.assertEqual(rules.decode_save(bad, ('chop', 'neon'), 5), ({}, 0))
        self.assertEqual(rules.decode_save(None, ('chop',), 5), ({}, 0))
        self.assertEqual(rules.decode_save({'version': 2}, ('chop',), 5),
                         ({}, 0))
        self.assertEqual(
            rules.decode_save({'version': 1, 'best': {'chop': [True, 1]}},
                              ('chop',), 5), ({}, 0))


if __name__ == '__main__':
    unittest.main()
