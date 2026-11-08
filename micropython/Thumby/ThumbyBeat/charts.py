"""Song index for Thumby Beat.

Each song lives in its own module (s_*.py) so only the selected song is
kept in memory. META is a light index for the song select screen; tests
check that it matches the song modules.

Song chart steps: '.' rest, '|' bar, bare pitch = key note with an
automatic lane, lane letter (S L R B A) + pitch = fixed lane, 'S' =
scratch. Charts never have two notes at the same time (A+B together is
reserved for START). BGM steps: pitch, '-' hold, '.' rest.
"""
import sys

# (module, id, title, genre, level, bpm, note count), easiest first.
META = (
    ('s_island', 'island', 'ISLAND BEEP', 'REGGAE', 1, 92, 44),
    ('s_twinkle', 'twinkle', 'TWINKLE STAR', 'TOY POP', 1, 110, 47),
    ('s_jingle', 'jingle', 'JINGLE BELLS', 'SWING', 2, 140, 54),
    ('s_ode', 'ode', 'ODE TO JOY', 'EURO HOUSE', 2, 124, 67),
    ('s_swan', 'swan', 'SWAN LAKE', 'TRANCE', 3, 138, 105),
    ('s_funk', 'funk', 'PIXEL FUNK', 'FUNK', 3, 108, 75),
    ('s_minuet', 'minuet', 'MINUET IN G', 'CLASSIC 1', 3, 132, 130),
    ('s_chop', 'chop', 'CHOPSTICKS', 'WALTZ POP', 3, 120, 159),
    ('s_korobeiniki', 'korobeiniki', 'KOROBEINIKI', 'EUROBEAT', 4, 150, 120),
    ('s_elise', 'elise', 'FUR ELISE', 'CLASSIC 2', 4, 144, 122),
    ('s_canon', 'canon', 'CANON IN D', 'CHILL BREAKS', 5, 92, 114),
    ('s_habanera', 'habanera', 'HABANERA', 'LATIN', 5, 104, 102),
    ('s_neon', 'neon', 'NEON STEPS', 'TECHNO', 5, 128, 105),
    ('s_nacht', 'nacht', 'NACHTMUSIK', 'DISCO', 6, 116, 140),
    ('s_turca', 'turca', 'ALLA TURCA', 'BREAK-BEATS', 6, 120, 122),
    ('s_rave', 'rave', 'BEEP RAVE', 'RAVE', 7, 145, 122),
    ('s_king', 'king', 'HALL OF KING', 'HARDCORE', 7, 140, 146),
    ('s_tell', 'tell', 'WILLIAM TELL', 'BIG BEAT', 7, 140, 147),
    ('s_star', 'star', 'STAR CIRCUIT', 'DRUM N BASS', 8, 150, 113),
    ('s_bumble', 'bumble', 'BUMBLEBEE', 'HYPER TECHNO', 9, 128, 170),
)
MODULE, ID, TITLE, GENRE, LEVEL, BPM, NOTES = range(7)


def load(index):
    """Import one song module and drop it from sys.modules again."""
    name = META[index][MODULE]
    module = __import__(name)
    song = module.SONG
    try:
        del sys.modules[name]
    except KeyError:
        pass
    return song
