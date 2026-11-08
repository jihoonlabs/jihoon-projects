# Arrangement of "Minuet in G major" (Christian Petzold, from the 1725
# Anna Magdalena Bach notebook, public domain).
from pat import bars, clicks, join, rest

_A = join('D5 . G4 A4 B4 C5', 'D5 . G4 . G4 .', 'E5 . C5 D5 E5 F#5',
          'G5 . G4 . G4 .', 'C5 . D5 C5 B4 A4', 'B4 . C5 B4 A4 G4',
          'F#4 . G4 A4 B4 G4', 'A4 . . . . .')
_A2 = join('D5 . G4 A4 B4 C5', 'D5 . G4 . G4 .', 'E5 . C5 D5 E5 F#5',
           'G5 . G4 . G4 .', 'C5 . D5 C5 B4 A4', 'B4 . C5 B4 A4 G4',
           'A4 . B4 A4 G4 F#4', 'G4 . . . S .')
_WALTZ = '@0 - @12 . @7 .'
_ROOTS_A = ['G3', 'G3', 'C3', 'G3', 'C3', 'G3', 'D3', 'D3']
_ROOTS_A2 = ['G3', 'G3', 'C3', 'G3', 'C3', 'G3', 'D3', 'G3']

SONG = {
    'id': 'minuet', 'title': 'MINUET IN G', 'genre': 'CLASSIC 1',
    'level': 3, 'bpm': 132, 'step_div': 2, 'beats_per_bar': 3,
    'chart': join(rest(6), _A, _A2, _A, _A2),
    'bgm': join(clicks(2, 3, 'G5'),
                bars(_WALTZ, _ROOTS_A + _ROOTS_A2 + _ROOTS_A + _ROOTS_A2)),
}
