# Hostinger VPS deployment

This application runs as four Docker services on the VPS: the application,
PostgreSQL, Redis, and Caddy. Caddy provides HTTPS and passes requests to the
application's existing internal Nginx server.

## First deployment

1. Clone the repository on the VPS.
2. Copy `.env.production.example` to `.env` and add real secrets locally on
   the VPS. Never commit `.env` or paste it into chat.
3. Point the domain's `@` and `www` DNS records at the VPS before starting
   Caddy so it can issue HTTPS certificates.
4. Run `docker compose up -d --build`.
5. Confirm it is healthy with `docker compose ps` and
   `docker compose logs --tail=100 app`.

## Data and recovery

The PostgreSQL, Redis, uploaded media, static files, and Caddy certificates
are Docker volumes. Do not remove these volumes during ordinary redeployments.
Export the existing Render PostgreSQL database before its expiry, restore it
into the `postgres` container, then verify the application before shutting
down Render.

## Updating

```bash
git pull --ff-only
docker compose up -d --build
docker compose run --rm app python backend/manage.py migrate
```

Inspect a service without exposing secrets:

```bash
docker compose ps
docker compose logs --tail=100 app
```

## Google sign-in and password resets

Password resets are already enabled. They use the same Resend sender as email
verification, so keep `RESEND_API_KEY`, `DEFAULT_FROM_EMAIL`, and
`FRONTEND_URL=https://trendjackhunter.tech` set in the VPS `.env`.

To enable Google sign-in, create a **Web application** OAuth client in Google
Cloud and add these Authorized JavaScript origins:

- `https://trendjackhunter.tech`
- `https://www.trendjackhunter.tech`

Copy its client ID into `GOOGLE_OAUTH_CLIENT_ID` in the VPS `.env`, then
rebuild the app so Next.js can include the public button configuration:

```bash
docker compose up -d --build app
```

The client ID is safe to place in `.env`; do not add a Google client secret to
the application or share any account credentials.
