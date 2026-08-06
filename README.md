# AI-Powered Trend Intelligence

Production SaaS platform by Foluxnova. Monitors trends across platforms, explains why they matter for founders/creators/businesses, and generates ready-to-publish content.

See `docs/2026-08-06-trend-intelligence-roadmap.md` for the full architecture review and phased build plan. This repo is built one phase/feature at a time against that roadmap.

## Stack

Frontend: Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui + React Query + Axios
Backend: Django + Django REST Framework + PostgreSQL + Celery + Redis
AI: OpenAI + Claude behind a provider abstraction (`backend/ai_providers/`)

## Local development

Prerequisites: Python 3.11+, Node 22+. Everything runs natively — no Docker.

Quickest path: `./scripts/dev.sh` runs backend + frontend together in one terminal (installs
dependencies on first run). See below for the equivalent step-by-step commands.

By default, dev uses SQLite (no Postgres install needed) and runs Celery tasks synchronously,
in-process (`CELERY_TASK_ALWAYS_EAGER=True` in `config/settings/dev.py`) — so trend polling
works with zero extra services running. PostgreSQL and Redis are only required for
production-parity testing or once you want to run a real Celery worker/beat locally.

Backend:
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env   # then fill in DATABASE_URL/REDIS_URL for your local Postgres/Redis
python manage.py migrate
python manage.py runserver
```

Frontend:
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Celery, for real async/scheduled behaviour (needs Redis running and
`CELERY_TASK_ALWAYS_EAGER=False` in your `.env`):
```bash
cd backend
celery -A config worker -l info
celery -A config beat -l info
```

## Trend monitoring

Platforms (Google Trends, specific subreddits, RSS feeds) are rows in the `Platform` table,
each pointing at a registered adapter (`backend/apps/trend_sources/adapters.py`). To try it locally:

```bash
cd backend
python manage.py seed_platforms   # creates the starter set of platforms
python manage.py poll_now         # fetches from every active platform immediately
```

`poll_now --platform <slug>` polls just one. In production, Celery Beat calls
`poll_due_platforms` every 5 minutes, which only fans out to platforms whose own
`poll_interval_minutes` has actually elapsed. Reddit requires `REDDIT_CLIENT_ID` /
`REDDIT_CLIENT_SECRET` (a "script" app at reddit.com/prefs/apps) to be set in `.env`;
Google Trends and RSS work with no credentials.

## Deployment

Deployed to Render as native (non-Docker) services, defined in `render.yaml`:
`trend-intelligence-backend` (Django/gunicorn web service), `trend-intelligence-celery-worker`
and `trend-intelligence-celery-beat` (background workers), `trend-intelligence-redis`
(managed Redis), and `trend-intelligence-frontend` (Next.js web service). Postgres is
provisioned from the `databases:` block. In the Render dashboard: New → Blueprint →
point at this repo → Render reads `render.yaml` and creates all five resources. Env vars
marked `sync: false` (API keys, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `NEXT_PUBLIC_API_URL`)
need to be filled in manually after the first deploy, once you know the actual service URLs.

## Testing & linting

```bash
# backend
cd backend && pytest --cov=apps && flake8 apps config --exclude=migrations && black --check .

# frontend
cd frontend && npm run lint && npx tsc --noEmit && npm run build
```

Both run in CI on every PR (`.github/workflows/ci.yml`).

## Repository layout

```
backend/    Django project (config/ settings, apps/ feature modules, ai_providers/)
frontend/   Next.js app (app/ routes, features/ feature modules, components/ui/ design system)
docs/       Architecture roadmap and any future ADRs
```

## Status

Phase 0 (foundation), Phase 1 (authentication — email + Google OAuth, JWT), and Phase 2
(trend engine — modular platform adapters, dedup, trend feed API) are complete. See the
roadmap for build order and what's next.
