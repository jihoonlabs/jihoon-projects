# Arrangement of "Jingle Bells" (James Lord Pierpont, 1857,
# public domain).
from pat import bars, clicks, join, rest

_A = join('E5 . E5 . E5 . . .', 'E5 . E5 . E5 . . .',
          'E5 . G5 . C5 . . D5', 'E5 . . . . . S .')
_B1 = join('F5 . F5 . F5 . . F5', 'F5 . E5 . E5 . E5 E5',
           'E5 . D5 . D5 . E5 .', 'D5 . . . G5 . . .')
_B2 = join('F5 . F5 . F5 . . F5', 'F5 . E5 . E5 . E5 E5',
           'G5 . G5 . F5 . D5 .', 'C5 . . . S . . .')
_WALK = '@0 . @4 . @7 . @9 .'

SONG = {
    'id': 'jingle', 'title': 'JINGLE BELLS', 'genre': 'SWING',
    'level': 2, 'bpm': 140, 'step_div': 2, 'beats_per_bar': 4,
    'chart': join(rest(8), _A, _B1, _A, _B2),
    'bgm': join(clicks(2, 4, 'C6'),
                bars(_WALK, ['C3', 'C3', 'C3', 'C3', 'F3', 'C3', 'D3', 'G3',
                             'C3', 'C3', 'C3', 'C3', 'F3', 'C3', 'G3', 'C3'])),
}
