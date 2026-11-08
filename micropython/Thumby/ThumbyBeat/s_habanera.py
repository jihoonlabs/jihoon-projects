# Arrangement of the "Habanera" from "Carmen" (Georges Bizet, 1875,
# public domain).
from pat import bars, clicks, join, rest

_A = join('D5 . . C#5 C5 . C5 .', 'B4 . . A#4 A4 . A4 .',
          'G#4 . G4 . F#4 . F4 .', 'E4 . F4 E4 D#4 . E4 .',
          'F4 . E4 . F4 . S .')
_A2 = join('D5 . . C#5 C5 . C5 .', 'B4 . . A#4 A4 . A4 .',
           'G#4 . G4 . F#4 . F4 .', 'E4 . F4 E4 D#4 . E4 .',
           'D4 . . . S . S .')
_HAB = '@0 . . @7 @12 . @7 .'
_ROOTS = ['D3', 'A3', 'A3', 'A3', 'D3']

SONG = {
    'id': 'habanera', 'title': 'HABANERA', 'genre': 'LATIN',
    'level': 5, 'bpm': 104, 'step_div': 4, 'beats_per_bar': 2,
    'chart': join(rest(8), _A, _A2, _A, _A2, _A2),
    'bgm': join(clicks(4, 2, 'D6'), bars(_HAB, _ROOTS * 5)),
}
