# AI-Powered Trend Intelligence

Production SaaS platform by Foluxnova. Monitors trends across platforms, explains why they matter for founders/creators/businesses, and generates ready-to-publish content.

See `docs/2026-08-06-trend-intelligence-roadmap.md` for the full architecture review and phased build plan. This repo is built one phase/feature at a time against that roadmap.

## Stack

Frontend: Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui + React Query + Axios
Backend: Django + Django REST Framework + PostgreSQL + Celery + Redis
AI: OpenAI + Claude behind a provider abstraction (`backend/ai_providers/`)

## Local development

Prerequisites: Docker, or Python 3.11+ and Node 22+ if running services natively.

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1/health/
- Django admin: http://localhost:8000/admin/

### Option B — run services natively

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

Celery (needs Redis running):
```bash
cd backend
celery -A config worker -l info
celery -A config beat -l info
```

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

Phase 0 (foundation) complete: settings split by environment, soft-delete/audit base model, health check endpoint wired end-to-end between frontend and backend, Docker Compose, CI pipeline. No product features yet — see the roadmap for build order.
