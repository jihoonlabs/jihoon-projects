# Arrangement of "Eine kleine Nachtmusik" (Mozart, 1787, public domain).
from pat import bars, clicks, join, rest

_A = join('G5 . . . D5 . G5 . D5 G5 D5 G5 B5 . D6 .',
          'C6 . . . A5 . C6 . A5 C6 A5 F#5 A5 . D5 .',
          'G5 . G5 . G5 . B5 A5 G5 . G5 . F#5 . F#5 .',
          'F#5 . A5 C6 F#5 . A5 . G5 . . . S . . .')
_A2 = join('G5 . . . D5 . G5 . D5 G5 D5 G5 B5 . D6 .',
           'C6 . . . A5 . C6 . A5 C6 A5 F#5 A5 . D5 .',
           'G5 . G5 . G5 . B5 A5 G5 . G5 . F#5 . F#5 .',
           'F#5 . A5 C6 F#5 . A5 . G5 . S . S . . .')
_DISCO = '@0 . @12 . @0 . @12 . @0 . @12 . @0 . @12 .'

SONG = {
    'id': 'nacht', 'title': 'NACHTMUSIK', 'genre': 'DISCO',
    'level': 6, 'bpm': 116, 'step_div': 4, 'beats_per_bar': 4,
    'chart': join(rest(16), _A, _A2, _A, _A2, 'G5 . . . S . . . . . . . . . . .'),
    'bgm': join(clicks(4, 4, 'G5'),
                bars(_DISCO, ['G3', 'D3', 'G3', 'D3'] * 4 + ['G3'])),
}
