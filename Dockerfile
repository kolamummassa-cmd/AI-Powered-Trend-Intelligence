# Single-container deployment: Django (gunicorn) + Celery worker + Celery
# beat + Next.js frontend, fronted by nginx on one public port. Built this
# way specifically to run as ONE Render service instead of five, per an
# explicit product-owner decision (2026-08-19) to minimize the number of
# paid/managed services. See docker/ and Procfile for how the pieces fit
# together; render.yaml just points at this Dockerfile.

FROM python:3.12-slim

ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    NEXT_PUBLIC_API_URL=/api/v1 \
    NEXT_PUBLIC_GOOGLE_CLIENT_ID=${NEXT_PUBLIC_GOOGLE_CLIENT_ID}

# nginx: reverse proxy in front of both apps.
# gettext-base: provides envsubst, used to inject Render's $PORT into the
#   nginx config at container start (nginx config files can't read env
#   vars directly).
# build-essential/libpq-dev: psycopg2-binary occasionally needs to compile
#   against libpq depending on the exact base image/arch.
# nodejs: installed from NodeSource since Debian's default apt repo version
#   is too old for Next.js 16.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        nginx \
        gettext-base \
        build-essential \
        libpq-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir honcho

WORKDIR /app

# --- Backend dependencies (cached separately from app code) ---
COPY backend/requirements/ backend/requirements/
RUN pip install --no-cache-dir -r backend/requirements/prod.txt

# --- Frontend dependencies (cached separately from app code) ---
COPY frontend/package.json frontend/package-lock.json frontend/
RUN cd frontend && npm ci

# --- Application code ---
COPY backend/ backend/
COPY frontend/ frontend/

# Bakes public browser configuration into the client bundle. The API is on
# the same origin, while Google's public OAuth client ID lets the login pages
# render the Google Identity Services button.
RUN cd frontend && npm run build

# --- nginx + process orchestration ---
COPY docker/nginx.conf.template /etc/nginx/nginx.conf.template
COPY Procfile /app/Procfile
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8080
CMD ["/app/start.sh"]
