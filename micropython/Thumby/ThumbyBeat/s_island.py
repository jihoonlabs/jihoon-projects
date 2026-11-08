# Original song for Thumby Beat.
from pat import bars, clicks, join, rest

_A = join('G5 . . E5 . . D5 .', 'C5 . . . A4 . C5 .',
          'D5 . . E5 . . G5 .', 'E5 . . . . . S .',
          'A5 . . G5 . . E5 .', 'G5 . . . E5 . D5 .',
          'C5 . . D5 . . E5 .', 'C5 . . . . . S .')
_SKANK = '@0 @12 . @12 @7 @12 . @12'
_ROOTS = ['C3', 'A3', 'D3', 'C3', 'F3', 'C3', 'G3', 'C3']

SONG = {
    'id': 'island', 'title': 'ISLAND BEEP', 'genre': 'REGGAE',
    'level': 1, 'bpm': 92, 'step_div': 2, 'beats_per_bar': 4,
    'chart': join(rest(8), _A, _A),
    'bgm': join(clicks(2, 4, 'C6'), bars(_SKANK, _ROOTS * 2)),
}
