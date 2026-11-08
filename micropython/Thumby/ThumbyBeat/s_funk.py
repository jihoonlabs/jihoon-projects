# Original song for Thumby Beat.
from pat import bars, clicks, join, rest

_A = join('E5 . . G5 . A5 . . G5 . E5 . . . S .',
          'D5 . . E5 . G5 . . E5 . D5 . C5 . . .',
          'E5 . . G5 . A5 . . C6 . A5 . G5 . E5 .',
          'D5 . E5 . . . D5 . C5 . . . S . S .')
_FUNK = '@0 . . @0 . . @12 . @0 . @10 . @12 . . .'

SONG = {
    'id': 'funk', 'title': 'PIXEL FUNK', 'genre': 'FUNK',
    'level': 3, 'bpm': 108, 'step_div': 4, 'beats_per_bar': 4,
    'chart': join(rest(16), _A, _A, _A),
    'bgm': join(clicks(4, 4, 'E5'),
                bars(_FUNK, ['E3', 'D3', 'E3', 'A3'] * 3)),
}
