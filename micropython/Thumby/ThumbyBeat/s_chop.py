# Arrangement of "The Celebrated Chop Waltz" (Euphemia Allen, 1877,
# public domain), known as "Chopsticks".
from pat import join

_FG = 'LF5 RG5 LF5 RG5 LF5 RG5'
_EG = 'BE5 AG5 BE5 AG5 BE5 AG5'
_DB = 'LD5 RB5 LD5 RB5 LD5 RB5'
_CC = 'BC5 AC6 BC5 AC6 BC5 AC6'
_TURN = 'BC5 AC6 LB4 RD6 LA4 RE6'
_A = join(_FG, _FG, _EG, _EG, _DB, _DB, _CC, _TURN)
_B = join('LC5 . RE5 . BG5 .', 'AC6 . . . S .',
          'LD5 . RF5 . BA5 .', 'AD6 . . . S .')

_G7 = 'G3 - B3 . B3 .'
_C = 'C4 - E4 . E4 .'
_G7B = 'G3 - F4 . F4 .'
_CEND = 'C4 - G3 . G3 .'
_BGM_A = join(_G7, _G7, _C, _C, _G7B, _G7B, _C, _CEND)
_BGM_B = join(_C, _C, 'D4 - F4 . F4 .', _G7)

SONG = {
    'id': 'chop', 'title': 'CHOPSTICKS', 'genre': 'WALTZ POP',
    'level': 3, 'bpm': 120, 'step_div': 2, 'beats_per_bar': 3,
    'chart': join('. . . . . .', _A, _A, _B, _A,
                  'BC5 AC6 BC5 . S .', 'LC5 . . . . .'),
    'bgm': join('C6 . C6 . C6 .', _BGM_A, _BGM_A, _BGM_B, _BGM_A, _C,
                'C4 - - - . .'),
}
