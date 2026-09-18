# LexiShelf

An AI-powered reading companion that explains unfamiliar words, phrases, and idioms in plain English,
organizes them by book/collection, and can save them straight to Notion. Includes spaced-repetition
review, cross-collection search, native pronunciation, an in-app AI agent (chat), and a Telegram bridge
to the same agent.

See [PROJECT.md](PROJECT.md) for the full product/architecture spec.

## Stack

- **Backend**: FastAPI + SQLModel, SQLite (local) / PostgreSQL (production), Alembic migrations
- **AI**: Groq (explanations + agent reasoning), CrewAI (agent orchestration)
- **Mobile**: Expo + React Native + TypeScript
- **Integrations**: Notion (OAuth, read/write), Telegram (bot bridge to the same agent)

## Project structure

```
backend/    FastAPI app, Alembic migrations, tests
mobile/     Expo/React Native app
render.yaml Render deployment blueprint for the backend
```

## Local setup

### Backend

Requires Python 3.11 (CrewAI does not support newer versions).

```powershell
cd backend
python3.11 -m venv .venv311
.\.venv311\Scripts\pip install -r requirements.txt
copy .env.example .env   # then fill in the values below
.\.venv311\Scripts\alembic upgrade head
.\.venv311\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run tests: `.\.venv311\Scripts\python -m pytest -q`

### Mobile

```powershell
cd mobile
npm install
copy .env.example .env   # set EXPO_PUBLIC_API_BASE_URL to your backend's address
npx expo start --web --port 8081
```

Typecheck: `npm run typecheck`

## Environment variables (backend/.env)

Never commit real values — `.env` is gitignored. See `backend/.env.example` for the full list. Key ones:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | `sqlite:///./lexishelf.db` locally, or a Postgres URL (e.g. Neon) in production |
| `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_AGENT_MODEL` | LLM provider + models for explanations vs. the agent |
| `NOTION_CLIENT_ID`, `NOTION_CLIENT_SECRET`, `NOTION_REDIRECT_URI` | Notion OAuth app credentials |
| `NOTION_OAUTH_STATE_SECRET`, `NOTION_TOKEN_ENCRYPTION_KEY` | Sign OAuth state and encrypt stored tokens |
| `JWT_SIGNING_SECRET` | Signs app auth tokens |
| `APP_WEB_URL` | Where the mobile web build lives (used for OAuth return links) |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` | Optional Telegram bridge (leave blank to disable) |

## Deployment

The backend deploys as a single service (the AI agent is a route within it, not a separate service).

1. Push this repo to GitHub.
2. In [Render](https://render.com): **New → Blueprint**, select the repo — it reads `render.yaml`.
3. Fill in the environment variables Render prompts for (see table above).
4. Use a persistent external Postgres (e.g. [Neon](https://neon.tech), free tier) for `DATABASE_URL` —
   Render's free tier has no persistent disk.
5. After the first deploy, update `NOTION_REDIRECT_URI` to the deployed URL and add that exact URL to
   your Notion integration's allowed redirect URIs.
6. Point the mobile app's `EXPO_PUBLIC_API_BASE_URL` at the deployed backend URL.
7. For Telegram: create a bot via `@BotFather`, set `TELEGRAM_BOT_TOKEN`, then call Telegram's
   `setWebhook` API once with the deployed URL's `/api/v1/telegram/webhook` endpoint and your
   `TELEGRAM_WEBHOOK_SECRET`.
