# Arrangement of "Ode to Joy" (Beethoven, Symphony No. 9, 1824,
# public domain).
from pat import bars, clicks, join, rest

_P1 = join('E5 . E5 . F5 . G5 .', 'G5 . F5 . E5 . D5 .',
           'C5 . C5 . D5 . E5 .', 'E5 . . D5 D5 . . .')
_P2 = join('E5 . E5 . F5 . G5 .', 'G5 . F5 . E5 . D5 .',
           'C5 . C5 . D5 . E5 .', 'D5 . . C5 C5 . S .')
_P3 = join('D5 . D5 . E5 . C5 .', 'D5 . E5 F5 E5 . C5 .',
           'D5 . E5 F5 E5 . D5 .', 'C5 . D5 . G4 . S .')
_HOUSE = '@0 @12 @0 @12 @0 @12 @0 @12'

SONG = {
    'id': 'ode', 'title': 'ODE TO JOY', 'genre': 'EURO HOUSE',
    'level': 2, 'bpm': 124, 'step_div': 2, 'beats_per_bar': 4,
    'chart': join(rest(8), _P1, _P2, _P3, _P2, 'C5 . . . S . . .'),
    'bgm': join(clicks(2, 4, 'C6'),
                bars(_HOUSE, ['C3', 'G3', 'C3', 'G3', 'C3', 'G3', 'C3', 'C3',
                              'G3', 'C3', 'G3', 'G3', 'C3', 'G3', 'C3', 'C3',
                              'C3'])),
}
