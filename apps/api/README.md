# MockMate AI — API (FastAPI)

## Setup
```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set MOCKMATE_SECRET_KEY; DATABASE_URL for Neon in prod
uvicorn app.main:app --reload --port 8000
```

## Endpoints (`/api/v1`)
- `GET /health` — service health
- `POST /auth/setup-pin` — first-run only, 4–12 digit PIN (PBKDF2-HMAC-SHA256)
- `POST /auth/login` / `POST /auth/logout` / `GET /auth/me` — httpOnly signed session cookie, 7 days
- `GET /onboarding/status`, `POST /onboarding/profile`
- `POST /providers/validate` — live Groq check (GET /models + tiny completion, max_tokens 5)
- `POST /providers`, `GET /providers` (masked keys only), `POST /providers/{id}/test`, `DELETE /providers/{id}`, `GET /providers/usage`

Provider keys are encrypted with Fernet (key derived from `MOCKMATE_SECRET_KEY`) and never logged or returned in full.

## Migrations
```bash
alembic upgrade head
```
