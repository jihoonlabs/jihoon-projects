# Arrangement of the finale of the "William Tell" overture
# (Gioachino Rossini, 1829, public domain).
from pat import bars, clicks, join, rest

_G1 = 'E5 E5 E5 . E5 E5 E5 . E5 E5 A5 . B5 . C#6 .'
_G2 = 'E5 E5 E5 . E5 E5 A5 . C#6 . A5 . . . S .'
_G4 = 'E5 E5 A5 . C#6 . B5 . G#5 . E5 . S . . .'
_B = join('C#6 . C#6 . C#6 . B5 . A5 . . . G#5 . . .',
          'F#5 . F#5 . F#5 . G#5 . A5 . . . E5 . S .')
_GALLOP = '@0 . @0 @12 @0 . @0 @12 @0 . @0 @12 @0 . @0 @12'

SONG = {
    'id': 'tell', 'title': 'WILLIAM TELL', 'genre': 'BIG BEAT',
    'level': 7, 'bpm': 140, 'step_div': 4, 'beats_per_bar': 4,
    'chart': join(rest(16), _G1, _G2, _G1, _G4, _B, _G1, _G2, _G1, _G4,
                  _B, _G1, _G2, _G1, _G4, 'A5 . . . S . S . A4 . . . . . . .'),
    'bgm': join(clicks(4, 4, 'E5'),
                bars(_GALLOP, ['A3', 'A3', 'A3', 'E3', 'A3', 'E3'] * 2
                     + ['A3', 'A3', 'A3', 'E3', 'A3'])),
}
