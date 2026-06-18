# PocketPal Backend

FastAPI service for PocketPal / Personal Finance HQ.

## Run

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```bash
pytest
```

## Notes

Schema changes live in `../supabase/migrations`. The backend does not run Alembic and does not auto-migrate on startup. Webhook processing uses FastAPI `BackgroundTasks` for V1; replace it with a durable worker queue before production use.

