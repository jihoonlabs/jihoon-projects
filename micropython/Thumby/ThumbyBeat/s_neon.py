# Original song for Thumby Beat.
from pat import bars, clicks, join, rest

_A = join('LA4 . RC5 . BE5 . RC5 . LA4 . RC5 . AE5 . . .',
          'LG4 . RB4 . BD5 . RB4 . LG4 . RB4 . AD5 . S .',
          'LF4 . RA4 . BC5 . RA4 . LF4 . RA4 . AC5 . BD5 .',
          'AE5 . . . BD5 . . . RC5 . . . RB4 . S .')
_B1 = 'AE5 . BD5 . AE5 . BD5 . AE5 . RC5 . LB4 . . .'
_B2 = 'AA5 . BG5 . AE5 . BD5 . RC5 . LB4 . BC5 . . .'
_B3 = 'AE5 . BD5 . AE5 . BD5 . AE5 . RC5 . LD5 . . .'
_B4 = 'RE5 . . . S . S . LE4 . . . S . . .'
_TECHNO = '@0 . @12 . @0 . @12 . @0 . @12 . @0 . @12 .'

SONG = {
    'id': 'neon', 'title': 'NEON STEPS', 'genre': 'TECHNO',
    'level': 5, 'bpm': 128, 'step_div': 4, 'beats_per_bar': 4,
    'chart': join(rest(16), _A, _B1, _B2, _B3, _B4, _A, _B1, _B2, _B3,
                  'AA4 . . . . . . . S . . . . . . .'),
    'bgm': join(clicks(4, 4, 'A5'),
                bars(_TECHNO, ['A3', 'G3', 'F3', 'E3', 'C4', 'G3', 'A3', 'E3',
                               'A3', 'G3', 'F3', 'E3', 'C4', 'G3', 'A3']),
                'A3 - - - - - - - . . . . . . . .'),
}
