# Atomize — Roadmap

This file is the single source of truth for "what's next." It exists so any agent (or person) can pick up this project cold, know exactly what to build next, and leave a clean trail for whoever picks it up after them.

## How to use this file

1. Find the first task with status `[ ] Not started` whose **Depends on** list is entirely `[x] Done`.
2. Read its Goal and Acceptance Criteria. Check `docs/SPEC.md` / `docs/DATA_MODEL.md` / `docs/TECH_STACK.md` for the authoritative detail — this file intentionally doesn't restate everything.
3. Create a branch per `CONTRIBUTING.md`'s naming convention (e.g. `feat/t007-initial-migration`) — `main` is protected, direct pushes are rejected.
4. Implement it, following `docs/TECH_STACK.md`'s **Coding standards** section for any Python code: full type hints (mypy strict passes), and unit tests covering the new logic as thoroughly as practical — not just enough to pass CI. Run `uv run mypy ...` and `uv run pytest --cov` locally before considering a task done.
5. Fill in the task's **Summary** with what you actually did (not what you intended to do) — call out any deviation from the Goal/Acceptance Criteria and why, and note anything the next agent needs to know. Flip its status to `[x] Done`. Include this ROADMAP.md update in the same PR, not a follow-up.
6. Push the branch and open a PR using `.github/pull_request_template.md`. All three CI checks must pass before it can merge (branch protection enforces this); merge it yourself once green — no human approval is required (`required_approving_review_count: 0`), but a PR is.
7. If implementing it reveals new tasks that need to happen, add them to the roadmap in the right place rather than leaving them as an undocumented side effect.

Tasks are listed in the order they should be done. A task's **Depends on** field is the real constraint — most tasks are strictly sequential because they build on the same code, but where two tasks are genuinely independent it's called out explicitly ("Can run in parallel with T#").

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked (explain why in Summary)

---

## Phase 0 — Foundations

### T001 — Project overview & spec
- Status: [x] Done
- Depends on: —
- Goal: Capture the product requirements from the original overview, resolve ambiguities/gaps with the user.
- Summary: Produced `docs/SPEC.md` from `docs/Overview.pdf` plus a round of clarifying Q&A (household/contributor model, audit trail, dedup detection, tax rounding via largest-remainder method, total-only receipt categorization, budget carryover-into-savings, timezone handling, special-budget isolation, NL query scope, CSV export, 6-month image retention). All open problems from the first pass were resolved and folded back into the relevant sections.

### T002 — Data model
- Status: [x] Done
- Depends on: T001
- Goal: Translate SPEC.md into a relational schema.
- Summary: Produced `docs/DATA_MODEL.md` — 15 tables (household, user, household_membership, household_invite, category, budget, category_pacing_setting, budget_period_ledger, merchant_category_mapping, payment_method, special_budget, special_budget_estimate, receipt, expense_item, audit_log_entry), with an ER diagram and field-level rationale tying back to SPEC sections.

### T003 — Tech stack decision
- Status: [x] Done
- Depends on: T002
- Goal: Pick a stack: web-first (PWA now, native later), AWS-heavy with free tier emphasis, Python backend, uv for Python packaging.
- Summary: Produced `docs/TECH_STACK.md`. Next.js (TS) frontend on Amplify Hosting; FastAPI (Python, uv) on Lambda behind API Gateway; Cognito auth; RDS Postgres + SQLAlchemy/Alembic; S3 for receipt images with a lifecycle rule; Textract (OCR) + Bedrock/Claude (itemization & categorization); EventBridge-scheduled Lambda jobs; CDK (Python) for IaC. Flagged honestly: RDS free tier is 12 months only (chosen anyway over DynamoDB to avoid a NoSQL redesign); Bedrock has no free tier.

### T004 — Git repo & license
- Status: [x] Done
- Depends on: —
- Goal: Initialize version control.
- Summary: `git init`, MIT license, `origin` pointed at `git@github.com:JoseLoarca/atomize.git`, pushed.

### T005 — Monorepo scaffold
- Status: [x] Done
- Depends on: T002, T003
- Goal: Stand up `apps/api` (FastAPI + SQLAlchemy models mirroring DATA_MODEL.md + Alembic), `apps/web` (Next.js PWA), `infra` (CDK Python stack: VPC, RDS, S3 with 6-month lifecycle rule, Cognito, placeholder API Lambda + HTTP API, scheduled month-close Lambda stub), `docs/` holding the three spec docs.
- Summary: All three projects scaffolded and verified working (models import, 15 tables create cleanly, `cdk synth` succeeds, Next.js builds/lints). Both Python projects use `uv`, pinned to Python 3.14 (matches the `PYTHON_3_14` Lambda runtime available in this CDK version — confirmed no version mismatch). Known gaps documented in `infra/README.md`: the API Lambda is still an inline placeholder (not the real FastAPI app), and it isn't VPC-attached yet so it can't reach RDS.

### T006 — CI
- Status: [x] Done
- Depends on: T005
- Goal: Basic GitHub Actions CI.
- Summary: `.github/workflows/ci.yml` — three jobs (`api`: ruff + pytest via uv, `infra`: pytest + cdk synth via uv, `web`: eslint + next build), on push/PR to `main`. Added a real health-check test to `apps/api` since it had zero tests (pytest exits nonzero on zero tests collected).

---

## Phase 1 — Database foundation

### T007 — Initial Alembic migration
- Status: [x] Done
- Depends on: T006
- Goal: Generate and commit the first real Alembic migration from the SQLAlchemy models in `apps/api/src/atomize_api/models/`, and get it applying cleanly against a local Postgres (via Docker Compose, not SQLite — SQLite was only used earlier as a quick DDL smoke test and doesn't enforce the same constraints Postgres will).
- Acceptance criteria:
  - `docker-compose.yml` (or similar) at repo root or in `apps/api` spins up a local Postgres matching `DATABASE_URL` in `.env.example`.
  - `uv run alembic revision --autogenerate -m "initial schema"` produces a migration covering all 15 tables, FKs, uniques, and enums.
  - `uv run alembic upgrade head` succeeds against the local Postgres.
  - `uv run alembic downgrade base` succeeds (round-trips cleanly).
- Summary: Added `docker-compose.yml` at the repo root (Postgres 17, credentials matching `.env.example`; host port overridable via `ATOMIZE_DB_PORT` because 5432 is often already taken locally). Generated `apps/api/alembic/versions/575b68b0f294_initial_schema.py` via autogenerate: all 15 tables plus the three native enums (`audit_changed_by`, `audit_entity_type`, `household_role`), with FKs and uniques. Deviation from raw autogenerate output: `downgrade()` now also drops the enum types (autogenerate leaves them behind, which made `upgrade → downgrade → upgrade` fail), and the file was run through `ruff --fix` so it passes CI lint. Verified against local Postgres: `upgrade head`, `check` (no drift), `downgrade base` (no tables or types left), `upgrade head` again. No automated test was added since CI has no Postgres service; adding one would be a reasonable follow-up. To run locally: `docker compose up -d --wait` from repo root, then `cd apps/api && uv run alembic upgrade head`.

### T008 — Seed the canonical category list
- Status: [x] Done
- Depends on: T007
- Goal: Seed the 23 default categories from SPEC.md §4 into the `category` table as part of migration/setup (not as applic­ation-layer logic), since the list is fixed and global.
- Acceptance criteria: A data migration (or a documented seed script run once post-migration) inserts all categories from SPEC.md with stable, meaningful `sort_order` values. Re-running it is idempotent (no duplicate rows).
- Summary: Seeded the 23 categories from Overview.pdf §4 (SPEC.md §4 defers to it for the list). The list and an idempotent `seed_categories(connection)` live in `apps/api/src/atomize_api/seed/categories.py`; data migration `seed_categories` (`alembic/versions/seed_categories_seed_default_categories.py`) calls it. `sort_order` is 10, 20, … in overview order (gaps leave room for later insertions); ids are deterministic `uuid5(name)` so every environment shares the same keys. Idempotency is by name: only missing categories are inserted, so re-running never duplicates. Downgrade deletes just those 23 names. Verified on Postgres: upgrade → 23 rows, downgrade → 0, re-upgrade → 23, `alembic check` clean. Unit tests (SQLite in-memory, so they run in CI without Postgres) cover count/uniqueness, ordering, idempotency, filling only missing rows, and stable ids. Note for later: the migration imports the app's seed module, so changing `DEFAULT_CATEGORY_NAMES` later changes what a fresh `upgrade` seeds; future list changes should be new migrations.

---

## Phase 2 — Core domain logic (no AI yet)

These are pure-Python business rules from SPEC.md that have no external dependency (no AWS, no AI) and should be unit-testable in isolation before anything is wired to an API route.

### T009 — Tax allocation (largest-remainder method)
- Status: [ ] Not started
- Depends on: T008
- Goal: Implement the proportional tax allocation algorithm from SPEC.md §11 (and the multi-category note in §8): given a receipt's `tax_total` and a list of items with pre-tax totals, return each item's `allocated_tax_amount` such that the sum exactly equals `tax_total`, using truncate-then-distribute-remainder-by-largest-fraction.
- Acceptance criteria: Pure function (e.g. `allocate_tax(tax_total: Decimal, item_pretax_totals: list[Decimal]) -> list[Decimal]`), uses `Decimal` throughout (not float) to avoid floating-point drift, unit tests cover: even division, division with remainder, single item, zero tax, more items than cents of tax.

### T010 — Receipt duplicate detection
- Status: [ ] Not started
- Depends on: T008
- Goal: Implement the duplicate-candidate query from SPEC.md §6 (match on household + merchant_normalized_name + total_amount + transaction_datetime_local + payment_method_label) as a reusable query function, not yet wired to an endpoint.
- Can run in parallel with T009.
- Acceptance criteria: Function returns the matching existing receipt(s), if any, given a candidate receipt's fields. Unit-tested against a seeded in-memory/test DB.

### T011 — Merchant → category mapping lookup & correction
- Status: [ ] Not started
- Depends on: T008
- Goal: Implement household-level, forward-only merchant category mapping per SPEC.md §9: lookup (for total-only receipt categorization) and correction (upsert, forward-only — never touches past receipts).
- Can run in parallel with T009, T010.
- Acceptance criteria: `get_default_category_for_merchant(household_id, merchant_normalized_name) -> Category | None` and `set_merchant_category_mapping(...)` functions, unit-tested; confirms a correction doesn't mutate any existing `receipt.single_category_id`.

### T012 — Audit log writer
- Status: [ ] Not started
- Depends on: T008
- Goal: Implement the append-only audit logging utility from SPEC.md §5 / DATA_MODEL.md's `audit_log_entry` — a single function/decorator pattern that both AI-assigned values (on creation) and user corrections (on update) funnel through, so there's one code path that guarantees nothing bypasses the audit trail.
- Depends on T008 only (not T009–T011) — can run in parallel with them.
- Acceptance criteria: `record_audit_entry(household_id, entity_type, entity_id, field_name, old_value, new_value, changed_by, changed_by_user_id=None)` function; unit tests confirm it never updates/deletes existing rows, and confirm both an AI-origin and user-origin entry serialize correctly.

### T013 — Confidence threshold & low-confidence flagging
- Status: [ ] Not started
- Depends on: T008
- Goal: Implement the fixed global confidence threshold from SPEC.md §5/§21 — a constant plus a pure function that sets `expense_item.is_low_confidence` from `confidence_score`.
- Can run in parallel with T009–T012.
- Acceptance criteria: Threshold is a named constant in one place (not hardcoded inline at call sites), documented as "fixed for v1, household-configurable later" per SPEC.md §21, with a unit test at and around the boundary value.

---

## Phase 3 — API layer (households, auth, core CRUD)

### T014 — Cognito-backed auth dependency
- Status: [ ] Not started
- Depends on: T013
- Goal: FastAPI dependency that verifies a Cognito JWT on incoming requests and resolves it to a `User` row (creating one on first sign-in if needed), per TECH_STACK.md.
- Acceptance criteria: Protected routes reject missing/invalid/expired tokens with 401; a valid token resolves `request.state.user` (or equivalent) to the correct `User`. Tested with a mocked/fake JWT (don't require a live Cognito pool for unit tests).

### T015 — Households, membership, and invite codes
- Status: [ ] Not started
- Depends on: T014
- Goal: Endpoints for SPEC.md §2: create a household (creator becomes super_user), generate/revoke a shareable invite code, join a household via invite code (becomes contributor).
- Acceptance criteria: Creating a household auto-assigns `super_user` to the creator; joining via a revoked or unknown code is rejected with a clear error; a user can belong to more than one household (not explicitly ruled out in SPEC — confirm with the user if this needs to be restricted before building, otherwise assume unrestricted).

### T016 — Categories & payment methods endpoints
- Status: [ ] Not started
- Depends on: T015
- Goal: Read-only `GET /categories` (the fixed global list); CRUD-lite for `payment_method` (household-scoped, label-only, per SPEC.md §15).
- Can run in parallel with T017, T018.
- Acceptance criteria: Categories endpoint requires auth but not household-scoping (global list); payment methods are household-scoped and only visible to that household's members.

### T017 — Budgets & pacing settings endpoints
- Status: [ ] Not started
- Depends on: T015
- Goal: CRUD for `budget` (monthly, per category, SPEC.md §7) and `category_pacing_setting` (SPEC.md §13), household-scoped.
- Can run in parallel with T016, T018.
- Acceptance criteria: Budget uniqueness constraint `(household_id, category_id, year_month)` enforced at the API layer with a clear error, not just a raw DB constraint violation; pacing setting defaults match SPEC.md §13 (on for variable categories, off for fixed/lump-sum) when a household hasn't explicitly set one.

### T018 — Special budgets endpoints
- Status: [ ] Not started
- Depends on: T015
- Goal: CRUD for `special_budget` + `special_budget_estimate` (SPEC.md §14).
- Can run in parallel with T016, T017.
- Acceptance criteria: Creating a special budget and attaching a receipt to it (via `receipt.special_budget_id`, once receipts exist — see T019) correctly excludes that receipt from the regular monthly budget math; this constraint should be written as a test even before T019 lands, against a stubbed receipt row.

---

## Phase 4 — Receipts & expense items (the core workflow, still no AI)

### T019 — Manual receipt + line item entry
- Status: [ ] Not started
- Depends on: T016, T017, T018
- Goal: Endpoints to create/read/update a receipt and its expense items manually (no OCR/AI yet) — this is the foundation the AI pipeline will plug into later, and lets the rest of the app (budgets, pacing, reports) be built and tested against real data without waiting on Textract/Bedrock integration.
- Acceptance criteria: Creating a receipt with items triggers tax allocation (T009) automatically; running the duplicate check (T010) on create surfaces a warning (not a hard block) per SPEC.md §6; every field set on creation is logged via the audit writer (T012) with `changed_by = user`; total-only receipts get their category inferred via T011 if no items are provided.

### T020 — Returns & refunds
- Status: [ ] Not started
- Depends on: T019
- Goal: Implement SPEC.md §12 — item-level returns (negative `expense_item` counterpart) and receipt-level refunds (negative `receipt`, `is_return=true`, linked via `original_receipt_id`).
- Acceptance criteria: A return/refund never deletes or mutates the original row; category totals used in budget math treat the return "as if it never happened" (excluded from pacing/trend calculations) while still being visible in transaction history (a query for "all activity" still surfaces it, a query for "pacing-relevant spend" excludes it).

### T021 — Budget period ledger computation (carryover)
- Status: [ ] Not started
- Depends on: T020
- Goal: Implement the month-close computation from SPEC.md §7 / DATA_MODEL.md's `budget_period_ledger`: for a given household/category/month, compute `actual_spent` (excluding special-budget-attributed receipts per §14, treating returns as void per §12) and `unspent_amount`, and upsert the ledger row. Expose the household's running "saved" total as `SUM(unspent_amount)`.
- Acceptance criteria: Callable as a plain function first (so it can be unit tested without Lambda/EventBridge involved), then wired into the `MonthCloseLedgerHandler` Lambda stub in `infra/stacks/atomize_stack.py` (replacing the TODO body). Idempotent — running it twice for the same month doesn't double-count.

### T022 — Budget pacing & trajectory endpoint
- Status: [ ] Not started
- Depends on: T021
- Goal: Endpoint(s) backing SPEC.md §8/§9/§13 — for a pacing-enabled category, return actual cumulative spend vs. linear expected spend by day, plus total/percent-used/remaining for all categories regardless of pacing.
- Acceptance criteria: Returns no trajectory data (not zeros, not nulls pretending to be zero) for a category with `show_pacing = false`, per §13's "avoids misleading analytics" requirement.

---

## Phase 5 — AI pipeline

### T023 — S3 upload flow for receipt images
- Status: [ ] Not started
- Depends on: T019
- Goal: Endpoint to get a presigned S3 upload URL (or direct multipart upload through the API, decide at build time) for a receipt image/PDF, storing the resulting `source_image_path` on the receipt.
- Acceptance criteria: Uses the `ReceiptsBucket` from the CDK stack; confirms the bucket's 6-month lifecycle rule is in place (infra-level, already built in T005) and that `image_deleted_at` gets set by a follow-up job once S3 actually deletes the object (see T026).

### T024 — Textract OCR integration
- Status: [ ] Not started
- Depends on: T023
- Goal: On receipt image upload, call Amazon Textract to extract raw text/table structure, per TECH_STACK.md.
- Acceptance criteria: Raw Textract output is stored/passed through to T025 without the API needing to re-call Textract; failure (unreadable image) surfaces a clear, user-facing error rather than a silent total-only receipt.

### T025 — Bedrock (Claude) itemization & categorization
- Status: [ ] Not started
- Depends on: T024
- Goal: Feed Textract's output to Bedrock to produce structured line items, category assignments, confidence scores (feeding T013), and merchant normalization (feeding T011), per SPEC.md §20.
- Acceptance criteria: AI-assigned values are written through the audit log (T012) with `changed_by = ai` at creation time; AI never invents a category outside the fixed list (§20) — validate and reject/fallback if it does; total-only receipts (no parseable line items) fall back to merchant-based categorization (T011) rather than failing.

### T026 — Image retention sync job
- Status: [ ] Not started
- Depends on: T025
- Goal: Implement SPEC.md §19 — when S3's lifecycle rule deletes a receipt image after 6 months, a Lambda (triggered by the S3 deletion event) sets `receipt.image_deleted_at` so the app can reflect it without the row itself being touched otherwise.
- Acceptance criteria: Wired as an actual S3 Event Notification → Lambda in the CDK stack (currently not present — this task adds it); unit-testable by invoking the handler directly with a synthetic S3 event.

---

## Phase 6 — Reporting & natural-language queries

### T027 — CSV export
- Status: [ ] Not started
- Depends on: T022
- Goal: Implement SPEC.md §18 — an endpoint that exports a household's receipts/items (with category, payment method, dates) as CSV.
- Can run in parallel with T028.
- Acceptance criteria: Export respects any date-range/category filters passed in; large households don't time out the Lambda (stream the response or paginate — decide at build time and document the choice).

### T028 — Natural-language query endpoint
- Status: [ ] Not started
- Depends on: T022
- Goal: Implement SPEC.md §16 — free-form question answering over the fields already modeled (receipts, items, categories, payment methods, dates, merchants, locations). Example: "Show me purchases from the last 6 months made with my Visa ending in 1234."
- Can run in parallel with T027.
- Acceptance criteria: Decide and document the parsing approach (e.g. Bedrock translating NL → structured query against the existing endpoints/DB) before building; no new data fields are needed beyond what's already in DATA_MODEL.md per SPEC.md §16.

---

## Phase 7 — Frontend

### T029 — Auth & household onboarding UI
- Status: [ ] Not started
- Depends on: T015
- Goal: Sign-up/sign-in (Cognito), create-a-household flow, join-via-invite-code flow.
- Acceptance criteria: Matches SPEC.md §2 exactly — no per-user attribution UI, no email-invite UI (code/link only).

### T030 — Receipt capture & review UI
- Status: [ ] Not started
- Depends on: T025, T029
- Goal: Camera/file upload (PWA), review screen highlighting low-confidence fields/items (SPEC.md §5) with inline correction, duplicate-warning modal (SPEC.md §6).
- Acceptance criteria: Every correction made in this UI results in an audit log entry (verify against T012's endpoint/contract, not just visually).

### T031 — Budgets & pacing dashboard
- Status: [ ] Not started
- Depends on: T022, T029
- Goal: Per-category budget view (spent/remaining/%), trajectory line graph for pacing-enabled categories (SPEC.md §9), household savings/carryover total (§7).
- Can run in parallel with T032.

### T032 — Special budgets UI
- Status: [ ] Not started
- Depends on: T018, T029
- Goal: Create/view a special budget (e.g. "Ireland Summer 2026"), estimate ranges per category, before/after comparison.
- Can run in parallel with T031.

### T033 — Reports & NL query UI
- Status: [ ] Not started
- Depends on: T027, T028, T029
- Goal: CSV export button/flow; a simple chat-like or search-bar interface for natural-language queries (SPEC.md §16).

---

## Phase 8 — Hardening (pre-real-use)

### T034 — Package the real FastAPI app as the Lambda artifact
- Status: [ ] Not started
- Depends on: T033
- Goal: Replace the placeholder inline Lambda handlers in `infra/stacks/atomize_stack.py` with a real packaged build of `apps/api` (per the gap flagged in `infra/README.md` since T005).
- Acceptance criteria: `cdk deploy` produces a working API Gateway endpoint serving the real FastAPI app, not the `"Atomize API placeholder"` stub.

### T035 — VPC-attach the API Lambda to reach RDS
- Status: [ ] Not started
- Depends on: T034
- Goal: Resolve the networking gap flagged in `infra/README.md` since T005 — VPC-attach the API Lambda (with VPC endpoints for S3/Bedrock/Textract so a NAT gateway isn't required) so it can actually reach the RDS instance.
- Acceptance criteria: API Lambda successfully queries Postgres in a deployed (not just synthesized) stack; no NAT gateway added (stay in the free-tier-conscious posture from TECH_STACK.md) unless a documented reason requires one.

### T036 — Basic observability
- Status: [ ] Not started
- Depends on: T035
- Goal: CloudWatch alarms/dashboards for the API Lambda (errors, latency, throttles) and the scheduled jobs (failures).
- Acceptance criteria: At minimum, a failed month-close ledger run or image-retention sync job is not silently swallowed.

---

## Deferred / explicitly out of scope

Per SPEC.md §21 — do not build these without a new round of spec clarification first: custom categories, HSA/FSA/tax-advantaged programs, asset tracking, income modeling, bank account connections, multi-currency households, per-user expense attribution, native mobile app (TECH_STACK.md notes this as "later," not scheduled).
