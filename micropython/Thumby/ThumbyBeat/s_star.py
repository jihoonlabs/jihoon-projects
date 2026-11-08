# Original song for Thumby Beat.
from pat import bars, clicks, join, rest

_C = join('S . LE5 . RG5 . BB5 . AE6 . BB5 . RG5 . LE5 .',
          'S . LD5 . RF#5 . BA5 . AD6 . BA5 . RF#5 . LD5 .',
          'S . LC5 . RE5 . BG5 . AC6 . BG5 . RE5 . LC5 .',
          'S . LB4 . RD#5 . BF#5 . AB5 . . S . S . .')
_D1 = 'AE6 . BD6 . AB5 . BA5 . RG5 . LF#5 . RG5 . BA5 .'
_D2 = 'AB5 . . BA5 . . RG5 . LE5 . . . S . . .'
_D3 = 'AE6 . BD6 . AB5 . BA5 . RG5 . LA5 . RB5 . BC6 .'
_D4 = 'AB5 . . . S . S . LE5 . . . S S S .'
_DNB = '@0 . . . . . @12 . . . @0 . @7 . . .'

SONG = {
    'id': 'star', 'title': 'STAR CIRCUIT', 'genre': 'DRUM N BASS',
    'level': 8, 'bpm': 150, 'step_div': 4, 'beats_per_bar': 4,
    'chart': join(rest(16), _C, _D1, _D2, _D3, _D4, _C, _D1, _D2, _D3,
                  'LE5 . . . S . . . . . . . . . . .'),
    'bgm': join(clicks(4, 4, 'E5'),
                bars(_DNB, ['E3', 'D3', 'C3', 'B2', 'C3', 'D3', 'B2', 'E3',
                            'E3', 'D3', 'C3', 'B2', 'C3', 'D3', 'B2']),
                'E3 - - - - - - - . . . . . . . .'),
}
