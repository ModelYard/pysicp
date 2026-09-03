"""Tests for the chapter-carving tool.

The property that matters is losslessness: the carved files must reassemble
into the upstream chapter byte for byte. If they do not, every diff between an
original and its translation is measuring the carve as well as the translation.
"""

from pathlib import Path

import pytest

from tools.carve import Heading, carve_chapter, filename_for, find_headings, slugify

UPSTREAM_CHAPTERS = (
    Path(__file__).resolve().parent.parent / "vendor" / "sicp-latex" / "chapters"
)


def test_slugify_unwraps_inline_markup() -> None:
    assert slugify(r"Constructing Procedures Using \code{lambda}") == (
        "constructing-procedures-using-lambda"
    )


def test_slugify_handles_nested_markup() -> None:
    assert slugify(r"Procedures and the Processes They \mbox{Generate}") == (
        "procedures-and-the-processes-they-generate"
    )


def test_filename_pads_to_three_levels() -> None:
    chapter = Heading(0, "chapter", "Building Abstractions", (1,))
    assert filename_for(chapter) == "01-00-00-building-abstractions.tex"


def test_filename_uses_full_section_number() -> None:
    subsection = Heading(0, "subsection", "Expressions", (1, 1, 1))
    assert filename_for(subsection) == "01-01-01-expressions.tex"


@pytest.mark.parametrize("chapter", [1, 2, 3, 4, 5])
def test_carve_is_lossless(chapter: int, tmp_path: Path) -> None:
    source = UPSTREAM_CHAPTERS / f"chapter_{chapter}.tex"
    if not source.exists():
        pytest.skip("submodule not checked out")

    written = carve_chapter(source, tmp_path)
    rejoined = "".join(path.read_text(encoding="utf-8") for path in sorted(written))

    assert rejoined == source.read_text(encoding="utf-8")


@pytest.mark.parametrize("chapter", [1, 2, 3, 4, 5])
def test_every_heading_is_numbered(chapter: int) -> None:
    source = UPSTREAM_CHAPTERS / f"chapter_{chapter}.tex"
    if not source.exists():
        pytest.skip("submodule not checked out")

    headings = find_headings(
        source.read_text(encoding="utf-8").splitlines(keepends=True)
    )

    assert headings
    assert all(heading.number for heading in headings)
