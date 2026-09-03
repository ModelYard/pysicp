# PySICP

SICP rewriten in Python

## Installation

```bash
uv sync
```

## Development

```bash
uv sync --group dev   # install dev dependencies
pre-commit install    # install git hooks

uv run pytest         # run tests
uv run mypy src/      # type check
uv run ruff check     # lint
uv run ruff format    # format
```

## License

GPL-3.0
