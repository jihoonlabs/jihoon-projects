# Arrangement of "In the Hall of the Mountain King" (Edvard Grieg,
# Peer Gynt, 1875, public domain). Transposed to E minor.
from pat import bars, clicks, join, rest

_P = join('E5 . F#5 . G5 . A5 . B5 . G5 . B5 . . .',
          'A#5 . F#5 . A#5 . . . A5 . F5 . A5 . . .',
          'E5 . F#5 . G5 . A5 . B5 . G5 . B5 . E6 .',
          'D6 . B5 . G5 . B5 . D6 . . . . . . .')
_P2 = join('E5 . F#5 . G5 . A5 . B5 . G5 . B5 . S .',
           'A#5 . F#5 . A#5 . S . A5 . F5 . A5 . S .',
           'E5 . F#5 . G5 . A5 . B5 . G5 . B5 . E6 .',
           'D6 . B5 . G5 . B5 . D6 . . . S . S .')
_Q = join('A5 . B5 . C6 . D6 . E6 . C6 . E6 . . .',
          'D#6 . B5 . D#6 . . . D6 . A#5 . D6 . . .',
          'A5 . B5 . C6 . D6 . E6 . C6 . E6 . A6 .',
          'G6 . E6 . C6 . E6 . G6 . . . S . . .')
_F = join('E5 F#5 G5 A5 B5 G5 B5 . A#5 F#5 A#5 . A5 F5 A5 .',
          'E5 F#5 G5 A5 B5 G5 B5 E6 D6 B5 G5 B5 D6 . S .')
_HARD = '@0 @12 @0 @12 @0 @12 @0 @12 @0 @12 @0 @12 @0 @12 @0 @12'
_ROOTS_P = ['E3', 'B2', 'E3', 'G3']
_ROOTS_Q = ['A3', 'B3', 'A3', 'C4']

SONG = {
    'id': 'king', 'title': 'HALL OF KING', 'genre': 'HARDCORE',
    'level': 7, 'bpm': 140, 'step_div': 4, 'beats_per_bar': 4,
    'chart': join(rest(16), _P, _P2, _Q, _P2, _F,
                  'E6 . . . S . S . E5 . . . . . . .'),
    'bgm': join(clicks(4, 4, 'E5'),
                bars(_HARD, _ROOTS_P * 2 + _ROOTS_Q + _ROOTS_P
                     + ['E3', 'E3', 'E3'])),
}
