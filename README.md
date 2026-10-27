# Atomize

Household expense tracking that uses AI to parse receipts down to the line-item level, categorizes spend, and tracks it against category budgets — with trend/pacing analysis over time.

## Docs

- [ROADMAP.md](ROADMAP.md) — sequential task breakdown; start here to pick up work
- [docs/SPEC.md](docs/SPEC.md) — product spec (v1)
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md) — relational data model
- [docs/TECH_STACK.md](docs/TECH_STACK.md) — tech stack and infrastructure choices
- [docs/Overview.pdf](docs/Overview.pdf) — original project overview

## Repo structure

```
apps/
  web/      Next.js (TypeScript) PWA frontend
  api/      FastAPI (Python, uv-managed) backend, deployed on AWS Lambda
infra/      AWS CDK (Python, uv-managed) app defining all infrastructure
docs/       Spec, data model, tech stack docs
```

Each app directory has its own README with setup instructions.

## Status

Early scaffold — data model and infra are defined, but the app has no real endpoints or UI yet. See [ROADMAP.md](ROADMAP.md) for what's next.
