# MockMate AI — Practice smarter. Interview stronger.

Personal-first, SaaS-ready AI interview intelligence platform. **Phase 1 (foundation) is implemented;**
Phases 2–7 (resume/JD intelligence, interview engine, voice/video, reports, Interview DNA, SaaS) are not yet built.

## Architecture

```
mockmate-ai/
├── apps/web/   Next.js 14 App Router, TypeScript, Tailwind CSS
└── apps/api/   FastAPI (Python 3.12), SQLAlchemy 2, Alembic, pytest
```

Web → API over `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). The browser never
holds an LLM API key: keys are sent once to the backend, validated live against Groq,
encrypted (Fernet, key from `MOCKMATE_SECRET_KEY`), and shown masked only.

## Quick start (local)

```bash
# 1. API
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set MOCKMATE_SECRET_KEY
uvicorn app.main:app --reload --port 8000

# 2. Web (new terminal)
cd apps/web
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev   # http://localhost:3000
```

## First-run onboarding

1. Open http://localhost:3000 → `/onboarding`
2. **Welcome** — create a 4–12 digit owner PIN (first run only).
3. **Groq setup** — paste your Groq API key, click **Test connection**. The backend calls
   Groq's live `GET /models` plus a tiny chat completion (`max_tokens: 5`); only both
   succeeding counts as connected, and the model dropdown is populated from that live
   response — no model is hard-coded. Save to encrypt and store the key.
4. **Profile** — name, target roles, experience level.
5. **Dashboard** — provider status, usage, recent sessions (empty until Phase 3).

Get a free Groq key at https://console.groq.com — never paste it in chat or commit it.

## How to supply a Groq key

Only through the onboarding UI or **Settings → AI provider settings** in the app.
There is no key in any config file, and `POST /api/v1/providers/validate` never logs
or returns the full key.

## Deployment (free tiers)

| Piece | Target | Notes |
|---|---|---|
| Web | Vercel (Hobby) | Set `NEXT_PUBLIC_API_URL` to the API URL |
| API | Render (free) | Set `DATABASE_URL`, `MOCKMATE_SECRET_KEY`, `CORS_ORIGINS`; free tier sleeps when idle |
| DB | Neon (free Postgres) | Set `DATABASE_URL=postgresql+psycopg2://…?sslmode=require`, then `alembic upgrade head` |

Local dev uses SQLite (`sqlite:///./mockmate.db`) by default.

## Tests

```bash
cd apps/api && .venv/bin/python -m pytest -q
cd apps/web && npm run build
```

## What is NOT done yet

Resume/JD intelligence, interview engine & personas, voice/video, evaluation & PDF
reports, Interview DNA, multi-user auth, billing. See `ARCHITECTURE_PLAN.md`.
