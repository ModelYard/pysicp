"""Check the Python printed in the book.

The code in \\code{codeBlock} environments is written REPL-style, with >>> and
... prompts and the interpreter's replies interleaved. That is not a module, so
it cannot simply be handed to ruff: names arrive from earlier sections,
procedures are deliberately redefined as the argument develops, and a bare
expression on a line is the REPL displaying a value rather than a statement
with no effect. Running ruff over the extracted source reports all of those,
and every one of them is a false alarm.

Two properties are worth enforcing, and neither has false alarms:

  * every block parses as Python -- a typo in printed code is a defect the
    reader hits directly, and nothing else in the build would catch it;
  * no line exceeds the measure -- at 7.5pt the column fits 80 characters, and
    a longer line runs into the margin (see book/preamble/init.tex).

Run with --ruff to additionally report what ruff makes of the extracted source,
advisory only, for the occasional real finding among the noise.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BLOCK = re.compile(r"\\begin\{(codeBlock|compactCodeBlock)\}\n(.*?)\\end\{\1\}", re.S)
MAX_WIDTH = 80

# Reported by ruff on every extracted module, always spuriously: see the
# module docstring for why each is an artefact of the REPL form rather than a
# fault in the book.
ARTEFACTS = ("F821", "F811", "B018", "I001", "E402")

# Body indentation. A continuation line may also be aligned under an opening
# bracket, at any column, which is why this is checked per-suite below rather
# than by looking at every line's indent.
INDENT = 4


def repl_source(body: str) -> str | None:
    """The source lines of a REPL block, prompts stripped; None if not one."""
    lines = body.split("\n")
    if not any(line.startswith(">>> ") for line in lines):
        return None
    return "\n".join(line[4:] for line in lines if line.startswith((">>> ", "... ")))


def odd_indents(source: str) -> list[str]:
    """Indentation that is neither a multiple of four nor bracket alignment.

    A three-space body reads as a four-space one in print and is invisible to
    every other check, since it still parses. Lines inside an unclosed bracket
    are skipped: aligning a continuation under the bracket it belongs to is
    correct, and lands on whatever column the bracket happens to be in.
    """
    found: list[str] = []
    depth = 0
    for line in source.split("\n"):
        stripped = line.strip()
        if stripped and depth == 0:
            indent = len(line) - len(line.lstrip())
            if indent % INDENT:
                found.append(
                    f"indented {indent}, not a multiple of {INDENT}: {stripped}"
                )
        depth += line.count("(") + line.count("[") + line.count("{")
        depth -= line.count(")") + line.count("]") + line.count("}")
        depth = max(depth, 0)
    return found


def book_files() -> list[Path]:
    return sorted(
        p for p in (REPO_ROOT / "book").rglob("*.tex") if "original" not in p.parts
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ruff", action="store_true", help="also report ruff findings")
    args = parser.parse_args()

    problems: list[str] = []
    blocks = 0
    sources: dict[str, str] = {}

    for tex in book_files():
        chunks: list[str] = []
        for match in BLOCK.finditer(tex.read_text()):
            source = repl_source(match.group(2))
            if source is None:
                continue
            blocks += 1
            chunks.append(source)
            rel = tex.relative_to(REPO_ROOT)

            try:
                ast.parse(source)
            except SyntaxError as exc:
                problems.append(f"{rel}: block does not parse: {exc.msg}")

            for line in match.group(2).split("\n"):
                if len(line) > MAX_WIDTH:
                    problems.append(
                        f"{rel}: code line is {len(line)} characters, "
                        f"over the {MAX_WIDTH} the measure fits:\n    {line}"
                    )
            problems.extend(f"{rel}: {bad}" for bad in odd_indents(source))
        if chunks:
            sources[tex.stem.replace("-", "_")] = "\n\n".join(chunks) + "\n"

    if problems:
        print("error: problems in the book's printed code:", file=sys.stderr)
        for problem in problems:
            print(f"    {problem}", file=sys.stderr)
        return 1

    print(f"book code: {blocks} REPL blocks, all parse, none over {MAX_WIDTH} columns")

    if args.ruff:
        with tempfile.TemporaryDirectory() as tmp:
            for name, source in sources.items():
                (Path(tmp) / f"{name}.py").write_text(source)
            subprocess.run(
                [
                    "uv",
                    "run",
                    "ruff",
                    "check",
                    "--no-cache",
                    "--extend-ignore",
                    ",".join(ARTEFACTS),
                    "--output-format",
                    "concise",
                    tmp,
                ],
                cwd=REPO_ROOT,
                check=False,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
