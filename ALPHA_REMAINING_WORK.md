# Kora Alpha: Remaining Work and Launch Readiness

**Review date:** 2026-11-16  
**Purpose:** Track the work needed to complete the Alpha workflows and safely begin real-user testing.

This review compares [PROJECT_SPECS.md](PROJECT_SPECS.md) with the code and tests currently in the workspace. It describes the current repository state, including existing uncommitted changes; it is not a claim that every workflow has been validated in production.

## Status at a Glance

| Area | Current status | What remains |
|---|---|---|
| Inventory CRUD and stock changes | Partial | Basic operations exist; aliases, units, low-stock thresholds, and more natural matching are missing. |
| Sales and purchases | Partial | Recording and inventory updates exist; purchase coverage, multi-item conversations, duplicate transaction protection, and correction after recording need work. |
| Expenses | Not started | No expense model, service, conversation intent, or history. |
| Business insights | Not started | No reporting or aggregation service or insight intents. |
| Conversation state | Partial | Redis-backed sessions, slot collection, confirmation, cancellation, and same-message deduplication exist; production Redis behavior and recovery need end-to-end validation. |
| Launch and operations | Needs verification | Webhook setup documentation is stale, and public endpoint security and failure handling need a launch check. |
| Automated tests | Partial | 43 tests pass in the project virtual environment; most transaction, integration, and reporting behavior is not covered. |

## Already Present

- Product creation, listing, lookup, update, deletion, and stock adjustment, scoped to the current user. Product names are normalized for case and surrounding whitespace.
- Basic product quantities and cost/selling prices, with validation for product data.
- Sale and purchase transaction services. They update stock and persist transaction/items in one database commit; sales reduce stock and purchases increase it.
- Transaction lookup, an unfiltered transaction list, and receipt text generation.
- A conversational flow with missing-slot prompts, confirmation before writes, corrections before confirmation, cancellation/restart, and unfinished state stored in Redis with a TTL.
- Duplicate delivery suppression when the inbound message includes the same provider message ID.
- Regression tests for inventory CRUD and selected dialogue flows.

Relevant implementation: [dispatch service](app/services/dispatch_service.py), [inventory service](app/services/inventory_service.py), [sales service](app/services/sales_service.py), [session service](app/services/session_service.py), and [dialogue tests](tests/dialogue/test_dialogue.py).

## Work Required for the Alpha Spec

### P0: Complete and Verify the Core Transaction Loop

- [ ] Add service and conversation tests for purchases, including stock increase, amount calculation, invalid quantities/prices, and rollback when any part of a transaction fails.
- [ ] Verify sales and purchases against PostgreSQL, including simultaneous updates to the same product. The current test database is SQLite and does not prove production locking behavior.
- [ ] Decide whether a sale should use the product's saved selling price by default, require a price each time, or support both. Make the behavior explicit in prompts and tests.
- [ ] Support multi-message completion for sale/purchase fields and test that values are merged correctly. The conversation extractor currently rejects requests with multiple detected items, even though the transaction service accepts an item list.
- [ ] Add durable transaction idempotency. Provider message-ID deduplication only covers repeated delivery of the same identified message; it does not prevent a user or provider retry with a different/missing ID from recording the same sale twice.
- [ ] Add a transaction correction/void workflow for mistakes after confirmation has been committed. Current cancellation and correction apply before execution, not to an already-recorded transaction.
- [ ] Add a recent-sales view (or clearly scope the current all-transactions list). The current history operation lists transactions without a recent-sales filter.

**Done when:** A real WhatsApp test can add stock, record a sale, confirm that stock and transaction history agree, record a purchase, and safely retry a delivery without creating duplicate business records.

### P1: Add Expenses

- [ ] Define and persist expenses, including amount, category, description, and timestamp, associated with the correct business/user.
- [ ] Add natural-language expense capture with missing-field collection, validation, confirmation, cancellation, and recent-expense history.
- [ ] Add tests for expense creation, invalid/incomplete requests, category handling, user isolation, retry behavior, and history.
- [ ] Specify how purchases and expenses contribute to profit calculations so purchase costs are not accidentally counted twice.

**Done when:** A user can record and retrieve a categorized expense through the same conversational workflow as inventory and sales.

### P1: Add Business Insights

- [ ] Implement today's sales and expenses, estimated profit, weekly/monthly summaries, best-selling products, sales by product, and expense breakdown.
- [ ] Add low-stock product reporting; the current product model has no reorder/low-stock threshold, so define and persist one before calculating this report.
- [ ] Define date boundaries and business timezone behavior. Current timestamps are UTC-naive and there is no reporting date filter.
- [ ] Define the profit formula and wording, especially whether the Alpha estimate is revenue minus recorded expenses or includes cost of goods sold.
- [ ] Add tests with known transaction fixtures for date boundaries, aggregation, empty periods, and each summary calculation.
- [ ] Add insight intents/routes and concise responses grounded in database results, not generated estimates.

**Done when:** Each requested summary matches independently calculated expected values for fixed test data and the user's business-day timezone.

### P1: Improve Inventory Understanding

- [ ] Add product aliases or an equivalent matching strategy for common alternate names and spelling variations; current lookup is normalized exact-name matching.
- [ ] Define supported units and store/validate them with quantities. Quantities are currently integer counts with no persisted unit.
- [ ] Add configurable low-stock thresholds and a low-stock query/notification behavior.
- [ ] Test natural phrasing, ambiguity, misspellings, name collisions, and invalid reductions through the real extraction and confirmation path.

**Done when:** Common names and quantity/unit phrases resolve consistently, ambiguous matches ask the user to clarify, and stock cannot become negative.

### P1: Verify Conversation Reliability with Real Dependencies

- [ ] Add integration tests using Redis for state persistence between messages, TTL expiry, concurrent updates, duplicate message IDs, and recovery after an interrupted execution.
- [ ] Test intent switching, cancellation, corrections, incomplete input, ambiguous input, and graceful model/service failure across inventory, sales, and purchases.
- [ ] Test Twilio webhook delivery and response behavior, including provider retries and missing message IDs.
- [ ] Confirm failures do not leave tasks stuck in an executing state or tell the user a write succeeded when it did not.

Current dialogue tests replace the production session service with an in-memory fake. They verify useful state transitions, but do not validate Redis itself or a full WhatsApp-to-database request.

## Launch Checks Before Inviting Real Users

- [ ] Validate the deployed environment using the production database and Redis, required model files, Twilio credentials, and Gemini configuration. Confirm restart and recovery behavior.
- [ ] Verify Twilio webhook signatures before accepting public webhook requests; signature validation is not present in the current message endpoint.
- [ ] Confirm OTP abuse protections, secret handling, database backups, and a way to inspect errors and failed messages before exposing the service publicly.
- [ ] Run a small, supervised pilot with test accounts and a recovery procedure for incorrect or duplicate records.
- [ ] Update the onboarding docs: the README currently documents `/webhook`, `/request-otp`, and `/verify-otp`, while the routers expose `/conversations/`, `/otp/send`, and `/otp/verify`. The README/setup instructions also refer to `app/requirements.txt`, while the requirements file is at the repository root.

These are launch checks, not all new product features. A limited pilot can be useful before all Alpha reporting features are complete, but it should be described as an inventory/transaction pilot, not as the complete Alpha in the spec.

## Verification Snapshot

- `venv\Scripts\python.exe -m pytest`: **43 passed** in the project virtual environment.
- Running `pytest` with the active global interpreter failed during collection because that interpreter does not have the `redis` package installed. Use the project virtual environment for the current test suite.
- Existing tests cover inventory CRUD and selected dialogue cases. There are no expense or insight tests, and purchase behavior, live Redis, Twilio webhook integration, and production database concurrency are not covered.

## Suggested Order

1. Make the supervised pilot safe: verify webhook security, production configuration, retry/idempotency behavior, and transaction rollback/recovery.
2. Complete and test purchase/sale correctness and the full stock-in-to-sale workflow.
3. Implement expense capture and history.
4. Implement and verify insight calculations, including date/time and profit rules.
5. Add low-stock thresholds, aliases, and unit handling; then update setup and onboarding documentation.
