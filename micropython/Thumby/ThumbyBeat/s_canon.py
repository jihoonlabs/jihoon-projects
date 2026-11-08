# Arrangement of "Canon in D" (Johann Pachelbel, c. 1700, public domain).
# One bar here is one chord (two beats).
from pat import bars, clicks, join, rest

_V1 = join('F#5 . . . . . . .', 'E5 . . . . . . .', 'D5 . . . . . . .',
           'C#5 . . . . . . .', 'B4 . . . . . . .', 'A4 . . . . . . .',
           'B4 . . . . . . .', 'C#5 . . . S . . .')
_V2 = join('D5 . . . C#5 . . .', 'B4 . . . A4 . . .',
           'G4 . . . F#4 . . .', 'G4 . . . E4 . . .',
           'D4 . . . F#4 . . .', 'A4 . . . G4 . . .',
           'F#4 . . . D4 . . .', 'F#4 . . . E4 . S .')
_V3 = join('D5 . F#5 . A5 . G5 .', 'F#5 . D5 . F#5 . E5 .',
           'D5 . B4 . D5 . A4 .', 'G4 . B4 . A4 . G4 .',
           'F#4 . D4 . E4 . C#5 .', 'D5 . F#5 . A5 . A4 .',
           'B4 . G4 . B4 . D5 .', 'C#5 . A4 . E5 . S .')
_V4 = join('F#5 . D5 E5 F#5 . D5 E5', 'F#5 F#4 G4 A4 B4 C#5 D5 E5',
           'D5 . B4 C#5 D5 . D4 E4', 'F#4 G4 F#4 E4 F#4 D5 C#5 D5',
           'B4 . D5 C#5 B4 . A4 G4', 'A4 G4 F#4 G4 A4 B4 C#5 D5',
           'B4 . D5 C#5 D5 . C#5 B4', 'C#5 D5 E5 D5 C#5 . S .')
_CHILL = '@0 - - . @12 . @7 .'
_ROOTS = ['D3', 'A3', 'B3', 'F#3', 'G3', 'D3', 'G3', 'A3']

SONG = {
    'id': 'canon', 'title': 'CANON IN D', 'genre': 'CHILL BREAKS',
    'level': 5, 'bpm': 92, 'step_div': 4, 'beats_per_bar': 2,
    'chart': join(rest(8), _V1, _V2, _V3, _V4, 'D5 . . . S . . .'),
    'bgm': join(clicks(4, 2, 'D6'), bars(_CHILL, _ROOTS * 4 + ['D3'])),
}
