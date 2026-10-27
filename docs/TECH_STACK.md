# Atomize — Tech Stack (v1)

Web-first now, native mobile later — so the API layer is kept decoupled from the web frontend from day one. Leans on AWS free-tier services wherever a reasonable fit exists for DATA_MODEL.md.

## Summary

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js (TypeScript) + Tailwind, PWA-enabled | Responsive web app, installable on phones, camera access via browser for receipt capture |
| Frontend hosting | AWS Amplify Hosting | Free tier (1,000 build min + 15GB served/mo, always-free tier), handles Next.js SSR builds/deploys from GitHub |
| API | API Gateway + AWS Lambda (Python) | Backend runs on Python, per your call. Free tier is perpetual (1M Lambda requests/mo, 1M API Gateway calls/mo); frontend and a future native app both just call this same API — no rewrite needed later. FastAPI (via [Mangum](https://github.com/jordaneremieff/mangum) as the Lambda adapter) gives request validation, typed request/response models, and auto-generated OpenAPI docs |
| Auth | Amazon Cognito | Free tier (50,000 MAUs, perpetual); handles household invite-code sign-up flow (§2) cleanly via custom attributes/groups; Python backend verifies Cognito JWTs on each request |
| Database | Amazon RDS for PostgreSQL | Matches DATA_MODEL.md's relational schema directly (FKs, numeric types, constraints) with no redesign. **Caveat**: RDS free tier (db.t3/t4g.micro, 750 hrs/mo) is free for 12 months from account creation only, then low-cost (~$15–25/mo for a db this small). Flagging this honestly since DynamoDB would be perpetually free but would require remodeling the whole relational schema into single-table NoSQL — not worth it for a 2-person household app's budget. |
| ORM | SQLAlchemy + Alembic | Python-native ORM; models mirror DATA_MODEL.md tables, Alembic handles migrations |
| Receipt image storage | Amazon S3 | Free tier (5GB storage, 20k GET/2k PUT per month, 12 months), then pennies/month at household-app scale. S3 **lifecycle rule** auto-deletes objects after 6 months — a direct, built-in match for SPEC §19's retention policy |
| OCR | Amazon Textract | Free tier (1,000 pages/mo for the first 3 months, then low per-page cost); extracts raw text/line structure from receipt photos and PDFs; called from Python via `boto3` |
| AI itemization & categorization | Amazon Bedrock (Claude) | Takes Textract's raw output and turns it into structured line items, category assignments, confidence scores, and merchant normalization (SPEC §20); called from Python via `boto3`. No meaningful free tier here, but usage-based cost is small at household volume |
| Scheduled jobs | AWS Lambda (Python) + EventBridge Scheduler | Drives the month-close `budget_period_ledger` computation (DATA_MODEL §"Budget & Categories") and reacts to S3 deletion events to set `receipt.image_deleted_at` |
| Infra as code | AWS CDK (Python) | Whole stack (Lambda, API Gateway, RDS, S3, Cognito, EventBridge) defined in code, reviewable and reproducible — kept in Python too so the whole backend/infra side of the repo shares one language |
| CI/CD | GitHub Actions → CDK deploy | Pushes to `main` run tests/build (pytest for the API, Jest/Playwright for the frontend) and deploy via CDK |
| Python packaging | [uv](https://github.com/astral-sh/uv) | Used over pip/poetry for dependency management, virtualenvs, and lockfiles across the API, jobs, and CDK code — faster installs and a single tool for all Python packages in the repo |
| Local dev | Docker Compose (local Postgres) + AWS SAM CLI for local Lambda invocation | Lets development happen without hitting real AWS resources |

## Why this shape

- **Decoupled API from day one.** Because the plan is "web now, native later" (your choice), the Next.js app never talks to the database directly — it calls the same API Gateway/Lambda endpoints a future React Native app would call. No backend rewrite when that day comes.
- **Python backend.** Per your preference, the API, scheduled jobs, and infra code all run on Python (FastAPI on Lambda, SQLAlchemy/Alembic, boto3, CDK in Python) — one language across the entire backend/infra side of the repo. The frontend remains TypeScript/Next.js since that's the standard for a React-based PWA.
- **Relational DB over NoSQL.** DATA_MODEL.md is already a clean relational design (receipts → items → categories, budgets, audit log with joins). Forcing that into DynamoDB's single-table patterns would mean redesigning access patterns up front for a cost saving that's marginal at 2-person-household scale. RDS's free tier buys a full year to validate the product before that small recurring cost kicks in.
- **S3 lifecycle rule does real work.** SPEC §19's "delete receipt images after 6 months" isn't just a note — it maps to an actual S3 bucket lifecycle policy, enforced by AWS rather than a custom cron job. A small Lambda still needs to listen for the deletion event to flip `receipt.image_deleted_at` in Postgres so the UI reflects it.
- **Textract + Bedrock split.** Textract is purpose-built (and cheap/free-tier) for pulling raw text and table structure off a receipt image; Bedrock (Claude) is then used for the judgment-call part — deciding what's an item vs. a tax line, assigning categories, scoring confidence — which is exactly the split SPEC §20 draws between "parsing" and "classification."

## Known tradeoffs to revisit later

- RDS cost after the 12-month free tier — fine for now, but worth re-checking Aurora Serverless v2 (scales to near-zero, no free tier either) if cost becomes a concern at that point.
- Bedrock has no free tier — budget for small per-request costs once real households are actively uploading receipts.
- No native app yet — the "later" part of "web now, native later" isn't scheduled; revisit once the web app is in daily use.
