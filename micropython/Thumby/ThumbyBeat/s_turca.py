# Arrangement of "Rondo alla Turca" (Mozart, Piano Sonata No. 11,
# c. 1783, public domain).
from pat import bars, clicks, join, rest

_A = join('B4 A4 G#4 A4 C5 . . . D5 C5 B4 C5 E5 . . .',
          'F5 E5 D#5 E5 B5 A5 G#5 A5 B5 A5 G#5 A5 C6 . . .',
          'A5 . C6 . B5 . A5 . G5 . A5 . B5 . A5 .',
          'G5 . A5 . B5 . A5 . G5 . F#5 . E5 . S .')
_BREAKS = '@0 . . @0 . . @12 . @0 . @0 . @7 . . .'

SONG = {
    'id': 'turca', 'title': 'ALLA TURCA', 'genre': 'BREAK-BEATS',
    'level': 6, 'bpm': 120, 'step_div': 4, 'beats_per_bar': 4,
    'chart': join(rest(16), _A, _A, _A,
                  'E5 . . . S . S . A4 . . . S . . .'),
    'bgm': join(clicks(4, 4, 'A5'),
                bars(_BREAKS, ['A3', 'A3', 'C4', 'E3'] * 3 + ['A3'])),
}
