# PocketPal / Personal Finance HQ

## Overview

PocketPal is an offline-first, multi-currency personal finance ledger and
automation platform. It combines a React Native mobile app, a FastAPI backend,
Supabase Auth, Supabase PostgreSQL, append-only accounting records, sandbox
bank webhook ingestion, deterministic balance reconciliation, and frozen FX
valuation.

This is designed as a serious personal finance engineering project rather than a basic CRUD expense tracker.

## Why This Project Exists

Personal finance data gets hard once the app has to work offline, accept
at-least-once mobile sync, ingest external bank snapshots, preserve audit
history, and keep analytics clean. PocketPal demonstrates those real-world
constraints directly:

- Local mobile writes are queued with stable UUIDs and client revisions.
- Backend sync is idempotent and revision-aware.
- Finalized ledger entries are not destructively edited.
- Bank balance snapshots are reconciled against the ledger as of the snapshot timestamp.
- FX values are frozen when transactions are accepted so historical analytics do not drift.
- System adjustments affect balances but stay out of income, expense, and burn-rate KPIs.

## Core Features

- Offline-first manual transaction queue
- Supabase Auth and RLS
- Append-only ledger
- Sandbox bank webhook ingestion
- Deterministic reconciliation
- Multi-currency support
- Frozen FX valuation
- Dual-balance mobile dashboard
- Analytics contamination prevention
- OAuth degraded-state handling

## Architecture

```text
Mobile App
  - Expo / React Native
  - expo-sqlite local queue
  - AsyncStorage token/preferences
        |
        v
FastAPI Backend
  - Supabase JWT validation
  - revision-safe sync
  - money, FX, dashboard services
        |
        v
Supabase / PostgreSQL
  - Auth users
  - RLS policies
  - append-only ledger
  - analytics view

Webhook Provider
        |
        v
FastAPI Webhook
  - provider verifier
  - quick HTTP 200
        |
        v
Background Task
  - normalize payload
  - idempotent inserts
  - balance snapshot
  - reconciliation

Exchange Rate Service
        |
        v
FX Table
        |
        v
Dashboard Analytics
```

## Tech Stack

- Backend: FastAPI, Python 3.11, Pydantic, asyncpg connection pool
- Database: Supabase PostgreSQL
- Auth: Supabase Auth JWT validation
- Migrations: Supabase CLI raw SQL migrations only
- Mobile: Expo Managed Workflow, React Native, TypeScript
- Local storage: expo-sqlite for transaction queue, AsyncStorage for small tokens/preferences
- Webhooks: provider verifier abstraction with mock-bank HMAC support
- Testing: pytest, pytest-asyncio
- Deployment path: containerized FastAPI plus Supabase-managed Postgres/Auth

## Repository Map

- `backend/`: FastAPI API, domain services, webhook processors, and backend tests.
- `mobile/`: Expo / React Native mobile app with SQLite offline sync queue.
- `supabase/`: Raw SQL migrations, local Supabase config, and seed data.
- `legacy_streamlit/`: Preserved Streamlit prototype from the original app.

## Ledger Philosophy

PocketPal treats money movement as an accounting ledger.

- `pending`: manual entries accepted by the backend but not yet cleared or matched.
- `cleared`: finalized entries from a trusted source or manual-only cash account.
- `adjusted`: system reconciliation rows that make the ledger match a bank snapshot.

Manual pending entries may be updated if the incoming `client_revision` is
newer. Cleared, adjusted, system-generated, reconciliation, and opening-balance
rows are not destructively edited. Corrections after finalization happen
through reversals or compensating entries.

Day Zero onboarding uses an opening-balance transaction so a newly linked
account does not begin life with an ugly reconciliation adjustment.

## Money Model

PocketPal bans IEEE 754 floating-point math for money.

- `amount_minor`: native transaction amount in integer minor units.
- `currency`: the native transaction currency, such as PHP, USD, JPY, or KWD.
- `currency.exponent`: the number of decimal places for display and conversion.
- `base_currency`: the user's reporting currency.
- `amount_minor_base`: frozen reporting value in base-currency minor units.
- `exchange_rate_to_base`: rate used to freeze the base value.

Display uses `amount_minor / (10 ^ currency.exponent)`. JPY uses exponent `0`;
KWD uses exponent `3`. The backend uses Python `Decimal` for conversion and
stores money as `BIGINT`.

## Reconciliation Model

Bank current balance is the reconciliation ground truth. PocketPal stores
immutable `account_balance_snapshots` from the provider and compares:

```text
bank current balance at snapshot.as_of
vs.
local ledger sum where ledger_cutoff_at <= snapshot.as_of
```

Reconciliation is performed in the account's native currency first.
`available_balance` is stored for display and context, but it is not used as the
reconciliation target.

If the snapshot and ledger differ, PocketPal creates one system reconciliation
transaction plus one `reconciliation_adjustments` row for that account/snapshot
pair. Later corrections reverse or supersede adjustments; historical rows are
not deleted.

## Offline Sync Model

The mobile app writes new manual transactions to SQLite first. Each queued row has:

- `local_transaction_uuid`
- `client_revision`
- `sync_state`
- native integer `amount_minor`
- IANA timezone-aware timestamp data

Sync is at-least-once. The backend generates the idempotency key
`manual:{local_transaction_uuid}` and returns per-record statuses:

- `inserted`
- `updated`
- `already_synced`
- `stale_ignored`
- `failed`

Revision `2` can replace revision `1` while the server row is still pending.
Revision `1` cannot overwrite revision `2`. The server uses `ledger_status`;
`local_unsynced` exists only in the mobile SQLite queue.

## Security Model

PocketPal validates Supabase JWTs in the FastAPI dependency
`get_current_user()`. It extracts `sub` as the authenticated user ID and does
not trust `user_id` from request bodies.

Supabase RLS is enabled on user-owned tables:

- `user_preferences`
- `accounts`
- `account_connection_events`
- `transfer_groups`
- `transactions`
- `account_balance_snapshots`
- `reconciliation_adjustments`

Reference tables such as `currencies` and `exchange_rates` are readable by
authenticated users. Provider webhooks are verified through provider-specific
verifier classes. The mock bank uses HMAC-SHA256. Plaid is intentionally
represented by a separate verifier placeholder and is documented as a TODO
rather than falsely treated as mock HMAC.

Secrets live in environment variables. No production secrets belong in the repository.

## Getting Started

1. Install prerequisites: Python 3.11+, Node.js, npm, Expo CLI, Docker, and Supabase CLI.
2. Clone the repository.
3. Copy `.env.example` to `.env` and fill local development values.
4. Start Supabase:

```bash
supabase start
```

5. Apply migrations:

```bash
supabase db reset
```

6. Seed data is included in `supabase/seed.sql` and the migrations.
7. Run FastAPI:

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

8. Run Expo:

```bash
cd mobile
npm install
npx expo start
```

## Environment Variables

```env
APP_ENV=development
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=replace_me
SUPABASE_JWT_SECRET=replace_me
SUPABASE_SERVICE_ROLE_KEY=replace_me

DEFAULT_BASE_CURRENCY=PHP
DEFAULT_TIMEZONE=Asia/Manila

MOCK_WEBHOOK_SECRET=replace_me
PLAID_CLIENT_ID=replace_me
PLAID_SECRET=replace_me
PLAID_ENV=sandbox

CORS_ORIGINS=http://localhost:8081,http://localhost:19006
```

## Backend Commands

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
python -m pytest -q
```

## Mobile Commands

```bash
cd mobile
npm install
npx expo start
npx expo start --ios
npx expo start --android
```

## API Overview

- `GET /health`: returns service health.
- `GET /dashboard`: returns projected balance, settled balance, pending manual
  total, account cards, KPIs, and reconnect actions.
- `POST /sync`: accepts offline manual queue entries with idempotent, revision-safe upsert behavior.
- `POST /accounts/mock-connect`: creates a sandbox account, stores the Day Zero
  snapshot, ingests historical transactions, and creates the opening balance.
- `POST /webhooks/bank/{provider}`: verifies provider signatures, persists
  events, normalizes mock-bank transactions, stores snapshots, and runs
  reconciliation.

## Testing

Backend tests cover the acceptance scenarios:

- offline edit revision ordering
- stale overwrite prevention
- Day Zero opening-balance math
- duplicate webhook idempotency
- temporal snapshot reconciliation
- analytics contamination prevention
- currency exponent behavior
- frozen FX historical value
- OAuth degraded-state contract
- RLS policy coverage

Run:

```bash
cd backend
python -m pytest -q
```

## Known V1 Limitations

- Sandbox/mock banking only.
- FastAPI `BackgroundTasks` are process-bound and should be replaced before production.
- FX rates are seeded prototype rates unless a provider is added.
- No production trading or investment execution.
- No real money movement.
- Plaid JWT/JWK verification is a TODO and is not represented as fake HMAC.

## Roadmap

- Durable worker queue
- Real Plaid/Brankas verification
- Real FX provider
- Advanced categorization
- Portfolio analytics
- Export/reporting
- Stronger audit review workflow

## Legacy Prototype

The previous Streamlit prototype has been preserved under `legacy_streamlit/`.

## License

MIT
