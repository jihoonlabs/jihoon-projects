"""Songs for Thumby Beat.

Chart steps: '.' rest, lane letter (S L R B A) + pitch = note, '|' bar.
BGM steps: pitch, '-' hold, '.' rest. Charts never have two notes at the
same time (A+B together is reserved for START).

CHOPSTICKS is an arrangement of "The Celebrated Chop Waltz" (Euphemia
Allen, 1877, public domain). The other songs are original to this game.
"""


def _bars(*parts):
    return ' | '.join(parts)


# --- 1. CHOPSTICKS (easy, 3/4, eighth-note steps) ---------------------------
_FG = 'LF5 RG5 LF5 RG5 LF5 RG5'
_EG = 'BE5 AG5 BE5 AG5 BE5 AG5'
_DB = 'LD5 RB5 LD5 RB5 LD5 RB5'
_CC = 'BC5 AC6 BC5 AC6 BC5 AC6'
_TURN = 'BC5 AC6 LB4 RD6 LA4 RE6'
_CHOP_A = _bars(_FG, _FG, _EG, _EG, _DB, _DB, _CC, _TURN)
_CHOP_B = _bars('LC5 . RE5 . BG5 .', 'AC6 . . . S .',
                'LD5 . RF5 . BA5 .', 'AD6 . . . S .')
_REST6 = '. . . . . .'

_G7 = 'G3 - B3 . B3 .'
_C = 'C4 - E4 . E4 .'
_G7B = 'G3 - F4 . F4 .'
_CEND = 'C4 - G3 . G3 .'
_CHOP_BGM_A = _bars(_G7, _G7, _C, _C, _G7B, _G7B, _C, _CEND)
_CHOP_BGM_B = _bars(_C, _C, 'D4 - F4 . F4 .', _G7)

CHOPSTICKS = {
    'id': 'chop',
    'title': 'CHOPSTICKS',
    'level': 2,
    'bpm': 120,
    'step_div': 2,
    'beats_per_bar': 3,
    'chart': _bars(_REST6, _CHOP_A, _CHOP_A, _CHOP_B, _CHOP_A,
                   'BC5 AC6 BC5 . S .', 'LC5 . . . . .'),
    'bgm': _bars('C6 . C6 . C6 .', _CHOP_BGM_A, _CHOP_BGM_A, _CHOP_BGM_B,
                 _CHOP_BGM_A, _C, 'C4 - - - . .'),
}


# --- 2. NEON STEPS (normal, 4/4, sixteenth-note steps, original) ------------
_REST16 = '. . . . . . . . . . . . . . . .'


def _bass(low, high):
    return ' '.join([low + ' . ' + high + ' .'] * 4)


_NEON_A = _bars(
    'LA4 . RC5 . BE5 . RC5 . LA4 . RC5 . AE5 . . .',
    'LG4 . RB4 . BD5 . RB4 . LG4 . RB4 . AD5 . S .',
    'LF4 . RA4 . BC5 . RA4 . LF4 . RA4 . AC5 . BD5 .',
    'AE5 . . . BD5 . . . RC5 . . . RB4 . S .')
_NEON_B1 = 'AE5 . BD5 . AE5 . BD5 . AE5 . RC5 . LB4 . . .'
_NEON_B2 = 'AA5 . BG5 . AE5 . BD5 . RC5 . LB4 . BC5 . . .'
_NEON_B3 = 'AE5 . BD5 . AE5 . BD5 . AE5 . RC5 . LD5 . . .'
_NEON_B4 = 'RE5 . . . S . S . LE4 . . . S . . .'
_NEON_BGM_A = _bars(_bass('A3', 'A4'), _bass('G3', 'G4'),
                    _bass('F3', 'F4'), _bass('E3', 'E4'))
_NEON_BGM_B = _bars(_bass('C4', 'C5'), _bass('G3', 'G4'),
                    _bass('A3', 'A4'), _bass('E3', 'E4'))

NEON_STEPS = {
    'id': 'neon',
    'title': 'NEON STEPS',
    'level': 5,
    'bpm': 128,
    'step_div': 4,
    'beats_per_bar': 4,
    'chart': _bars(_REST16, _NEON_A, _NEON_B1, _NEON_B2, _NEON_B3, _NEON_B4,
                   _NEON_A, _NEON_B1, _NEON_B2, _NEON_B3,
                   'AA4 . . . . . . . S . . . . . . .'),
    'bgm': _bars('A5 . . . A5 . . . A5 . . . A5 . . .',
                 _NEON_BGM_A, _NEON_BGM_B, _NEON_BGM_A,
                 _bass('C4', 'C5'), _bass('G3', 'G4'), _bass('A3', 'A4'),
                 'A3 - - - - - - - . . . . . . . .'),
}


# --- 3. STAR CIRCUIT (hard, 4/4, sixteenth-note steps, original) ------------
_STAR_C = _bars(
    'S . LE5 . RG5 . BB5 . AE6 . BB5 . RG5 . LE5 .',
    'S . LD5 . RF#5 . BA5 . AD6 . BA5 . RF#5 . LD5 .',
    'S . LC5 . RE5 . BG5 . AC6 . BG5 . RE5 . LC5 .',
    'S . LB4 . RD#5 . BF#5 . AB5 . . S . S . .')
_STAR_D1 = 'AE6 . BD6 . AB5 . BA5 . RG5 . LF#5 . RG5 . BA5 .'
_STAR_D2 = 'AB5 . . BA5 . . RG5 . LE5 . . . S . . .'
_STAR_D3 = 'AE6 . BD6 . AB5 . BA5 . RG5 . LA5 . RB5 . BC6 .'
_STAR_D4 = 'AB5 . . . S . S . LE5 . . . S S S .'
_STAR_BGM_C = _bars(_bass('E3', 'E4'), _bass('D3', 'D4'),
                    _bass('C3', 'C4'), _bass('B2', 'B3'))
_STAR_BGM_D = _bars(_bass('C3', 'C4'), _bass('D3', 'D4'),
                    _bass('B2', 'B3'), _bass('E3', 'E4'))

STAR_CIRCUIT = {
    'id': 'star',
    'title': 'STAR CIRCUIT',
    'level': 8,
    'bpm': 150,
    'step_div': 4,
    'beats_per_bar': 4,
    'chart': _bars(_REST16, _STAR_C, _STAR_D1, _STAR_D2, _STAR_D3, _STAR_D4,
                   _STAR_C, _STAR_D1, _STAR_D2, _STAR_D3,
                   'LE5 . . . S . . . . . . . . . . .'),
    'bgm': _bars('E5 . . . E5 . . . E5 . . . E5 . . .',
                 _STAR_BGM_C, _STAR_BGM_D, _STAR_BGM_C,
                 _bass('C3', 'C4'), _bass('D3', 'D4'), _bass('B2', 'B3'),
                 'E3 - - - - - - - . . . . . . . .'),
}

SONGS = (CHOPSTICKS, NEON_STEPS, STAR_CIRCUIT)
