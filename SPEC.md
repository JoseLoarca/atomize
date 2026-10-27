# Atomize — Product & Data Spec (v1)

Status: Working draft, incorporates decisions made after initial overview review.

## 1. Goal

Household expense tracking app that uses AI to parse receipts down to the line-item level, categorizes spend, and tracks it against category budgets — with trend/pacing analysis over time.

Not in scope for now: bank connections, net-worth tracking (beyond category carryover, see §7), income modeling.

## 2. Households & Users

- The unit of account is a **Household**, not an individual user.
- Whoever creates a household automatically becomes its **Super User**.
- The Super User adds **Contributors** to the household via a **shareable invite code/link** — anyone who has it can join the household. No email dependency required.
- A household supports **N contributors** (no fixed cap).
- Roles:
  - **Super User**: everything a Contributor can do, plus defines budgets, categories, and settings.
  - **Contributor**: uploads receipts, tags receipts with context, views analytics/trends/reports.
- **No per-user attribution.** Receipts and expenses belong to the household as a whole — there is no "who spent this" tracking in v1. All contributors see the same shared budgets and totals.
- Households are **USD-only** for now. No multi-currency households. (A single receipt can still be in a foreign currency — see §12 — but the household's reporting currency is always USD.)

## 3. Core Data Concepts

### Receipt
Represents a single transaction. Immutable fact once captured (corrections are layered on top, see §5).

Key fields:
- Merchant name
- Date & time (see §9 for timezone handling)
- Location (city, country; address if present)
- Original currency
- Exchange rate (if not home currency), stored at transaction time
- Total amount
- Taxes (explicit total, if present)
- Payment method (free-form label)
- Line items (if available)

Receipts can be:
- Fully itemized
- Partially itemized
- Total-only (see §8 for categorization rule)

### Line Item (ExpenseItem)
The atomic unit of categorization.

Fields:
- Description
- Quantity
- Unit price
- Total price (pre-tax)
- Assigned category
- Confidence score (AI classification)
- Optional tags (future-safe, minimal use for now)

## 4. Categories

- Single canonical, flat, mutually exclusive category list (see overview for the default list).
- No subcategories, no custom categories in v1.
- **v1 constraint: one category per receipt.** A receipt is not yet split across multiple categories by line item — see §8 for the planned evolution and its tax-allocation complication.

## 5. Receipt Corrections & Audit Trail

- Every edit or correction to a receipt or line item (category reassignment, amount fix, merchant fix, etc.) is recorded in an **audit trail**: who/when/what changed, original AI-assigned value vs. corrected value. Entries are append-only.
- On upload, any field or line item below the confidence threshold is **visually highlighted** in the review UI so contributors can see and fix it before it's finalized.
- Confidence threshold is **fixed/global for now**; per-household configurability is deferred (same posture as §13 below).

## 6. Duplicate Receipt Detection

- On upload, the system checks existing receipts in the household for a match on: **amount + merchant + date/time + payment method**.
- If all four match an existing receipt, the system does **not** silently block the upload — it warns the user ("this looks like a duplicate of [receipt], upload anyway?") and lets them confirm or cancel.
- This is a soft warning, not a hard rule — matches are possible (e.g., two genuinely separate $4.50 coffee purchases at the same merchant on the same payment method within the same minute), so the user always has final say.

## 7. Budgets

- Budgets are **monthly, per category**. Fields: category, budget amount, optional notes.
- Budgets do not care about payment method, merchant, tax mechanics, or contributor — only category totals over time.

### Carryover
- Unused budget in a category **does not roll forward** into the next month's budget amount. February's Groceries budget is always its configured amount (e.g., $100), regardless of January's underspend or overspend.
- However, unspent amounts **do accumulate into a running household "saved" total**, tracked separately from the monthly budget figures — effectively a lightweight net-worth-adjacent number, but explicitly scoped to "money not spent against budget," not a full net-worth tracker. This carryover total is visible to users as its own figure, distinct from any single month's budget view.

## 8. Multi-Category Receipts (Planned, Not v1)

- v1: one category per receipt (§4).
- **Planned evolution**: allow a single receipt to contain line items across multiple categories (e.g., a Market Basket trip with groceries, cat litter under Pets, and a gift under Gifts & Donations).
- **Tax allocation resolution**: no new rounding logic is needed. Tax is allocated using the largest-remainder method (§11) across **all items on the receipt, receipt-wide, regardless of category** — this is the same single allocation pass as today. Only *after* each item has its final rounded tax share does the system roll items up into their respective categories (summing already-rounded cent values). Because allocation happens once, receipt-wide, before category rollup, the receipt-level tax total is guaranteed to reconcile exactly, and category totals simply inherit correct, already-rounded numbers — multi-category receipts don't introduce a second rounding step.

## 9. Total-Only Receipts

- When a receipt has no line items, its category is **inferred from the merchant**, not left uncategorized.
- Example: a total-only receipt from a gas station → `Gas`. A total-only receipt from a grocery store → `Groceries`.
- This requires a merchant → default-category mapping (maintained by AI merchant normalization, correctable by the user, and subject to the same audit trail as any other categorization).
- The mapping is **household-level and forward-only**: any household member can correct a merchant's mapping, and the correction applies to future receipts from that merchant. Past total-only receipts already categorized under the old mapping are left untouched unless manually edited.

## 10. Date & Timezone Handling

- All receipts are normalized to and reported against the **household's home timezone** for budgeting, pacing, and month-boundary calculations.
- The **local time at the point of purchase** (i.e., the receipt's own timezone, e.g., while traveling) is still stored and displayed on the receipt itself.
- Example: a household based in US/Eastern with a receipt timestamped 11:30 PM local in Dublin — the receipt detail shows "11:30 PM (Dublin time)," but it counts toward whichever home-timezone day/month it falls into for budget/pacing purposes.

## 11. Taxes

- Tax Handling Strategy: **Proportional Allocation**, per item, based on each item's share of the receipt's pre-tax subtotal.
- Tax is stored as its own entity (`ExpenseTax`), distinct from items, but allocated and attributed to category totals.
- **Rounding rule (largest remainder method):**
  1. Compute each item's exact proportional tax share (not rounded).
  2. Truncate each share down to the nearest cent.
  3. Compute the leftover: `total tax − sum(truncated shares)`.
  4. Distribute the leftover one cent at a time to the items with the largest fractional remainder (descending order) until the leftover is exhausted.
  - This guarantees item-level tax shares always sum exactly to the receipt's stated total tax, deterministically and reversibly, consistent with the "correctness over cleverness" philosophy.

## 12. Returns & Refunds

- Modeled as **negative expenses**, never deletions. Original receipts remain intact.
- **Item Return**: one or more line items get negative counterparts; category totals adjust automatically.
- **Receipt-Level Refund**: recorded as a negative receipt, linked to the original merchant and payment method.
- **Effect on pacing/trend analysis**: a return is treated **as if the original purchase never happened** for pacing-line and trend math (i.e., the trajectory line recalculates as though that spend didn't occur). However, the return event itself remains **visible** in the receipt/transaction history — it's excluded from the pacing math, not hidden from the user.
- No income modeling in v1. Refunds only offset expenses.

## 13. Budget Pacing / Trajectory

- For variable-spend categories, the app shows: spent so far, expected spend by today (linear, day-based model), and ahead/behind status.
- Pacing is **opt-in per category** via `show_pacing: true/false`, defaulting on for variable categories (groceries, dining, shopping, travel, etc.) and off for fixed/lump-sum categories (rent, insurance, utilities, subscriptions).
- If pacing is disabled: budget totals still show, but no trajectory line or ahead/behind messaging.

## 14. Special Budgets (Travel, Events)

- Special budgets are **budget groups**, not categories (e.g., "Ireland Summer 2026"). They include a date range, category-level estimates (ranges allowed), and actual spend tracking during/after the event.
- They reuse the same category list and can enable pacing by default.
- **Isolation rule**: any expense tagged to a special budget lives entirely in that special budget's own world — it does **not** also count against that category's regular monthly budget for the month(s) it occurred in. E.g., a $200 dinner during the Ireland trip counts only against the trip's "Restaurants & Dining" estimate, not against the household's regular monthly Dining budget.

## 15. Payment Methods

- Lightweight, free-form labels (not verified, optional to "enroll"): e.g., Cash, "MASTERCARD 1234," Venmo, Apple Pay.
- Used for filtering, search, and natural-language queries. Not used for balance tracking or financial reconciliation.

## 16. Natural-Language Queries

- Goal: let a user ask free-form questions against their household's transaction history via the app, e.g.:
  - "Show me purchases from the last 6 months made with my Visa ending in 1234"
  - "How much did we spend on dining in Q2?"
- Scope for v1: query surface spans receipts, line items, categories, payment methods, dates, merchants, and locations — the fields already modeled elsewhere in this spec. No new data beyond what's already captured is required to support this; it's a query/interface layer on top of the existing model.
- Implementation approach (parsing engine, UI placement) is deferred to build time — not specified here.

## 17. Location & Context Data

- If present on the receipt: store address, city/country, currency.
- Stored for geographic spending analysis, travel analytics, and future seasonal/contextual insights.
- Exchange rate is stored at transaction time for accurate home-currency (USD) reporting and historical correctness.

## 18. Reports & Export

- CSV export is a v1 requirement — users can export their transaction/expense data out of the app.

## 19. Receipt Image Retention

- Receipt images (photos/PDFs) are **deleted after 6 months**. Parsed transaction data (merchant, amounts, items, categories) persists indefinitely; only the underlying image is purged.
- This is a placeholder policy — revisit if a use case emerges that needs longer image retention (e.g., warranty claims, disputes).

## 20. AI Responsibilities (Strictly Scoped)

AI does: OCR & parsing, itemization, initial category assignment, confidence scoring, proportional tax allocation, merchant normalization (incl. total-only receipt category inference, §9).

AI does not: invent categories, override user corrections, make financial judgments.

## 21. Explicitly Deferred (Out of Scope for v1)

- Custom categories (category list is fixed/stable for now; multi-category-per-receipt per §8 is the first planned evolution)
- Per-category confidence threshold configuration (fixed globally for now; household-configurable later)
- HSA/FSA/tax-advantaged programs
- Full asset tracking
- Income modeling
- Bank account connections
- Multi-currency households
- Per-user expense attribution within a household

The data model is intended to support all of the above without requiring rework.

## 22. Open Problems — Resolved

All three items previously flagged here have been resolved and folded into their respective sections:

- Multi-category tax allocation → §8
- Household invite flow → §2
- Merchant→category mapping governance → §9

## 23. Philosophy (Unchanged)

- Receipts are immutable facts.
- Interpretation layers (categorization, tax allocation, pacing) are configurable and correctable, with a full audit trail.
- Visualization is opt-in where ambiguity exists.
- Complexity is postponed, not ignored.
- The system favors correctness over cleverness.
