# PySICP

SICP rewriten in Python

## Installation

To work on the book, clone the repository and sync the environment:

```bash
uv sync
```

To use the `pysicp` package on its own -- the trampolining support the book's
code depends on -- install it as a dependency:

```bash
uv add pysicp            # in a uv project
uv pip install pysicp    # into the active environment
```

The package ships type information (`py.typed`), so `mypy` and editors see its
annotations. Only `src/pysicp/` is packaged; the book, its build machinery and
the vendored upstream source are not part of the distribution.

## Development

```bash
uv sync --group dev   # install dev dependencies
pre-commit install    # install git hooks

uv run ipython        # REPL with pysicp importable
uv run pytest         # run tests
uv run mypy src/      # type check
uv run ruff check     # lint
uv run ruff format    # format
```

## License

- **Code** (`src/`, `code/`, `tools/`, `tests/`, build machinery) — MIT.
- **Book text** (`book/`, and the PDF and HTML built from it) — CC BY-SA 4.0,
  as a derivative of *Structure and Interpretation of Computer Programs*
  (2nd ed.), which is itself CC BY-SA 4.0. The ShareAlike term is inherited,
  not chosen.

See `LICENSE`.

---

## Notes on typography and house style

> Temporary home. These are decisions about how the book is set, recorded here
> so they are not lost; they belong somewhere more permanent (`CLAUDE.md`, or a
> style guide under `docs/`) once there are enough of them to organize.

### Departures from the vendored source

The book inherits its preamble from `vendor/sicp-latex`, so anything not listed
here follows that source. These are the deliberate exceptions, all applied in
`book/preamble/init.tex` *after* the upstream preamble is inherited, so the
submodule itself is never modified.

- **No line numbers on code blocks.** Upstream adds them (`numbers=left` in
  `preamble/syntaxhighlight.tex`); their README lists "Code blocks now have
  numbered lines" among their own changes, so the book being translated did not
  have them. Reverted with `\lstset{numbers=none}`, and `numbers=none` is set in
  `pythonStyle` so Python listings match.
- **Code is set in black, not grey.** Upstream sets `basicstyle` to
  `SchemeLight` (`#686868`). Redefined to `#000000` so code matches body text.
  Note that `SchemeLight` is also upstream's `commentstyle`, so comments are now
  black too; they remain distinguishable by their italics. If comments should
  stay grey, give `commentstyle` its own colour rather than reverting this.

### Conventions

- **`\noindent` belongs only after a display** — a code block, list, figure or
  block quote — where the paragraph continues a thought the display interrupted.
  After ordinary prose a new paragraph should indent normally. Watch for this
  when merging an input and an output block into a single `>>>` transcript: the
  original's `\noindent` was there because a display followed, and merging
  leaves it orphaned.
- **Hard-wrap `.tex` at 80 columns.** Sections are diffed against their carved
  originals (`make diff SECTION=...`), and reflowing a paragraph turns a small
  diff into a whole-paragraph rewrite.
- **Inline code**: `\code{...}` for naming things in prose (TeX specials must be
  escaped); `\pycode{...}` for real Python where highlighting earns its keep (no
  escaping needed except `%`, and `~` is currently swallowed).
- **Predicates are named `is_...`** — Scheme's trailing `?` (`good-enough?`) has
  no Python spelling; `is_good_enough` is the nearest idiom and reads the same
  in prose.
- **Translation seams** are marked with `buildFromScarcity`, `revealTheSurface`,
  `departure` or `notTaste` — a fixed vocabulary, so the notes stay greppable.
