# Arrangement of the main theme of "Swan Lake" (Tchaikovsky, 1876,
# public domain).
from pat import bars, clicks, join, rest

_A = join('B5 . . . E5 F#5 G5 A5', 'B5 . . G5 B5 . . G5',
          'B5 . . E5 G5 E5 C5 G5', 'E5 . . . . . S .',
          'C6 B5 A5 . . . B5 C6', 'D6 . . C6 B5 A5 G5 F#5',
          'G5 . . A5 B5 . . G5', 'E5 . . . S . S .')
_TRANCE = '@0 @0 @12 @0 @7 @0 @12 @0'
_ROOTS = ['E3', 'E3', 'C3', 'E3', 'A3', 'D3', 'G3', 'B2']

SONG = {
    'id': 'swan', 'title': 'SWAN LAKE', 'genre': 'TRANCE',
    'level': 3, 'bpm': 138, 'step_div': 2, 'beats_per_bar': 4,
    'chart': join(rest(8), _A, _A, _A),
    'bgm': join(clicks(2, 4, 'E5'), bars(_TRANCE, _ROOTS * 3)),
}
