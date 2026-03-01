# Contributing to openclaw-x

## Development Setup

```bash
git clone https://github.com/AmuMoon/openclaw-x-skill.git
cd openclaw-x-skill
uv sync --group dev
```

## Running Tests

```bash
uv run pytest tests/ -v
```

## Linting

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Pull Requests

1. Fork the repo and create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass and linting is clean
4. Submit a PR with a clear description of changes

## Commit Messages

Use conventional commits:
- `feat: add new feature`
- `fix: resolve bug`
- `docs: update documentation`
- `test: add tests`
- `chore: maintenance tasks`

## Code Style

- Python >= 3.11 with modern typing (`str | None`, `dict[str, Any]`)
- Format with `ruff format`
- Lint with `ruff check`
- Keep dependencies minimal
