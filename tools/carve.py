"""Carve the upstream SICP LaTeX chapters into one file per (sub)section.

The upstream source keeps each chapter in a single monolithic file --
``chapters/chapter_1.tex`` alone is ~4,100 lines spanning 22 sections. That
granularity is useless for a section-by-section translation: the working diff
between original and translation degrades to "everything changed".

This script splits each chapter at its ``\\section``/``\\subsection`` boundaries
into ``book/original/chN/NN-NN-NN-slug.tex``, byte-for-byte, so that
``diff book/original/ch1/X.tex book/ch1/X.tex`` stays a meaningful comparison
for a single section at a time.

The output tree is generated, never hand-edited, and is not committed: it is
CC BY-SA 4.0 text belonging to the pinned submodule, reproducible at any time
with ``make carve``.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = REPO_ROOT / "vendor" / "sicp-latex"
OUT_ROOT = REPO_ROOT / "book" / "original"

# A heading we split on. Titles are single-line throughout the upstream source.
HEADING_RE = re.compile(r"^\\(chapter|section|subsection)\{")

# The number is taken from the \label that follows each heading, never inferred
# by counting -- upstream labels every one of them.
LABEL_RE = re.compile(r"\\label\{(Chapter|Section) ([\d.]+)\}")

# Markup that appears inside headings and must be unwrapped to build a slug,
# e.g. \subsection{Constructing Procedures Using \code{lambda}}
INLINE_MACRO_RE = re.compile(r"\\[a-zA-Z]+\*?\{([^{}]*)\}")


@dataclass(frozen=True)
class Heading:
    """One split point: where it starts, what it is called, how it is numbered."""

    line_index: int
    level: str
    title: str
    number: tuple[int, ...]


def extract_braced(text: str, open_index: int) -> tuple[str, int]:
    """Return the brace-delimited group starting at ``open_index`` and its end.

    Headings nest markup (``\\mbox{Generate}``), so a non-greedy regex would cut
    the title short. Match braces properly instead.
    """
    if text[open_index] != "{":
        raise ValueError(f"expected '{{' at offset {open_index}")
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : i], i
    raise ValueError("unbalanced braces in heading")


def slugify(title: str) -> str:
    """Turn a LaTeX heading into a lowercase dashed filename fragment."""
    text = title
    # Unwrap inline markup repeatedly so nested macros collapse to their text.
    while True:
        unwrapped = INLINE_MACRO_RE.sub(r"\1", text)
        if unwrapped == text:
            break
        text = unwrapped
    text = text.replace("\\", " ")
    text = re.sub(r"[^A-Za-z0-9]+", "-", text)
    return text.strip("-").lower()


def find_headings(lines: list[str]) -> list[Heading]:
    """Locate every chapter/section/subsection heading and its number."""
    headings: list[Heading] = []
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if match is None:
            continue
        level = match.group(1)
        title, _ = extract_braced(line, line.index("{"))

        # The label sits within a couple of lines of the heading.
        number: tuple[int, ...] | None = None
        for lookahead in lines[index : index + 4]:
            label = LABEL_RE.search(lookahead)
            if label is not None:
                number = tuple(int(part) for part in label.group(2).split("."))
                break
        if number is None:
            raise ValueError(
                f"no \\label found for heading on line {index + 1}: {line!r}"
            )

        headings.append(Heading(index, level, title, number))
    return headings


def filename_for(heading: Heading) -> str:
    """``01-01-01-expressions.tex`` -- sorts in reading order, greps by number."""
    padded = tuple(heading.number) + (0, 0, 0)
    return (
        "-".join(f"{part:02d}" for part in padded[:3])
        + f"-{slugify(heading.title)}.tex"
    )


def carve_chapter(source: Path, out_dir: Path) -> list[Path]:
    """Split one chapter file into per-(sub)section files. Returns what was written."""
    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    headings = find_headings(lines)
    if not headings:
        raise ValueError(f"{source} contains no headings")

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for position, heading in enumerate(headings):
        start = heading.line_index
        end = (
            headings[position + 1].line_index
            if position + 1 < len(headings)
            else len(lines)
        )
        target = out_dir / filename_for(heading)
        target.write_text("".join(lines[start:end]), encoding="utf-8")
        written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chapters",
        nargs="*",
        type=int,
        default=[1, 2, 3, 4, 5],
        help="chapter numbers to carve (default: all)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="remove the output tree before carving",
    )
    args = parser.parse_args(argv)

    if not UPSTREAM.exists():
        print(
            f"error: {UPSTREAM} is missing -- run 'git submodule update --init'",
            file=sys.stderr,
        )
        return 1

    if args.clean and OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)

    total = 0
    for chapter in args.chapters:
        source = UPSTREAM / "chapters" / f"chapter_{chapter}.tex"
        if not source.exists():
            print(f"error: {source} is missing", file=sys.stderr)
            return 1
        written = carve_chapter(source, OUT_ROOT / f"ch{chapter}")
        total += len(written)
        print(f"chapter {chapter}: {len(written)} files -> {OUT_ROOT / f'ch{chapter}'}")

    print(f"carved {total} files from {len(args.chapters)} chapters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
