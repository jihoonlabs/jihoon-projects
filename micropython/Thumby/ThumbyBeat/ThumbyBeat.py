import sys
import time
try:
    import ujson as json
except ImportError:
    import json
import thumby
# The device launcher need not add the game folder to the module path.
if sys.implementation.name == 'micropython':
    sys.path.append('/Games/ThumbyBeat')
import rules
from charts import SONGS

GAME_NAME = 'ThumbyBeat'
FPS = 30
# Note fall speeds in pixels per second, selectable on the song screen.
SPEEDS = (20, 30, 40, 50, 60)
DEFAULT_SPEED = 1

# Playfield geometry (72x40 screen). Lane order: S L R B A.
JUDGE_Y = 33
LANE_X = (1, 10, 17, 24, 31)
LANE_W = (8, 6, 6, 6, 6)
FIELD_RIGHT = 37
PANEL_X = 39
KEY_MS = 90           # key sound length
JUDGE_SHOW_MS = 600   # how long a judgment stays on screen
FLASH_MS = 100        # lane flash after a hit
PAUSE_HOLD_MS = 300   # A+B must be held this long to pause during play
DEMO_IDLE_MS = 8000   # title idle time before the demo starts
LAMP_SHORT = ('--', 'FAIL', 'CLR', 'FC')
PAUSE_ITEMS = ('CONTINUE', 'RETRY', 'QUIT')


def sprite(rows):
    """Convert '#'/'.' rows to Thumby's vertical-byte blit format."""
    width = len(rows[0])
    height = len(rows)
    data = bytearray(width * ((height + 7) // 8))
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char == '#':
                data[(y // 8) * width + x] |= 1 << (y % 8)
    return (data, width, height)


# Original 16x17 dancer with headphones.
_HEAD = (
    '.....######.....',
    '...##########...',
    '..##........##..',
    '.###.##..##.###.',
    '.###........###.',
    '.###..####..###.',
    '..##........##..',
    '...##########...',
)
_SAD_HEAD = _HEAD[:3] + (
    '.###........###.',
    '.###.##..##.###.',
    '.###........###.',
    '..##..####..##..',
    '...##########...',
)
_LEGS = (
    '.....######.....',
    '.....##..##.....',
    '.....##..##.....',
    '.....##..##.....',
    '....###..###....',
)
DANCER_DOWN = sprite(_HEAD + (
    '......####......',
    '...##########...',
    '..#..######..#..',
    '..#..######..#..',
    '.....######.....',
    '.....##..##.....',
    '....##....##....',
    '...##......##...',
    '..###......###..',
))
DANCER_UP = sprite(_HEAD + (
    '#.....####.....#',
    '.##.########.##.',
    '...##.####.##...',
    '.....######.....',
) + _LEGS)
DANCER_SAD = sprite(_SAD_HEAD + (
    '......####......',
    '....########....',
    '...#.######.#...',
    '...#.######.#...',
) + _LEGS)

JINGLES = {
    rules.LAMP_FAILED: ((392, 150), (330, 150), (262, 300)),
    rules.LAMP_CLEAR: ((523, 110), (659, 110), (784, 110), (1047, 250)),
    rules.LAMP_FULL_COMBO: ((523, 90), (659, 90), (784, 90), (1047, 90),
                            (784, 90), (1047, 300)),
}


# --- clock ------------------------------------------------------------------

def now_ms():
    # MicroPython uses wrap-safe ticks; CPython tests use a monotonic clock.
    if hasattr(time, 'ticks_ms'):
        return time.ticks_ms()
    return int(time.monotonic() * 1000)


def time_diff(a, b):
    if hasattr(time, 'ticks_diff'):
        return time.ticks_diff(a, b)
    return a - b


# --- state ------------------------------------------------------------------

def new_game(best=None, speed=DEFAULT_SPEED, now=0):
    return {
        'screen': 'title',
        'song': 0,
        'speed': speed,
        'best': best if best is not None else {},
        'play': None,
        'start': 0,
        'demo': False,
        'demo_song': 0,
        'menu_song': 0,
        'idle_since': now,
        'ab_hold_since': None,
        'pause_since': 0,
        'pause_sel': 0,
        'held': [False] * rules.LANE_COUNT,
        'flash': [-10000] * rules.LANE_COUNT,
        'sound_ms': -10000,
        'key_until': 0,
        'bgm_event': None,
        'bgm_playing': False,
        'jingle': None,
        'jingle_pos': 0,
        'jingle_next': 0,
        'result': None,
        'save_dirty': False,
    }


def read_inputs():
    # Call justPressed on every button each frame to keep its edge state fresh.
    taps = {}
    for name in ('U', 'D', 'L', 'R', 'A', 'B'):
        taps[name] = bool(getattr(thumby, 'button' + name).justPressed())
    held = {}
    for name in ('U', 'D', 'L', 'R', 'A', 'B'):
        held[name] = bool(getattr(thumby, 'button' + name).pressed())
    return make_inputs(taps, held)


def make_inputs(taps, held):
    lane_taps = [taps['U'] or taps['D'], taps['L'], taps['R'],
                 taps['B'], taps['A']]
    lane_held = [held['U'] or held['D'], held['L'], held['R'],
                 held['B'], held['A']]
    return {
        'tap': taps,
        'held': held,
        'lane_taps': lane_taps,
        'lane_held': lane_held,
        'any': any(taps.values()),
        # START: both held and one of them just went down.
        'start': held['A'] and held['B'] and (taps['A'] or taps['B']),
    }


def song_time(game, now):
    return time_diff(now, game['start'])


def beat_of(game, t):
    song = SONGS[game['song']]
    return (t * song['bpm']) // 60000 if t >= 0 else -1


# --- audio ------------------------------------------------------------------

def stop_audio(game):
    thumby.audio.stop()
    game['bgm_event'] = None
    game['bgm_playing'] = False
    game['key_until'] = 0


def key_sound(game, freq, t):
    if freq is None:
        return
    thumby.audio.play(freq, KEY_MS)
    game['key_until'] = t + KEY_MS
    game['bgm_playing'] = False
    game['sound_ms'] = t


def step_bgm(game, t):
    """Auto accompaniment; key sounds interrupt it and it resumes after."""
    event = rules.due_bgm(game['play'], t)
    if event is not None:
        game['bgm_event'] = event
        game['bgm_playing'] = False
    event = game['bgm_event']
    if event is None:
        return
    remaining = event[0] + event[2] - t
    if remaining <= 15:
        game['bgm_event'] = None
        game['bgm_playing'] = False
        return
    if not game['bgm_playing'] and t >= game['key_until']:
        thumby.audio.play(event[1], remaining)
        game['bgm_playing'] = True
        if t - event[0] < 40:
            game['sound_ms'] = t


def start_jingle(game, lamp, now):
    game['jingle'] = JINGLES.get(lamp)
    game['jingle_pos'] = 0
    game['jingle_next'] = now


def step_jingle(game, now):
    notes = game['jingle']
    if notes is None:
        return
    if time_diff(now, game['jingle_next']) < 0:
        return
    if game['jingle_pos'] >= len(notes):
        game['jingle'] = None
        return
    freq, length = notes[game['jingle_pos']]
    thumby.audio.play(freq, length - 10)
    game['jingle_pos'] += 1
    game['jingle_next'] = now + length


# --- screens ----------------------------------------------------------------

def start_song(game, now, demo=False):
    song = SONGS[game['song']]
    data = rules.load_song(song)
    game['play'] = rules.new_play(data['notes'], data['bgm'])
    game['start'] = now
    game['demo'] = demo
    game['screen'] = 'play'
    game['ab_hold_since'] = None
    game['flash'] = [-10000] * rules.LANE_COUNT
    game['sound_ms'] = -10000
    stop_audio(game)


def to_title(game, now):
    if game['demo']:
        game['song'] = game['menu_song']
    stop_audio(game)
    game['screen'] = 'title'
    game['demo'] = False
    game['play'] = None
    game['idle_since'] = now


def finish_song(game, now):
    play = game['play']
    stop_audio(game)
    if game['demo']:
        game['demo_song'] = (game['demo_song'] + 1) % len(SONGS)
        to_title(game, now)
        return
    song = SONGS[game['song']]
    note_count = len(play['notes'])
    ex = rules.ex_score(play['counts'])
    lamp = rules.lamp(play)
    old = game['best'].get(song['id'], [0, rules.LAMP_NONE])
    improved = rules.update_best(game['best'], song['id'], ex, lamp)
    if game['best'][song['id']] != old:
        game['save_dirty'] = True
    game['result'] = {
        'ex': ex,
        'max_ex': note_count * 2,
        'grade': rules.grade(ex, note_count),
        'lamp': lamp,
        'counts': list(play['counts']),
        'max_combo': play['max_combo'],
        'new_best': improved,
    }
    game['screen'] = 'result'
    start_jingle(game, lamp, now)


def step_title(game, inputs, now):
    if inputs['start'] or inputs['tap']['A']:
        game['screen'] = 'select'
        return
    if inputs['any']:
        game['idle_since'] = now
    elif time_diff(now, game['idle_since']) >= DEMO_IDLE_MS:
        game['menu_song'] = game['song']
        game['song'] = game['demo_song']
        start_song(game, now, demo=True)


def step_select(game, inputs, now):
    tap = inputs['tap']
    count = len(SONGS)
    if inputs['start'] or (tap['A'] and not inputs['held']['B']):
        start_song(game, now)
        return
    if tap['B'] and not inputs['held']['A']:
        game['screen'] = 'title'
        game['idle_since'] = now
        return
    if tap['U']:
        game['song'] = (game['song'] - 1) % count
    if tap['D']:
        game['song'] = (game['song'] + 1) % count
    if tap['L'] and game['speed'] > 0:
        game['speed'] -= 1
        game['save_dirty'] = True
    if tap['R'] and game['speed'] < len(SPEEDS) - 1:
        game['speed'] += 1
        game['save_dirty'] = True


def step_play(game, inputs, now):
    play = game['play']
    t = song_time(game, now)
    if game['demo']:
        if inputs['any']:
            to_title(game, now)
            return
        lanes = rules.auto_lanes(play, t)
        game['held'] = [lane in lanes for lane in range(rules.LANE_COUNT)]
    else:
        held = inputs['held']
        if held['A'] and held['B']:
            if game['ab_hold_since'] is None:
                game['ab_hold_since'] = now
            elif time_diff(now, game['ab_hold_since']) >= PAUSE_HOLD_MS:
                game['ab_hold_since'] = None
                game['screen'] = 'pause'
                game['pause_sel'] = 0
                game['pause_since'] = now
                stop_audio(game)
                return
        else:
            game['ab_hold_since'] = None
        lanes = [lane for lane in range(rules.LANE_COUNT)
                 if inputs['lane_taps'][lane]]
        game['held'] = list(inputs['lane_held'])
    for lane in lanes:
        judge, freq = rules.press(play, lane, t)
        key_sound(game, freq, t)
        if judge is not None and judge != rules.POOR:
            game['flash'][lane] = t
    rules.update_misses(play, t)
    step_bgm(game, t)
    if rules.is_finished(play, t):
        finish_song(game, now)


def step_pause(game, inputs, now):
    tap = inputs['tap']
    if tap['U']:
        game['pause_sel'] = (game['pause_sel'] - 1) % len(PAUSE_ITEMS)
    if tap['D']:
        game['pause_sel'] = (game['pause_sel'] + 1) % len(PAUSE_ITEMS)
    if tap['B'] and not inputs['held']['A']:
        game['pause_sel'] = 0
        tap = dict(tap, A=True)
    if tap['A'] and not inputs['held']['B']:
        choice = PAUSE_ITEMS[game['pause_sel']]
        if choice == 'CONTINUE':
            # Shift the song clock by the paused time so notes do not jump.
            game['start'] += time_diff(now, game['pause_since'])
            game['screen'] = 'play'
            game['bgm_event'] = None
        elif choice == 'RETRY':
            start_song(game, now)
        else:
            game['screen'] = 'select'


def step_result(game, inputs, now):
    step_jingle(game, now)
    tap = inputs['tap']
    if tap['A'] or tap['B']:
        thumby.audio.stop()
        game['jingle'] = None
        game['screen'] = 'select'


STEPS = {
    'title': step_title,
    'select': step_select,
    'play': step_play,
    'pause': step_pause,
    'result': step_result,
}


def step(game, inputs, now):
    STEPS[game['screen']](game, inputs, now)


# --- drawing ----------------------------------------------------------------

def text_right(display, text, right, y):
    display.drawText(text, right - len(text) * 6, y, 1)


def draw_dancer(display, game, x, y, t, beat):
    play = game['play']
    sad = False
    up = False
    if play is not None and play['last_judge'] is not None:
        recent = t - play['last_judge_ms'] < 400
        sad = recent and play['last_judge'] >= rules.BAD
        up = play['combo'] >= 10 and beat % 2 == 1
    if sad:
        frame = DANCER_SAD
        dx = 0
    elif up:
        frame = DANCER_UP
        dx = 0
    else:
        frame = DANCER_DOWN
        dx = -1 if beat % 2 == 0 else 1
    # Small bob at the start of each beat.
    dy = 1 if beat >= 0 and beat_phase(game, t) < 120 else 0
    data, width, height = frame
    display.blit(data, x + dx, y + dy, width, height, 0, 0, 0)


def beat_phase(game, t):
    song = SONGS[game['song']]
    beat_len = 60000 // song['bpm']
    return t % beat_len if t >= 0 else 0


def draw_bars(display, x_left, x_right, floor_y, t, sound_ms, beat):
    # Equalizer bars driven by how recently a sound started.
    level = 12 - (t - sound_ms) // 25
    if level < 0:
        level = 0
    for index, x in enumerate((x_left, x_left + 3, x_right, x_right + 3)):
        height = level - (3 if (index + beat) % 2 else 0)
        if height > 0:
            display.drawFilledRectangle(x, floor_y - height, 2, height, 1)


def draw_panel(display, game, t):
    play = game['play']
    beat = beat_of(game, t)
    display.drawLine(PANEL_X, 18, 71, 18, 1)
    draw_dancer(display, game, PANEL_X + 8, 1, t, beat)
    draw_bars(display, PANEL_X + 1, PANEL_X + 27, 17, t, game['sound_ms'], beat)
    if game['demo']:
        if (t // 500) % 2 == 0:
            display.drawText('DEMO', PANEL_X + 3, 20, 1)
    elif (play['last_judge'] is not None
            and t - play['last_judge_ms'] < JUDGE_SHOW_MS
            and (t // 66) % 4 != 3):
        name = rules.JUDGE_NAMES[play['last_judge']]
        display.drawText(name, PANEL_X + 1, 20, 1)
    if play['combo'] >= 2:
        text_right(display, str(play['combo']), 72, 28)
    # Groove gauge with a clear mark at 80 %.
    display.drawRectangle(PANEL_X, 36, 33, 4, 1)
    fill = (play['gauge'] * 31) // rules.GAUGE_MAX
    if fill > 0:
        display.drawFilledRectangle(PANEL_X + 1, 37, fill, 2, 1)
    mark = PANEL_X + 1 + (rules.GAUGE_CLEAR * 31) // rules.GAUGE_MAX
    display.drawLine(mark, 34, mark, 35, 1)


def draw_field(display, game, t):
    play = game['play']
    speed = SPEEDS[game['speed']]
    for x in (0, 9, 16, 23, 30, FIELD_RIGHT):
        display.drawLine(x, 0, x, JUDGE_Y, 1)
    display.drawLine(0, JUDGE_Y, FIELD_RIGHT, JUDGE_Y, 1)
    for lane in range(rules.LANE_COUNT):
        x = LANE_X[lane]
        w = LANE_W[lane]
        if t - game['flash'][lane] < FLASH_MS:
            display.drawFilledRectangle(x, JUDGE_Y - 3, w, 3, 1)
        if game['held'][lane]:
            display.drawFilledRectangle(x, 35, w, 5, 1)
        else:
            display.drawRectangle(x, 35, w, 5, 1)
    notes = play['notes']
    judged = play['judged']
    start, stop = rules.visible_range(play, t, JUDGE_Y, speed)
    for index in range(start, stop):
        if judged[index]:
            continue
        note = notes[index]
        y = rules.note_y(note[0], t, JUDGE_Y, speed)
        # Notes are 2 px tall (y-1..y); skip any that would leave the screen.
        if y < 1 or y > JUDGE_Y + 1:
            continue
        lane = note[1]
        display.drawFilledRectangle(LANE_X[lane], y - 1, LANE_W[lane], 2, 1)


def draw_play(display, game, now):
    t = song_time(game, now)
    display.fill(0)
    draw_field(display, game, t)
    draw_panel(display, game, t)


def draw_pause(display, game, now):
    display.fill(0)
    display.drawText('PAUSE', 21, 0, 1)
    for index, item in enumerate(PAUSE_ITEMS):
        y = 12 + index * 9
        if index == game['pause_sel']:
            display.drawFilledRectangle(4, y - 1, 64, 9, 1)
            display.drawText(item, 12, y, 0)
        else:
            display.drawText(item, 12, y, 1)


def draw_title(display, game, now):
    t = time_diff(now, game['idle_since'])
    display.fill(0)
    display.drawText('THUMBY BEAT', 3, 1, 1)
    beat = t // 500
    data, width, height = DANCER_UP if beat % 4 == 3 else DANCER_DOWN
    dx = 0 if beat % 4 == 3 else (-1 if beat % 2 == 0 else 1)
    display.blit(data, 28 + dx, 10, width, height, 0, 0, 0)
    sound_ms = beat * 500
    draw_bars(display, 16, 51, 26, t, sound_ms, beat)
    display.drawLine(10, 27, 61, 27, 1)
    if (t // 400) % 3 != 2:
        display.drawText('A+B START', 9, 31, 1)


_NOTE_COUNTS = {}


def song_note_count(index):
    # Parse once; drawing every frame must not re-parse the chart.
    if index not in _NOTE_COUNTS:
        _NOTE_COUNTS[index] = len(rules.load_song(SONGS[index])['notes'])
    return _NOTE_COUNTS[index]


def draw_select(display, game, now):
    song = SONGS[game['song']]
    display.fill(0)
    display.drawText(song['title'], 0, 0, 1)
    display.drawText('LV%d BPM%d' % (song['level'], song['bpm']), 0, 8, 1)
    best = game['best'].get(song['id'])
    if best:
        note_count = song_note_count(game['song'])
        display.drawText('HI%d %s' % (best[0], rules.grade(best[0], note_count)),
                         0, 16, 1)
        text_right(display, LAMP_SHORT[best[1]], 66, 24)
    else:
        display.drawText('HI --', 0, 16, 1)
    display.drawText('SPD%d' % (game['speed'] + 1), 0, 24, 1)
    # Up/down arrows hint at song switching.
    display.drawLine(68, 25, 70, 25, 1)
    display.drawLine(69, 24, 69, 24, 1)
    display.drawLine(68, 29, 70, 29, 1)
    display.drawLine(69, 30, 69, 30, 1)
    display.drawText('A:GO  B:BACK', 0, 33, 1)


def draw_result(display, game, now):
    result = game['result']
    counts = result['counts']
    display.fill(0)
    display.drawText(rules.LAMP_NAMES[result['lamp']], 0, 0, 1)
    display.drawText(result['grade'], 0, 8, 1)
    if result['new_best'] and (now // 300) % 2 == 0:
        text_right(display, 'NEW!', 72, 8)
    display.drawText('EX%d MX%d' % (result['ex'], result['max_combo']), 0, 16, 1)
    display.drawText('GR%d GD%d' % (counts[0], counts[1]), 0, 24, 1)
    display.drawText('BD%d PR%d' % (counts[2], counts[3]), 0, 32, 1)


DRAWS = {
    'title': draw_title,
    'select': draw_select,
    'play': draw_play,
    'pause': draw_pause,
    'result': draw_result,
}


def draw(game, now):
    DRAWS[game['screen']](thumby.display, game, now)


# --- save -------------------------------------------------------------------

def load_save():
    try:
        thumby.saveData.setName(GAME_NAME)
        if thumby.saveData.hasItem('data'):
            payload = json.loads(thumby.saveData.getItem('data'))
            return rules.decode_save(payload, [s['id'] for s in SONGS],
                                     len(SPEEDS))
    except Exception:
        pass
    return {}, DEFAULT_SPEED


def save_game(game):
    try:
        thumby.saveData.setName(GAME_NAME)
        thumby.saveData.setItem(
            'data', json.dumps(rules.encode_save(game['best'], game['speed'])))
        thumby.saveData.save()
        game['save_dirty'] = False
        return True
    except Exception:
        return False


def main_loop():
    thumby.display.setFPS(FPS)
    best, speed = load_save()
    game = new_game(best, speed, now_ms())
    while True:
        now = now_ms()
        step(game, read_inputs(), now)
        # Save outside of play so flash writes never stall the song.
        if game['save_dirty'] and game['screen'] in ('select', 'result'):
            save_game(game)
        draw(game, now)
        thumby.display.update()


if sys.implementation.name == 'micropython':
    main_loop()
