# AI-Powered Trend Intelligence — Architecture Review & Implementation Roadmap

**Prepared for:** Kolamu / Foluxnova
**Date:** 2026-08-06
**Status:** Pre-implementation review — awaiting approval before any code is written

---

## 1. Current State

The project folder is empty. This is a greenfield build — there is no existing codebase to review, migrate, or refactor. Every decision below is a proposal, not a description of something already in place.

Given the pitch date of August 28 (22 days from today), the honest engineering read is this: everything in the spec is achievable as *real, production-grade* code — but not all of it can be *built* in 22 days to production maturity. What's achievable is standing up the correct architecture now so that every feature added afterward slots in cleanly, and delivering the core workflow (trend → analysis → generated content) as genuinely production-quality software rather than a shortcut. Breadth (8 monitoring platforms, full notification system, full analytics suite) will need to be sequenced rather than built simultaneously. This is addressed directly in Section 6.

---

## 2. Architectural Principles

- **Feature-based clean architecture** on both sides of the stack. No business logic in UI components, no business logic in Django views/serializers directly — logic lives in a service layer, views/components are thin.
- **Provider-agnostic AI layer.** OpenAI and Claude sit behind a common interface (`AIProvider`) so a provider swap is a config change, not a rewrite.
- **Adapter pattern for trend monitoring.** Each platform (TikTok, Reddit, Google Trends, etc.) implements a common `TrendSource` interface. Adding a platform means writing one adapter, not touching the pipeline.
- **Everything async that can be async.** Trend collection, AI analysis, and content generation are Celery tasks, not request-blocking calls. The API returns fast; work happens in the background with status polling/websocket updates.
- **Soft deletes and audit fields everywhere.** No hard deletes on user-generated or business data. Every model tracks `created_at`, `updated_at`, `created_by` where relevant, `deleted_at` for soft delete.

---

## 3. Repository Structure

```
ai-trend-intelligence/
├── backend/
│   ├── config/                    # Django settings (base/dev/prod split), celery.py, urls.py
│   ├── apps/
│   │   ├── accounts/               # auth, users, profile, sessions
│   │   ├── trends/                 # trend models, ingestion orchestration
│   │   ├── trend_sources/          # platform adapters (modular, one module per platform)
│   │   ├── trend_analysis/         # scoring, AI trend understanding
│   │   ├── content_studio/         # content brief, hooks, scripts, remix templates
│   │   ai_chat/                    # conversational content refinement
│   │   ├── notifications/          # in-app + email notification engine
│   │   ├── analytics/              # usage & platform analytics
│   │   └── core/                   # shared utilities, base models, permissions, pagination
│   ├── ai_providers/                # AIProvider interface + OpenAIProvider + ClaudeProvider
│   ├── tests/
│   ├── Dockerfile
│   └── requirements/
├── frontend/
│   ├── app/                        # Next.js App Router
│   │   ├── (auth)/                 # login, register, verify, reset
│   │   ├── (dashboard)/             # dashboard, trends, content studio, analytics, settings
│   ├── features/                   # feature-based modules (trends, content-studio, auth, notifications)
│   │   ├── trends/
│   │   │   ├── api/                 # React Query hooks, Axios calls
│   │   │   ├── components/
│   │   │   ├── types/
│   │   │   └── utils/
│   │   └── content-studio/ ...
│   ├── components/ui/               # shadcn/ui primitives, shared design system
│   ├── lib/                         # axios instance, query client, auth helpers
│   └── Dockerfile
├── docker-compose.yml               # local dev: postgres, redis, backend, celery worker, celery beat, frontend
├── .github/workflows/                # CI: lint, test, build, deploy to Render
└── docs/                             # architecture decision records, this roadmap
```

This structure is what makes "implement one feature at a time" actually work — each feature app is isolated, testable, and reviewable on its own.

---

## 4. Core Domain Model (PostgreSQL)

All tables include `id (UUID)`, `created_at`, `updated_at`, `deleted_at` (soft delete) unless noted. Indexes noted are beyond the automatic PK/FK indexes.

**accounts**
- `User` — email, password_hash, auth_provider (email/google), is_verified, timezone
- `UserProfile` — display_name, avatar_url (Cloudinary), role, preferences (jsonb)
- `RefreshToken` / session tracking for JWT rotation and revocation

**trend_sources**
- `Platform` — name, slug, adapter_key, is_active (drives which adapters run)
- `RawTrendSignal` — raw ingested payload before analysis, source platform, external_id, fetched_at (indexed on `platform_id, fetched_at` for dedup/query)

**trends**
- `Trend` — title, category_id, summary, why_spreading, estimated_lifespan, status (active/expiring/expired), first_detected_at
  - Index on `(status, trend_score DESC)` for dashboard "active/high-value" queries
  - Index on `first_detected_at` for "new today" queries
- `TrendSourceLink` — M2M between Trend and Platform (a trend can span multiple platforms), with source URL
- `Category` — normalized lookup table, not a free-text field

**trend_analysis**
- `TrendAnalysis` — trend_id (1:1 or versioned 1:many), business_relevance, founder_relevance, entrepreneurship_relevance, ai_relevance, trend_score, opportunity_score, confidence_score, ai_explanation, model_used, prompt_version
  - Versioned so re-analysis doesn't destroy history — useful for both product iteration and defensibility of scores in the pitch

**content_studio**
- `ContentBrief` — trend_id, business_angle, founder_angle, educational_angle, marketing_angle, talking_points (jsonb)
- `GeneratedContent` — brief_id, content_type (hook/script_30/script_60/cta/hashtags/thumbnail_suggestion/remix_template), body, version, is_saved
  - Index on `(user_id, is_saved)` for "saved content" dashboard widget
- `AIChatMessage` — content_id, role (user/assistant), message, created_at — powers the AI Chat refinement thread per generated piece

**notifications**
- `Notification` — user_id, type (new_high_value_trend/expiring_trend/generation_complete), payload (jsonb), read_at
  - Index on `(user_id, read_at)` for unread-count queries

**analytics**
- `UsageEvent` — user_id, event_type, metadata (jsonb), occurred_at — append-only event log that both the Analytics screen and future BI work read from, rather than computing everything live from operational tables

Rationale for this shape: analysis and content are separated from raw trend data and versioned, so the AI pipeline can be re-run, improved, or A/B tested without ever losing what a user has already seen or saved. This matters a lot at pitch time — you can show score history and explain *why* a number changed.

---

## 5. AI & Trend Engine Design

**AI Provider Layer** (`backend/ai_providers/`)
```
AIProvider (interface)
 ├── generate_trend_analysis(raw_signal) -> TrendAnalysisResult
 ├── generate_content_brief(trend) -> ContentBrief
 ├── generate_script(brief, duration, tone) -> str
 └── chat_refine(content, instruction, history) -> str

OpenAIProvider(AIProvider)
ClaudeProvider(AIProvider)
```
Provider selection is a settings/env value (`AI_PROVIDER=openai|claude`) with per-call override allowed, so different pipeline stages can use different providers if one is stronger at a given task (e.g., Claude for long-form scripts, GPT for fast hook variations) without hardcoding that decision into business logic.

**Trend Source Adapters** (`backend/apps/trend_sources/`)
Each adapter implements `fetch_signals() -> list[RawTrendSignal]` and is registered in a source registry. Celery Beat schedules a per-platform polling task. Google Trends, RSS, and Reddit have straightforward, stable APIs and should be built first. TikTok, Instagram Reels, YouTube Shorts, and X have stricter API access/cost constraints — the roadmap sequences these after the pipeline is proven on the easier sources, using officially supported APIs only (no scraping that violates ToS, which is a real legal/production risk to flag directly for a platform you're pitching).

**Pipeline**
`RawTrendSignal` → dedup/normalize → `Trend` created/updated → Celery task calls AI provider for scoring → `TrendAnalysis` written → threshold check → `Notification` fired if high-value → user-triggered `ContentBrief` + script generation (also async, with status polling from the frontend so the UI can show progress rather than blocking).

---

## 6. Phased Roadmap (one feature at a time, in build order)

This order is deliberate: each phase produces something demonstrable, and nothing later depends on something not yet built.

**Phase 0 — Foundation (infrastructure, no user-facing feature yet)**
Repo scaffold, Docker Compose (Postgres, Redis, backend, worker, beat, frontend), Django project with settings split, CI pipeline skeleton (lint + test on PR), base models (soft delete, audit mixin), health check endpoint.

**Phase 1 — Authentication**
Email registration, verification, login, password reset, Google OAuth, JWT issuance/refresh/rotation, profile + account settings. This unlocks every other feature and is the highest-leverage thing to get right early (security-sensitive, hard to retrofit).

**Phase 2 — Trend Engine (ingestion + storage, no AI yet)**
Platform/Category models, adapter interface, Google Trends + RSS + Reddit adapters (lowest friction, official APIs), Celery Beat polling, raw signal storage, dedup logic, trend list API with pagination/filtering.

**Phase 3 — AI Trend Analysis**
AI provider abstraction, OpenAI + Claude implementations, trend scoring pipeline, `TrendAnalysis` model, trend detail page (backend + frontend), confidence/opportunity/trend score display.

**Phase 4 — Dashboard**
Aggregate stat endpoints (total/active/new-today trends, platform distribution), dashboard UI with skeleton loading and empty states, search and filters.

**Phase 5 — AI Content Studio**
Content brief generation, hooks, 30s/60s scripts, CTA, hashtags, thumbnail suggestion, remix template — the core "publishable content" deliverable and the product's central value proposition.

**Phase 6 — AI Chat (content refinement)**
Threaded refinement per generated content piece, platform-conversion actions (LinkedIn/Twitter thread/Carousel/Shorts).

**Phase 7 — Notifications**
High-value trend alerts, expiring-trend alerts, generation-complete alerts — in-app first, email via existing infra second.

**Phase 8 — Analytics**
Usage event logging (should actually start being recorded from Phase 1 onward, even before the screen exists), analytics dashboard.

**Phase 9 — Remaining trend sources**
TikTok, Instagram Reels, YouTube Shorts, X — added as adapters onto the already-proven pipeline, gated by whichever official API access is secured first.

**Phase 10 — Hardening**
Rate limiting, caching layer tuning, query optimization pass, load testing, security review, deployment pipeline to Render via GitHub Actions.

Each phase, when built, will come with: what was built, why, files changed, how it works, and what's next — per your process. Nothing proceeds to the next phase without your sign-off.

---

## 7. Direct Recommendations (things worth deciding now, not mid-build)

1. **Pick a launch AI provider now** (OpenAI or Claude as primary, the other as fallback/comparison) so Phase 3 isn't blocked on indecision. Both are wired via the abstraction either way, so this is low-risk to change later.
2. **TikTok/Instagram/YouTube official API access can take time to approve.** If the pitch depends on visibly monitoring those platforms, start that access request process today, in parallel with Phase 0–2 engineering — it's the one dependency that isn't on our own timeline.
3. **Scope the pitch narrative around Phases 0–5.** That's the full "trend detected → publishable content" loop working end-to-end on real, sanctioned data sources (Google Trends, RSS, Reddit) — that is the product's core claim, and it's achievable at real production quality in this window. Phases 6–10 strengthen the story but aren't what makes the core loop true.

---

## 8. Approval Checkpoint

No code has been written. Please confirm:
- The repository structure and domain model in Sections 3–4
- The build order in Section 6
- The AI provider decision in Section 7.1
- Whether the Phase 9 platforms (TikTok/IG/YouTube/X) need API access requests started today

Once approved, Phase 0 begins.
