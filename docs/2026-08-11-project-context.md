# AI-Powered Trend Intelligence — Project Context

Last updated: 2026-08-11. This document is a handoff/reference file — its job is to give a new AI session or developer full working context on this project without needing the app rebuilt or re-explained. It reflects the actual current state of the codebase, not the original plan.

## 1. What this is

A real production SaaS product (not a demo), built by Foluxnova. It automatically collects business/startup/investment-relevant trends and turns them into ready-to-use content for three target audiences: **Content Creators**, **Founders**, and **Investors**.

Core operating principle, established explicitly by the product owner (Kolamu) on 2026-08-11: customers use the application entirely through the UI; the system handles collection, analysis, and scoring automatically in the background; the terminal is a development/ops tool only and must never appear in customer-facing copy or be required for normal use.

## 2. Tech stack

**Backend:** Django 5.2 + Django REST Framework 3.15, Celery 5.4 + Redis (broker and result backend), PostgreSQL in dev/prod, JWT auth (`djangorestframework-simplejwt`) plus Google OAuth, Cloudinary for image storage, `feedparser` for RSS, two AI providers behind a shared abstraction (OpenAI gpt-4o/gpt-4o-mini and Anthropic Claude), `django-filter` for API filtering, `gunicorn` + `whitenoise` in production.

**Frontend:** Next.js 16 (App Router) + React 19, TypeScript, Tailwind CSS v4, TanStack React Query for server state, Radix UI primitives, `react-hook-form` + `zod`, a custom design system ("I Speak Society" tokens) with full light/dark theme support.

**Deployment:** Render.com via `render.yaml` — five services (web, Celery worker, Celery beat, Redis, Next.js frontend) plus a managed Postgres database, defined in a single multi-service manifest. Briefly moved to Railway (2026-08-12 to 2026-08-19), then moved back after repeated build/deploy failures there. No Docker, no Kubernetes — deliberately kept simple per the product owner's explicit "don't over-engineer" instruction.

## 3. Backend apps (`backend/apps/`)

- **accounts** — custom user model, email auth (register/verify/reset), Google OAuth login, profile and account settings endpoints.
- **trend_sources** — `Platform` (source config, `is_active`, `poll_interval_minutes`, `last_polled_at`), `RawTrendSignal` (raw ingested items, unique on `platform`+`external_id`), adapter pattern in `adapters.py` (`@register_adapter`). `RSSAdapter` is the only adapter actually active in production right now. Reddit, Google Trends, YouTube, X, TikTok, and Instagram adapters exist in code from earlier development phases but are intentionally inactive — RSS-only is a deliberate product decision, not a missing feature.
- **trends** — `Category`, `Trend` (denormalized latest AI scores/fields — the fast-read copy), `TrendSourceLink`, `TrendStatus` lifecycle (active/expiring/expired), app-level dedup via `dedup_key`, ingestion service (`services.py: ingest_raw_signal`).
- **trend_analysis** — `TrendAnalysis` (full versioned history — a plain `ForeignKey` to `Trend`, deliberately not `OneToOne`, so re-analysis never destroys prior results), `analyze_trend()` service, the `analyze_trend_task` Celery task, and the `analyze_now` management command for manual/admin backfill.
- **content_studio** — `ContentBrief` (perspective, content_angle, four angle fields, talking points), `GeneratedContent` (hook, 30s/60s script, CTA, hashtags, thumbnail suggestion, remix template — versioned per type).
- **ai_chat** — conversational refinement of already-generated content, plus platform-conversion actions.
- **notifications** — in-app notification engine.
- **core** — `/api/v1/health/` liveness/readiness endpoint (checks actual DB connectivity, used by Render's `healthCheckPath` on the backend service).

**Removed:** an `analytics` app existed from an earlier phase (event logging + a dashboard) and was fully removed on 2026-08-09 at the product owner's explicit request — judged not core to the product's value proposition. Don't resurrect it without being asked.

## 4. Frontend structure (`frontend/`)

- App Router route groups: `(auth)` — login, register, forgot-password, reset-password, verify-email; `(dashboard)` — dashboard, trends (+ `[slug]` detail), content (+ `[id]`), notifications.
- `features/` — feature-based folders: `auth`, `dashboard`, `trends`, `content-studio`, `ai-chat`, `notifications`, `system-health`. Each typically has an `api/` subfolder (React Query hooks + fetch functions) and a `components/` subfolder.
- `components/ui/` — design-system primitives (button, card, badge, input, dialog, skeleton, theme-toggle, etc.), rewritten 2026-08 to match the "I Speak Society" reference design (primary #2563eb, accent #14b8a6, purple #7c3aed, gradient/glow buttons, hover-lift cards, frosted-glass nav). Full light/dark toggle lives in `lib/theme-provider.tsx`, with a no-flash inline script in `app/layout.tsx`.
- Existing component/variant prop names were preserved during the design-system rewrite specifically so no call sites broke — don't assume a fresh rewrite is needed to add new UI; extend what's there.

## 5. Core trend pipeline (current state, RSS-only)

```
Celery Beat (5-min heartbeat: poll_due_platforms)
  → checks each Platform.is_due() against its own poll_interval_minutes
    (the seeded RSS platform is set to 20 minutes)
  → poll_platform task fetches via RSSAdapter (feedparser)
  → RawTrendSignal.get_or_create (unique on platform + external_id — safe to re-run)
  → if genuinely new signal → ingest_signal task
  → ingest_raw_signal() creates/attaches a Trend (app-level dedup via dedup_key)
  → if genuinely new Trend → analyze_trend_task fires automatically
  → AI provider computes: trend_score, opportunity_score, confidence_score,
    audience relevance (content_creator_score / founder_score / investor_score,
    0-100 each), best_audience (ALWAYS computed in Python from the three
    scores — never trusted from the AI's own claim), why_it_matters,
    what_is_happening, trend_stage, estimated_lifespan, suggested_content_angle
  → stored on Trend (denormalized "latest") AND a new TrendAnalysis row
    (versioned history)
  → appears in the trend list automatically once analyzed, UNLESS all three
    audience scores are below 60 (relevance-noise filter, added 2026-08-11,
    opt-out via ?include_low_relevance=true on the trend list endpoint)
```

Manual overrides that exist by design and should stay: the "Analyze now" / "Re-analyze" button on the trend detail page (`ReanalyzeTrendView`), and the `analyze_now` management command for admin/dev backfill. Neither is required for normal operation — they're overrides, not the primary path.

## 6. Customer-facing content generation flow

Trend detail page → customer reviews trend intelligence (audience relevance scores, why it matters, trend stage/lifespan, suggested content opportunity) → chooses a **Content Perspective** in the Content Studio panel (independent of `best_audience` — a pure intelligence signal, never a restriction on what the customer can pick) → clicks **Generate Content Brief** (this button must never be removed — it's the core paid-feature action) → AI generates a content angle plus four angle blurbs and talking points, using the trend's full intelligence context weighted by the chosen perspective → customer can then generate individual content pieces (hook, 30s script, 60s script, CTA, hashtags, thumbnail suggestion, remix template) → edit and save.

## 7. Key design decisions worth knowing before changing anything

- `best_audience` is always computed in Python (`_compute_best_audience()` in `ai_providers/base.py`) from the three numeric scores — never trusted from the AI's JSON response. This is deliberate and tested; don't "simplify" it by trusting the AI's own label.
- `TrendAnalysis` is a plain `ForeignKey` (not `OneToOne`) to `Trend` — intentional versioned history. Re-analysis must never delete or overwrite old rows.
- **Content Perspective** (chosen per content brief, drives generation tone/angle) and **Best Audience** (computed per-trend, an intelligence signal) and **Audience Relevance** (the three raw per-persona scores) are three explicitly separate concepts. Do not conflate them in future features — a trend's best audience being "Founders" must never prevent a Content Creator from generating creator-perspective content about it.
- `RawTrendSignal` has a real DB unique constraint (`platform` + `external_id`). `Trend` dedup is application-level only (`dedup_key` is indexed, not unique) — a known soft spot under high concurrency, narrowed but not eliminated by `transaction.atomic()`.
- `seed_platforms` is idempotent and RSS-only by product decision (2026-08-11). It actively deactivates legacy Reddit/Google-Trends `Platform` rows left over from earlier phases rather than leaving them silently active — re-running it is always safe.
- The relevance-noise threshold (an audience score of ≥60 to appear in the default trend list) reuses the same `AUDIENCE_RELEVANCE_THRESHOLD` constant already used by the audience filter (`apps/trends/filters.py`) — keep these in sync if the threshold ever changes.
- Customer-facing UI copy must never reference terminal/management commands. This was a real shipped bug (empty states told users to "run seed_platforms") fixed on 2026-08-11 — treat any future instance of this as a bug, not a style choice.

## 8. Deployment

Moved to Railway on 2026-08-12, then moved back to Render on 2026-08-19 after repeated Railway build/deploy failures (invalid `preDeployCommand` schema, a Python 3.13/psycopg2 ABI mismatch, and a pre-deploy step that kept failing without readable logs). `render.yaml` is the single source of truth again — unlike Railway, Render supports a multi-service manifest, so one file defines every service instead of one config file per service.

`render.yaml` defines five services plus a managed Postgres database: `trend-intelligence-backend` (Django web, gunicorn), `trend-intelligence-celery-worker`, `trend-intelligence-celery-beat`, `trend-intelligence-redis`, and `trend-intelligence-frontend` (Next.js). The web service's `startCommand` runs `python manage.py migrate --noinput && python manage.py seed_platforms` before gunicorn boots, on every deploy and restart — both are idempotent, so this requires no manual shell step in production.

Secrets and environment-specific values are marked `sync: false` in the manifest (`ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `CLOUDINARY_*`, `NEXT_PUBLIC_API_URL`) — Render won't set these from the file; they're entered once directly in each service's dashboard. `DATABASE_URL` and `REDIS_URL` are wired automatically via `fromDatabase`/`fromService` references to the other services defined in the same file. `DJANGO_SECRET_KEY` uses `generateValue: true` on the web service (and is read from the dashboard, `sync: false`, on the workers, so all three processes share the same key).

The four Railway-specific config files (`backend/railway.json`, `backend/railway.celery-worker.json`, `backend/railway.celery-beat.json`, `frontend/railway.json`) were deleted as part of this move back — they have no equivalent or purpose under Render.

`render.yaml` has been deleted from the repo root. There is no Docker or container orchestration in this project; keep it that way unless there's a concrete reason to change.

## 9. Environment variables

`backend/.env.example` is the authoritative list. Notable groups:

- Django/DB/Redis: `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, `REDIS_URL`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`.
- AI: `AI_PROVIDER` (`claude` or `openai`), `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`.
- Auth: `GOOGLE_OAUTH_CLIENT_ID`.
- Email: `FRONTEND_URL`, `DEFAULT_FROM_EMAIL`, `EMAIL_*` (production only).
- Media: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.
- Inactive-source keys (optional, unused while RSS-only): `YOUTUBE_API_KEY`, `X_BEARER_TOKEN`, `TIKTOK_RESEARCH_TOKEN`, `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`.

## 10. Testing conventions

- Backend: `python -m pytest apps/<app_name>` per app (or a space-separated list). Style: `flake8 <path>` and `black --check --fast <path>`. Schema drift check: `python manage.py makemigrations --check --dry-run` should report "No changes detected" whenever models are unchanged.
- Frontend: `npx tsc --noEmit` and `npx eslint <dirs>` — often worth splitting eslint across `app`, `components`, `lib`, `features` directories individually if working in a sandboxed shell with a short command timeout.
- In a sandboxed dev environment without a real Postgres install available, tests can run against `DATABASE_URL=sqlite:///test_db.sqlite3` as a verification-only substitute (confirmed safe — no Postgres-specific field types like ArrayField exist in this schema). Real dev and production always use Postgres; never change the actual project configuration to sqlite.

## 11. Known open items / deliberately deferred

- A Google News source adapter was requested once but never built — the conversation moved to other priorities before it started. Not in progress.
- A Reddit adapter exists in code, but Reddit API credentials (`REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET`) were never successfully obtained — repeated captcha/IP-block issues on Reddit's own app-creation page blocked setup. Reddit stays inactive regardless (RSS-only by product decision), so this doesn't currently block anything.
- `GeneratedContent` has no DB-level unique constraint on `(brief, content_type, version)` — versioning relies entirely on application code, not a database safeguard.
- `django-celery-beat` / `django-celery-results` are not installed — changing the Beat schedule requires a code deploy, and Celery task success/failure isn't visible in Django Admin (only inferable via `Platform.last_polled_at` / `Trend.analyzed_at IS NULL`).
- 10 RSS feeds are currently seeded and active in `seed_platforms.py` (TechCrunch main/Startups/Venture, VentureBeat AI, MIT Technology Review, Hacker News front page, TechCabal, Disrupt Africa, Rest of World, African Business). Business Daily Africa and Techpoint Africa were tried and deactivated (`DEACTIVATE_SLUGS`) after live testing showed malformed XML from both feeds. The sandbox dev environment has no outbound network access, so any new candidate feed can only be verified by running `feedparser.parse(url).entries` on Kolamu's own machine, not in-session — confirm before adding to `DEFAULT_PLATFORMS`.

## 12. Working conventions for whoever picks this up next

These are the product owner's standing instructions for this project — apply them by default, not just when reminded:

- Before deleting, overwriting, or renaming any existing file, show what will change and wait for confirmation.
- Never modify files outside the current project folder unless explicitly asked.
- Name new files `YYYY-MM-DD-descriptive-name`.
- For multi-step work: outline the plan first and wait for approval before executing; summarize briefly after each major step.
- At the end of a task, list every file created or modified, with its location.
- Nothing gets committed or pushed without the product owner explicitly saying so — and when he says "push," always provide the actual git commands.
