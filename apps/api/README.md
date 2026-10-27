# atomize-api

FastAPI backend for Atomize, deployed to AWS Lambda behind API Gateway (see [docs/TECH_STACK.md](../../docs/TECH_STACK.md)). SQLAlchemy models in `src/atomize_api/models/` mirror [docs/DATA_MODEL.md](../../docs/DATA_MODEL.md).

## Setup

```bash
cd apps/api
uv sync
cp .env.example .env   # then fill in a local DATABASE_URL, etc.
```

## Run locally

```bash
uv run uvicorn atomize_api.main:app --reload
```

## Migrations

```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## Tests, types, lint

```bash
uv run pytest --cov   # unit tests + coverage report
uv run mypy src/ tests/
uv run ruff check .
```

All three run in CI (see [docs/TECH_STACK.md](../../docs/TECH_STACK.md)'s Coding standards section: full type hints everywhere, checked with mypy in strict mode, and unit tests aiming for as much coverage as practical).
