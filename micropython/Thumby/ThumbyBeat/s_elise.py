# Arrangement of "Fur Elise" (Beethoven, Bagatelle in A minor, c. 1810,
# public domain).
from pat import bars, clicks, join, rest

_T = join('E5 D#5 E5 B4 D5 C5', 'A4 . . C4 E4 A4', 'B4 . . E4 G#4 B4',
          'C5 . . E4 E5 D#5', 'E5 D#5 E5 B4 D5 C5', 'A4 . . C4 E4 A4',
          'B4 . . E4 C5 B4')
_B = join('C5 . . G4 F5 E5', 'D5 . . F4 E5 D5', 'C5 . . E4 D5 C5',
          'B4 . . . E5 D#5')
_ARP = '@0 @7 @12 . . .'
_ROOTS_T = ['A3', 'A3', 'E3', 'A3', 'A3', 'A3', 'E3']

SONG = {
    'id': 'elise', 'title': 'FUR ELISE', 'genre': 'CLASSIC 2',
    'level': 4, 'bpm': 144, 'step_div': 2, 'beats_per_bar': 3,
    'chart': join(rest(6), '. . . . E5 D#5', _T, 'A4 . . . E5 D#5',
                  _T, 'A4 . . B4 C5 D5', _B, _T, 'A4 . . . S .'),
    'bgm': join(clicks(2, 3, 'A5'), rest(6),
                bars(_ARP, _ROOTS_T + ['A3'] + _ROOTS_T + ['A3']
                     + ['C4', 'G3', 'A3', 'E3'] + _ROOTS_T + ['A3'])),
}
