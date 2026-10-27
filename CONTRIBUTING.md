# Contributing

This is a 2-person side project, worked on by both people and by coding agents. These conventions exist so work from either source is easy to review and doesn't collide.

## Branching

- `main` is protected: no direct pushes, no force-pushes. All changes land via a pull request.
- Branch names: `<type>/<short-description>`, e.g. `feat/receipt-dedup-check`, `fix/tax-rounding-off-by-one`, `chore/bump-fastapi`. Types: `feat`, `fix`, `chore`, `docs`, `infra`, `refactor`.
- When a branch implements a ROADMAP.md task, prefer naming it after the task: `feat/t009-tax-allocation`.
- Rebase (or merge `main` in) before opening a PR if `main` has moved significantly; don't let branches go stale for long on a project this size.

## Commits

- Write commit messages that explain *why*, not just *what* (see the repo's existing history for the style — it's not currently following Conventional Commits strictly, and that's fine; clarity matters more than format).
- Prefer a small number of coherent commits over one commit per file-save. Squash fixups before opening a PR where it makes the history easier to read.

## Pull requests

- Every PR uses the template in `.github/pull_request_template.md` — fill in the checklist honestly, don't just check boxes.
- CI (`.github/workflows/ci.yml`) must pass before merging: `ruff`, `mypy` (strict), `pytest --cov` for both Python projects, `eslint` + `next build` for the web app, plus `cdk synth` for infra. These are required status checks on `main` (branch protection).
- If a PR completes a ROADMAP.md task, update that task's status to `[x] Done` and fill in its **Summary** as part of the PR — not as a separate follow-up.

## Local checks before pushing

Install [pre-commit](https://pre-commit.com) once per clone (no permanent install needed — `uvx` works too):

```bash
uvx pre-commit install
```

This runs the same checks CI runs (ruff, mypy, eslint) on every commit, so issues are caught before they reach a PR. The full test suite (`pytest --cov`) is **not** run on every commit — it's slower and CI already gates merges on it — but run it yourself before opening a PR:

```bash
cd apps/api && uv run pytest --cov
cd infra && uv run pytest --cov
```

## Coding standards

See `docs/TECH_STACK.md`'s **Coding standards** section: all Python code is fully type-hinted and checked with mypy in strict mode, and new logic should come with unit tests aiming for as much coverage as practical.

## Working from ROADMAP.md

If you're an agent picking up this project, start at `ROADMAP.md` — it has its own "How to use this file" instructions at the top. The short version: find the next unblocked task, implement it on its own branch, update its Summary, open a PR against this checklist.
