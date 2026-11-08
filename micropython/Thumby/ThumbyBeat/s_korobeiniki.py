# Arrangement of "Korobeiniki" (Russian folk song, 19th century,
# public domain).
from pat import bars, clicks, join, rest

_HEAD = join('E5 . B4 C5 D5 . C5 B4', 'A4 . A4 C5 E5 . D5 C5',
             'B4 . . C5 D5 . E5 .')
_TAIL = join('. D5 . F5 A5 . G5 F5', 'E5 . . C5 E5 . D5 C5',
             'B4 . B4 C5 D5 . E5 .')
_A = join(_HEAD, 'C5 . A4 . A4 . . .', _TAIL, 'C5 . A4 . A4 . S .')
_A2 = join(_HEAD, 'C5 . A4 . A4 . S .', _TAIL, 'C5 . A4 . A4 S . S')
_EURO = '. @12 . @12 . @12 . @12'
_ROOTS = ['E3', 'A3', 'E3', 'A3', 'D3', 'C3', 'E3', 'A3']

SONG = {
    'id': 'korobeiniki', 'title': 'KOROBEINIKI', 'genre': 'EUROBEAT',
    'level': 4, 'bpm': 150, 'step_div': 2, 'beats_per_bar': 4,
    'chart': join(rest(8), _A, _A2, _A2, 'A4 . . . S . . .'),
    'bgm': join(clicks(2, 4, 'A5'), bars(_EURO, _ROOTS * 3 + ['A3'])),
}
