# atomize-infra

AWS CDK (Python) app defining Atomize's infrastructure, per [docs/TECH_STACK.md](../docs/TECH_STACK.md): VPC, RDS Postgres, S3 (receipt images, 6-month lifecycle rule), Cognito, an API Lambda behind HTTP API, and a scheduled Lambda for the month-close budget ledger job.

## Setup

```bash
cd infra
uv sync
```

## Useful commands

```bash
uv run pytest             # unit tests against the synthesized template
cdk synth                 # emit the CloudFormation template
cdk diff                  # compare deployed stack with current state
cdk deploy                # deploy to your default AWS account/region
```

`cdk.json` invokes the app via `uv run python app.py`, so the CDK CLI picks up this project's uv-managed virtualenv automatically.

## Known gaps (scaffold stage)

- **API Lambda is a placeholder.** `ApiHandler` in `stacks/atomize_stack.py` currently points at an inline stub, not the real FastAPI app in `apps/api`. Packaging that app (dependencies + code) as a deployable Lambda artifact — e.g. a Docker-bundled build — is a follow-up step.
- **Lambda is not VPC-attached.** RDS lives in an isolated subnet (no NAT gateway, to stay in the free tier), but the API Lambda isn't currently attached to the VPC, so it can't reach the database yet. Resolving this means either VPC-attaching the Lambda (and adding VPC endpoints for S3/Bedrock/Textract so it doesn't need a NAT gateway for internet access) or fronting RDS with something reachable from outside the VPC. Not decided yet.
- **Month-close ledger Lambda is an empty stub** — the actual `budget_period_ledger` computation logic (DATA_MODEL.md) isn't implemented here.
