# Arrangement of "Flight of the Bumblebee" (Nikolai Rimsky-Korsakov,
# 1900, public domain).
from pat import bars, clicks, join, rest

_B1 = 'E6 D#6 D6 C#6 D6 C#6 C6 B5 C6 B5 A#5 A5 G#5 G5 F#5 F5'
_B2 = 'E5 F5 E5 D#5 E5 F5 E5 D#5 E5 F5 E5 D#5 E5 . S .'
_B3 = 'E5 D#5 D5 C#5 C5 F5 E5 D#5 E5 D#5 D5 C#5 C5 C#5 D5 D#5'
_B4 = 'E5 F5 F#5 G5 G#5 A5 A#5 B5 C6 C#6 D6 D#6 E6 . S .'
_HYPER = '@0 . @12 . @0 . @12 . @0 . @12 . @0 . @12 .'

SONG = {
    'id': 'bumble', 'title': 'BUMBLEBEE', 'genre': 'HYPER TECHNO',
    'level': 9, 'bpm': 128, 'step_div': 4, 'beats_per_bar': 4,
    'chart': join(rest(16), _B1, _B2, _B3, _B4, _B1, _B2, _B3, _B4,
                  _B1, _B2, _B3, 'E6 . . . S . S . E5 . . . . . . .'),
    'bgm': join(clicks(4, 4, 'E5'),
                bars(_HYPER, ['E3', 'E3', 'A3', 'B2'] * 2
                     + ['E3', 'E3', 'A3', 'E3'])),
}
