"""Render Section 2.2.4's figures from the code the section prints.

The section's pictures are not drawings of what its code would produce; they
are what it produces. The REPL blocks are extracted from the .tex, executed
against pysicp.picture, and the named painters rendered. Nothing is
reimplemented here, so a figure that disagreed with the printed code could not
be generated at all.

Only the drawing primitive comes from the package. Everything the section
teaches -- frames, vectors, beside, below, the recursive designs -- is defined
by the section and reaches this script by being read out of it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.lint_book_code import BLOCK, repl_source  # noqa: E402

SECTION = REPO_ROOT / "book" / "ch2" / "02-02-04-example-a-picture-language.tex"
OUT = REPO_ROOT / "build" / "figures" / "ch2"

# What to draw, and how big. The expressions are evaluated in the namespace the
# section's own code builds, so every name here must be one the section defines.
FIGURES: dict[str, tuple[str, int]] = {
    "wave": ("wave", 200),
    "wave-beside": ("beside(wave, flip_vert(wave))", 200),
    "wave-flipped-pairs": ("flipped_pairs(wave)", 200),
    "wave-right-split": ("right_split(wave, 3)", 200),
    "wave-corner-split": ("corner_split(wave, 3)", 240),
    "wave-square-limit": ("square_limit(wave, 3)", 300),
}

# Defined by the section's exercises rather than its text, so supplied here to
# let the rest of the section's code run. Keeping them few is deliberate: each
# one is a place where the figures stop being drawn by the printed code.
EXERCISE_ANSWERS = """
# Exercise 2.46 -- vectors.
def make_vect(x, y):
    return (x, y)


def xcor_vect(v):
    return v[0]


def ycor_vect(v):
    return v[1]


def add_vect(a, b):
    return (xcor_vect(a) + xcor_vect(b), ycor_vect(a) + ycor_vect(b))


def sub_vect(a, b):
    return (xcor_vect(a) - xcor_vect(b), ycor_vect(a) - ycor_vect(b))


def scale_vect(s, v):
    return (s * xcor_vect(v), s * ycor_vect(v))


# Exercise 2.47 -- frames. The section shows two constructors; this is the
# first, with the selectors that go with it, defined last so it wins.
def make_frame(origin, edge1, edge2):
    return (origin, edge1, edge2)


def origin_frame(f):
    return f[0]


def edge1_frame(f):
    return f[1]


def edge2_frame(f):
    return f[2]


# Exercise 2.48 -- segments.
def make_segment(start, end):
    return (start, end)


def start_segment(s):
    return s[0]


def end_segment(s):
    return s[1]


# Exercise 2.50 -- the transformations the text leaves to the reader.
def flip_horiz(painter):
    return transform_painter(painter, make_vect(1.0, 0.0),
                             make_vect(0.0, 0.0), make_vect(1.0, 1.0))


def rotate180(painter):
    return rotate90(rotate90(painter))


# Exercise 2.51 -- below.
def below(painter1, painter2):
    split_point = make_vect(0.0, 0.5)
    paint_lower = transform_painter(painter1, make_vect(0.0, 0.0),
                                    make_vect(1.0, 0.0), split_point)
    paint_upper = transform_painter(painter2, split_point,
                                    make_vect(1.0, 0.5), make_vect(0.0, 1.0))

    def painted(frame):
        return paint_lower(frame) + paint_upper(frame)

    return painted


# Exercise 2.44 -- up_split.
def up_split(painter, n):
    if n == 0:
        return painter
    smaller = up_split(painter, n - 1)
    return below(painter, beside(smaller, smaller))


def identity(x):
    return x
"""


def section_namespace() -> dict[str, Any]:
    """Execute the section's REPL blocks and return what they define."""
    namespace: dict[str, Any] = {}
    for match in BLOCK.finditer(SECTION.read_text()):
        source = repl_source(match.group(2))
        if source is None:
            continue
        try:
            exec(compile(source, str(SECTION), "exec"), namespace)  # noqa: S102
        except (NameError, TypeError, SyntaxError):
            # Blocks that use a name an exercise is meant to supply, or that
            # show a form before it is complete, are expected to fail here.
            continue
    exec(compile(EXERCISE_ANSWERS, "<exercises>", "exec"), namespace)  # noqa: S102
    return namespace


def main() -> int:
    from pysicp.picture import render

    namespace = section_namespace()
    missing = [n for n in ("wave", "beside", "flip_vert") if n not in namespace]
    if missing:
        print(f"error: the section did not define {missing}", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    for name, (expression, size) in FIGURES.items():
        painter = eval(expression, namespace)  # noqa: S307
        svg = OUT / f"{name}.svg"
        svg.write_text(render(painter, size))
        subprocess.run(
            [
                "rsvg-convert",
                "--format=pdf",
                f"--output={OUT / f'{name}.pdf'}",
                str(svg),
            ],
            check=True,
        )
        print(f"rendered {name} from the section's own code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
