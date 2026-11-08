"""Helpers for writing song files: bars, rests, clicks and bass patterns.

A bass pattern is a bar of BGM steps where '@n' means "root + n
semitones", e.g. '@0 . @12 .' plays the root and then its octave.
"""

_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
_BASE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def midi(name):
    value = _BASE[name[0]]
    rest = name[1:]
    if rest[0] == '#':
        value += 1
        rest = rest[1:]
    elif rest[0] == 'b':
        value -= 1
        rest = rest[1:]
    return (int(rest) + 1) * 12 + value


def note_name(number):
    return _NAMES[number % 12] + str(number // 12 - 1)


def fill(pattern, root):
    base = midi(root)
    out = []
    for token in pattern.split():
        if token[0] == '@':
            out.append(note_name(base + int(token[1:])))
        else:
            out.append(token)
    return ' '.join(out)


def bars(pattern, roots):
    """One bar of the pattern per root, e.g. bars('@0 . @12 .', ['C3'])."""
    return ' | '.join(fill(pattern, root) for root in roots)


def rest(steps):
    return ' '.join(['.'] * steps)


def clicks(step_div, beats, note):
    """Count-in bar: one click per beat."""
    beat = ' '.join([note] + ['.'] * (step_div - 1))
    return ' '.join([beat] * beats)


def join(*parts):
    return ' | '.join(parts)
