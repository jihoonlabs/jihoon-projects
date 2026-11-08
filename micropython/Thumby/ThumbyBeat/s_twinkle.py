# Arrangement of the French folk melody "Ah! vous dirai-je, maman"
# (18th century, public domain), known as "Twinkle Twinkle Little Star".
from pat import bars, clicks, join, rest

_A = join('C5 . C5 . G5 . G5 .', 'A5 . A5 . G5 . . .',
          'F5 . F5 . E5 . E5 .', 'D5 . D5 . C5 . S .')
_B = join('G5 . G5 . F5 . F5 .', 'E5 . E5 . D5 . . .',
          'G5 . G5 . F5 . F5 .', 'E5 . E5 . D5 . S .')
_TOY = '@0 . @12 . @7 . @12 .'

SONG = {
    'id': 'twinkle', 'title': 'TWINKLE STAR', 'genre': 'TOY POP',
    'level': 1, 'bpm': 110, 'step_div': 2, 'beats_per_bar': 4,
    'chart': join(rest(8), _A, _B, _A, 'C5 . . . S . . .'),
    'bgm': join(clicks(2, 4, 'C6'),
                bars(_TOY, ['C3', 'F3', 'F3', 'G3', 'C3', 'G3', 'C3', 'G3',
                            'C3', 'F3', 'F3', 'G3', 'C3'])),
}
