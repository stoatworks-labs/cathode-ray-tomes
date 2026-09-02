#!/usr/bin/env python3
"""Reading a grid designator, in either of the two conventions Atari used.

Until 1983 a device is named by its row letter then its column number:

    A1   H/J2   L/M/N3   R11

From 1983 the convention transposes — column number first, row letter second —
and the row alphabet changes with it. Major Havoc, Food Fight, Pole Position,
Millipede, I-Robot, Jedi and Super Sprint all print:

    2L   1F   3A   12J

and they use Q and S, letters the early alphabet deliberately skipped. So the
alphabet rule recorded in AGENTS.md ("Atari skips G, I, O and Q") describes the
early boards only, and applying it to a later one would reject real positions.

Orientation is a property of a board, never of a designator. `A1` can only be
read one way, but `2L` and `L2` are the same cell written two ways and nothing
in the string says which the silkscreen carries. So the board definition states
it once, in `grid.transposed`, and every reader here is told rather than
guessing. Getting it wrong does not corrupt a map so much as transpose it
entirely, which is why it is not inferred per designator.

Both conventions span the same way — a wide device sits across adjacent rows —
and a span is always written with the row letters joined: `H/J2` early, `2H/J`
late. It is the letters that span because it is the letters that are the narrow
axis; a DIP straddles rows, not columns.
"""
import re

# row letters, then column digits            A1, H/J2, L/M/N3, R11
LETTER_FIRST = re.compile(r'^([A-Z](?:/[A-Z])*)(\d{1,2})$')
# column digits, then row letters            2L, 1F, 12J, 2H/J
DIGIT_FIRST = re.compile(r'^(\d{1,2})([A-Z](?:/[A-Z])*)$')


def parse(desig, transposed=False):
    """('ABC', 3) for a designator spanning rows A, B and C in column 3.

    Returns None when the string is not a designator in this board's
    convention — which is the answer for OCR wreckage and for a designator
    written the other way round, and both must be rejected rather than coerced.
    """
    if not desig:
        return None
    m = (DIGIT_FIRST if transposed else LETTER_FIRST).match(desig.strip().upper())
    if not m:
        return None
    letters, digits = (m.group(2), m.group(1)) if transposed else m.group(1, 2)
    return letters.replace("/", ""), int(digits)


def cell_and_span(desig, transposed=False):
    """('B10', 'B/C10') for a span; ('C3', None) for a plain designator.

    The cell is where the map keys the device — its first row — and the span is
    the designator as the sheet prints it, kept so the device can be drawn
    across the cells it actually occupies rather than hung off one of them.
    """
    p = parse(desig, transposed)
    if not p:
        return None, None
    letters, col = p
    if len(letters) == 1:
        return desig.strip().upper(), None
    first = f"{col}{letters[0]}" if transposed else f"{letters[0]}{col}"
    return first, desig.strip().upper()


def format_cell(row_letter, col, transposed=False):
    """The designator a board of this convention would print for a cell."""
    return f"{col}{row_letter}" if transposed else f"{row_letter}{col}"
