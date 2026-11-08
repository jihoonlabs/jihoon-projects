"""Thumby Beat game rules: charts, judgments, score, gauge and saves.

Pure logic without the thumby module so CPython tests can run it.
All times are integer milliseconds from the start of the song.
"""

# Lane order on screen, left to right.
SCRATCH, KEY_L, KEY_R, KEY_B, KEY_A = 0, 1, 2, 3, 4
LANE_COUNT = 5
LANE_CHARS = 'SLRBA'

GREAT, GOOD, BAD, POOR = 0, 1, 2, 3
JUDGE_NAMES = ('GREAT', 'GOOD', 'BAD', 'POOR')
# Timing windows in ms (absolute offset from the note time).
GREAT_MS = 50
GOOD_MS = 100
BAD_MS = 150

# Groove gauge in 0.1 % units.
GAUGE_MAX = 1000
GAUGE_START = 220
GAUGE_CLEAR = 800
GAUGE_TOTAL = 1800
BAD_LOSS = 20
POOR_LOSS = 60

# A note in the same lane needs at least this gap so it can be pressed again.
MIN_SAME_LANE_MS = 100
SCRATCH_FREQ = 180

LAMP_NONE, LAMP_FAILED, LAMP_CLEAR, LAMP_FULL_COMBO = 0, 1, 2, 3
LAMP_NAMES = ('NO PLAY', 'FAILED', 'CLEAR', 'FULL COMBO')

SAVE_VERSION = 1

_NOTE_OFFSETS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def note_freq(name):
    """'A4' -> 440, 'F#5' -> 740. Octave is a single digit 1-8."""
    if len(name) < 2 or name[0] not in _NOTE_OFFSETS:
        raise ValueError('bad note: ' + name)
    semitone = _NOTE_OFFSETS[name[0]]
    rest = name[1:]
    if rest[0] == '#':
        semitone += 1
        rest = rest[1:]
    elif rest[0] == 'b':
        semitone -= 1
        rest = rest[1:]
    if len(rest) != 1 or not ('1' <= rest <= '8'):
        raise ValueError('bad note: ' + name)
    midi = (int(rest) + 1) * 12 + semitone
    return int(440 * 2 ** ((midi - 69) / 12) + 0.5)


def step_ms(bpm, step_div, step):
    # step_div steps per beat; integer rounding per step avoids drift.
    return (step * 60000) // (bpm * step_div)


def parse_chart(text, bpm, step_div):
    """Parse whitespace-separated steps into notes [time, lane, freq].

    '.' is a rest, '|' is an ignored measure bar. A note is a lane letter
    (S L R B A) plus an optional pitch, e.g. 'LC5'; '+' joins a chord.
    A scratch without a pitch uses SCRATCH_FREQ.
    """
    notes = []
    step = 0
    for token in text.split():
        if token == '|':
            continue
        if token != '.':
            t = step_ms(bpm, step_div, step)
            for part in token.split('+'):
                if not part or part[0] not in LANE_CHARS:
                    raise ValueError('bad chart token: ' + token)
                lane = LANE_CHARS.index(part[0])
                if len(part) > 1:
                    freq = note_freq(part[1:])
                elif lane == SCRATCH:
                    freq = SCRATCH_FREQ
                else:
                    raise ValueError('key note needs a pitch: ' + token)
                notes.append([t, lane, freq])
        step += 1
    notes.sort(key=lambda n: (n[0], n[1]))
    return notes


def parse_bgm(text, bpm, step_div):
    """Parse BGM steps into events (time, freq, duration).

    A pitch starts a note, '-' extends the previous note by one step,
    '.' is a rest and '|' is ignored.
    """
    events = []
    step = 0
    current = None
    for token in text.split():
        if token == '|':
            continue
        if token == '-':
            if current is None:
                raise ValueError("'-' without a note")
            current[2] += 1
        else:
            if current is not None:
                events.append(current)
                current = None
            if token != '.':
                current = [step, note_freq(token), 1]
        step += 1
    if current is not None:
        events.append(current)
    result = []
    for start, freq, length in events:
        t0 = step_ms(bpm, step_div, start)
        t1 = step_ms(bpm, step_div, start + length)
        # Short gap so repeated notes are heard as separate notes.
        result.append((t0, freq, max(20, t1 - t0 - 15)))
    return result


def chart_problems(notes):
    """Return a list of human-readable problems; empty means playable."""
    # No chords at all: A+B together is reserved for START.
    problems = []
    last_time = None
    last_in_lane = [None] * LANE_COUNT
    for t, lane, _freq in notes:
        if t == last_time:
            problems.append('two notes at %d' % t)
        last_time = t
        prev = last_in_lane[lane]
        if prev is not None and t - prev < MIN_SAME_LANE_MS:
            problems.append('lane %s too dense at %d' % (LANE_CHARS[lane], t))
        last_in_lane[lane] = t
    return problems


def load_song(song):
    """Build parsed note/BGM lists for a song definition from charts.py."""
    bpm = song['bpm']
    div = song['step_div']
    return {
        'notes': parse_chart(song['chart'], bpm, div),
        'bgm': parse_bgm(song['bgm'], bpm, div),
    }


def gauge_gain(note_count):
    return max(4, GAUGE_TOTAL // max(1, note_count))


def new_play(notes, bgm):
    lanes = [[] for _ in range(LANE_COUNT)]
    for index, note in enumerate(notes):
        lanes[note[1]].append(index)
    end_ms = 0
    if notes:
        end_ms = notes[-1][0]
    if bgm:
        last = bgm[-1]
        end_ms = max(end_ms, last[0] + last[2])
    return {
        'notes': notes,
        'bgm': bgm,
        'lanes': lanes,
        # Per-lane index into lanes[lane] of the first unjudged note.
        'lane_pos': [0] * LANE_COUNT,
        'judged': bytearray(len(notes)),
        'bgm_pos': 0,
        'counts': [0, 0, 0, 0],
        'combo': 0,
        'max_combo': 0,
        'gauge': GAUGE_START,
        'gain': gauge_gain(len(notes)),
        'last_judge': None,
        'last_judge_ms': -10000,
        'last_lane': None,
        'end_ms': end_ms + 1000,
    }


def judge_for_offset(offset):
    offset = abs(offset)
    if offset <= GREAT_MS:
        return GREAT
    if offset <= GOOD_MS:
        return GOOD
    if offset <= BAD_MS:
        return BAD
    return None


def _apply(play, judge, now):
    play['counts'][judge] += 1
    if judge == GREAT or judge == GOOD:
        play['combo'] += 1
        if play['combo'] > play['max_combo']:
            play['max_combo'] = play['combo']
        gain = play['gain'] if judge == GREAT else play['gain'] // 2
        play['gauge'] = min(GAUGE_MAX, play['gauge'] + gain)
    else:
        play['combo'] = 0
        loss = BAD_LOSS if judge == BAD else POOR_LOSS
        play['gauge'] = max(0, play['gauge'] - loss)
    play['last_judge'] = judge
    play['last_judge_ms'] = now


def lane_keysound(play, lane):
    """Pitch a press in this lane makes: the next unjudged note, else the last one."""
    indices = play['lanes'][lane]
    if not indices:
        return SCRATCH_FREQ if lane == SCRATCH else None
    pos = play['lane_pos'][lane]
    if pos >= len(indices):
        pos = len(indices) - 1
    return play['notes'][indices[pos]][2]


def press(play, lane, now):
    """Handle a key press. Returns (judge or None, freq or None)."""
    indices = play['lanes'][lane]
    pos = play['lane_pos'][lane]
    freq = lane_keysound(play, lane)
    if pos < len(indices):
        index = indices[pos]
        note = play['notes'][index]
        judge = judge_for_offset(now - note[0])
        if judge is not None:
            play['judged'][index] = 1
            play['lane_pos'][lane] = pos + 1
            play['last_lane'] = lane
            _apply(play, judge, now)
            return judge, note[2]
    # Too early: no judgment, but the key still makes its sound.
    return None, freq


def auto_lanes(play, now):
    """Demo mode: lanes whose next unjudged note time has been reached."""
    lanes = []
    for lane in range(LANE_COUNT):
        indices = play['lanes'][lane]
        pos = play['lane_pos'][lane]
        if pos < len(indices) and play['notes'][indices[pos]][0] <= now:
            lanes.append(lane)
    return lanes


def update_misses(play, now):
    """Judge POOR for notes that passed the BAD window. Returns miss count."""
    missed = 0
    for lane in range(LANE_COUNT):
        indices = play['lanes'][lane]
        pos = play['lane_pos'][lane]
        while pos < len(indices):
            index = indices[pos]
            if now - play['notes'][index][0] <= BAD_MS:
                break
            play['judged'][index] = 1
            pos += 1
            missed += 1
            _apply(play, POOR, now)
        play['lane_pos'][lane] = pos
    return missed


def due_bgm(play, now):
    """Return the latest BGM event whose start time has passed, or None."""
    bgm = play['bgm']
    pos = play['bgm_pos']
    latest = None
    while pos < len(bgm) and bgm[pos][0] <= now:
        latest = bgm[pos]
        pos += 1
    play['bgm_pos'] = pos
    return latest


def is_finished(play, now):
    return now >= play['end_ms'] and all(
        play['lane_pos'][lane] >= len(play['lanes'][lane])
        for lane in range(LANE_COUNT))


def ex_score(counts):
    return counts[GREAT] * 2 + counts[GOOD]


def grade(ex, note_count):
    """Letter grade from the EX ratio in ninths."""
    if note_count <= 0:
        return 'F'
    top = note_count * 2
    for ninths, letter in ((8, 'AAA'), (7, 'AA'), (6, 'A'), (5, 'B'),
                           (4, 'C'), (3, 'D'), (2, 'E')):
        if ex * 9 >= top * ninths:
            return letter
    return 'F'


def lamp(play):
    if play['gauge'] < GAUGE_CLEAR:
        return LAMP_FAILED
    counts = play['counts']
    if counts[BAD] == 0 and counts[POOR] == 0:
        return LAMP_FULL_COMBO
    return LAMP_CLEAR


def note_y(note_ms, now, judge_y, px_per_sec):
    """Screen y of a note; the judge line is reached at note time."""
    return judge_y - ((note_ms - now) * px_per_sec) // 1000


def visible_range(play, now, judge_y, px_per_sec, top=-2):
    """Indexes (start, stop) of notes that may be on screen (sorted notes)."""
    notes = play['notes']
    # +1 px covers the floor division in note_y.
    lead_ms = ((judge_y - top + 1) * 1000) // px_per_sec
    lo = now - BAD_MS
    hi = now + lead_ms
    start = 0
    count = len(notes)
    # Binary search for the first note with time >= lo.
    end = count
    while start < end:
        mid = (start + end) // 2
        if notes[mid][0] < lo:
            start = mid + 1
        else:
            end = mid
    stop = start
    while stop < count and notes[stop][0] <= hi:
        stop += 1
    return start, stop


def update_best(best, song_id, ex, new_lamp):
    """Merge a result into best records. Returns True if the score improved."""
    old = best.get(song_id, [0, LAMP_NONE])
    improved = ex > old[0]
    best[song_id] = [max(ex, old[0]), max(new_lamp, old[1])]
    return improved


def encode_save(best, speed_index):
    return {'version': SAVE_VERSION, 'best': best, 'speed': speed_index}


def decode_save(payload, song_ids, speed_count):
    """Validate saved data; unknown or broken entries are dropped."""
    best = {}
    speed = 0
    if not isinstance(payload, dict) or payload.get('version') != SAVE_VERSION:
        return best, speed
    raw = payload.get('best')
    if isinstance(raw, dict):
        for song_id in song_ids:
            entry = raw.get(song_id)
            if (isinstance(entry, list) and len(entry) == 2
                    and all(type(v) is int for v in entry)
                    and entry[0] >= 0 and LAMP_NONE <= entry[1] <= LAMP_FULL_COMBO):
                best[song_id] = [entry[0], entry[1]]
    raw_speed = payload.get('speed')
    if type(raw_speed) is int and 0 <= raw_speed < speed_count:
        speed = raw_speed
    return best, speed
