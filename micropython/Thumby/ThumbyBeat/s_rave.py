# Original song for Thumby Beat.
from pat import bars, clicks, join, rest

_A = join('A5 . A5 . C6 . A5 . E6 . . . D6 . C6 .',
          'B5 . . . G5 . . . B5 . D6 . B5 . G5 .',
          'A5 . C6 . E6 . A6 . G6 . E6 . C6 . E6 .',
          'D6 C6 B5 A5 G5 . B5 . A5 . . . S S S .',
          'A5 . A5 . C6 . A5 . E6 . . . D6 . C6 .',
          'B5 . . . G5 . . . B5 . D6 . B5 . G5 .',
          'F5 . A5 . C6 . F6 . E6 . C6 . A5 . C6 .',
          'B5 . G#5 . E5 . G#5 . B5 . E6 . S . S .')
_RAVE = '@0 . @12 @12 @0 . @12 @12 @0 . @12 @12 @0 . @12 @12'
_ROOTS = ['A3', 'G3', 'A3', 'E3', 'A3', 'G3', 'F3', 'E3']

SONG = {
    'id': 'rave', 'title': 'BEEP RAVE', 'genre': 'RAVE',
    'level': 7, 'bpm': 145, 'step_div': 4, 'beats_per_bar': 4,
    'chart': join(rest(16), _A, _A, 'A5 . . . . . . . S . . . . . . .'),
    'bgm': join(clicks(4, 4, 'A5'), bars(_RAVE, _ROOTS * 2 + ['A3'])),
}
