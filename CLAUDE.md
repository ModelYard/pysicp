# PySICP

SICP rewriten in Python

## Project structure

```
src/pysicp/   Main package
tests/                                Test suite
docs/                                 Documentation
  project-management/                 Project management docs (roadmap, architecture decisions, stories, etc.)
    stories/                            User stories and use cases
      to-do/                            User stories that are planned but not yet started
scratch/                              Local scratch notebooks and experiments (gitignored)
vendor/                               Third-party sources included as git submodules
  sicp-latex/                           Community LaTeX source of SICP 2nd ed. (CC BY-SA 4.0), pinned to a release tag
```

## Setup

```bash
git submodule update --init   # fetch vendor/sicp-latex (or clone with --recurse-submodules)
uv sync --group dev           # install all dependencies including dev
pre-commit install            # install git hooks
```

## Common commands

```bash
# Testing
uv run pytest                          # run all tests
uv run pytest tests/test_foo.py        # run a specific file
uv run pytest -x                       # stop on first failure
uv run pytest -v                       # verbose output

# Type checking
uv run mypy src/                       # type check the package

# Linting & formatting
uv run ruff check src/ tests/          # lint
uv run ruff check --fix src/ tests/    # lint with auto-fix
uv run ruff format src/ tests/         # format
```

## Conventions

- Python 3.13+ required
- `src/` layout: the package lives under `src/`, not at the repo root
- Tests are a package (`tests/__init__.py` exists) — use absolute imports in test files
- Strict mypy: all public APIs must be fully typed, no `Any` without justification
- Ruff handles both linting and formatting (line length: 88)
- Pre-commit runs ruff and mypy on every commit
- Always use Red/Green TDD when adding new features or fixing bugs.  Validate the test cases with a human before moving on to implementation.  DO that in the chat one by one using an english language descrption of the test case, not code.  Only after the test cases are validated, move on to implementation.
- Files under `docs/` must be named in all lowercase, 3–5 words, separated by dashes (e.g. `yaml-to-object-graph.md`)
- git commit summary is in present tense (e.g. not "Added support for YAML anchors" rather "Adds support for YAML anchors")

## Architecture

[Describe the high-level architecture here — key modules, data flow, external dependencies, important invariants.]
