"""Drawing for the picture language of Section 2.2.4.

The original assumes a graphics system and a primitive ``draw-line`` that puts
a line on the screen. It never says what that is, because in 1985 it depended
on the machine in front of you. This module is our substitute, and stands in
the same relation to the section as :func:`pysicp.tail_recursive` does to
Chapter 1: something the language assumes, supplied so the book's code runs.

Only two things live here. :func:`render` turns a painter into an SVG
document, and ``WAVE_SEGMENTS`` is the figure the original shows in Figure 2.10
but never lists. Everything the section actually teaches -- frames, vectors,
``beside``, ``below``, ``transform_painter`` and the recursive designs -- is
printed in the section for the reader to write, and is deliberately not here.

A painter is a procedure from a frame to the segments that fill it. The
original's painter is called for its effect and returns nothing; ours returns
what it would draw, so that composing painters is concatenating sequences and
nothing needs to be mutated or sequenced.
"""

from __future__ import annotations

from collections.abc import Callable

# A vector and a point are the same thing here: a pair of numbers.
Vect = tuple[float, float]
# A segment is the two points it runs between.
Segment = tuple[Vect, Vect]
# A frame is an origin and the two edges leading away from it.
Frame = tuple[Vect, Vect, Vect]
# A painter, given a frame, says which segments fill it.
Painter = Callable[[Frame], tuple[Segment, ...]]

UNIT_SQUARE: Frame = ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0))


def render(painter: Painter, size: int = 240, stroke: str = "currentColor") -> str:
    """Draw a painter over the unit square and return an SVG document.

    SVG's y axis runs downwards and the picture language's runs upwards, so the
    vertical coordinate is flipped on the way out; everything above can then be
    written the right way up.
    """
    segments = painter(UNIT_SQUARE)
    lines = "\n".join(
        f'  <line x1="{x1 * size:.2f}" y1="{(1 - y1) * size:.2f}"'
        f' x2="{x2 * size:.2f}" y2="{(1 - y2) * size:.2f}" />'
        for (x1, y1), (x2, y2) in segments
    )
    # The unit square's edges are drawable, so a segment along one sits exactly
    # on the boundary and half its stroke would fall outside the viewBox. Inset
    # the view by a whole stroke width rather than let the picture be shaved.
    pad = 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" '
        f'height="{size}" viewBox="{-pad} {-pad} {size + 2 * pad} '
        f'{size + 2 * pad}" fill="none" '
        f'stroke="{stroke}" stroke-width="1" stroke-linecap="round">\n'
        f"{lines}\n</svg>\n"
    )


# --- the wave painter ------------------------------------------------------
#
# The original shows `wave` in Figure 2.10 but never lists the segments that
# make it, since there it is drawn by whatever graphics system is to hand.
# These are ours: a stick figure standing in the unit square, with the raised
# arm that gives the painter its name. It is drawn in straight lines where the
# original's is a curved outline, which reads better at the size each copy
# appears in `square_limit`.

WAVE_SEGMENTS: tuple[Segment, ...] = (
    # head
    ((0.42, 0.80), (0.42, 0.90)),
    ((0.42, 0.90), (0.50, 0.97)),
    ((0.50, 0.97), (0.58, 0.90)),
    ((0.58, 0.90), (0.58, 0.80)),
    ((0.58, 0.80), (0.50, 0.75)),
    ((0.50, 0.75), (0.42, 0.80)),
    # body
    ((0.50, 0.75), (0.50, 0.38)),
    # the raised arm that gives the painter its name
    ((0.50, 0.68), (0.30, 0.74)),
    ((0.30, 0.74), (0.19, 0.93)),
    ((0.19, 0.93), (0.13, 0.88)),
    ((0.19, 0.93), (0.25, 0.97)),
    # the lowered arm
    ((0.50, 0.68), (0.72, 0.58)),
    ((0.72, 0.58), (0.88, 0.62)),
    # legs
    ((0.50, 0.38), (0.33, 0.19)),
    ((0.33, 0.19), (0.29, 0.02)),
    ((0.50, 0.38), (0.67, 0.19)),
    ((0.67, 0.19), (0.71, 0.02)),
)
