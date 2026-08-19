# Run by honcho (see docker/start.sh) inside the single container.
# honcho's default behavior: if any one of these exits, it stops all the
# others and exits too — so Render's restart policy restarts the whole
# container rather than leaving a half-dead set of processes running.
#
# worker+beat are combined into one embedded-beat process (`--beat` flag)
# instead of two separate `celery worker` / `celery beat` processes —
# added 2026-08-19 after the free Render instance (512MB RAM) ran out of
# memory running 5 separate processes. Embedded beat is single-threaded
# and slightly less crash-isolated than a dedicated beat process, but for
# our scale (one periodic schedule, no high-volume tasks) that's a fine
# trade for cutting out a whole extra Python/Django process.
proxy: nginx -g "daemon off;"
web: sh -c "cd /app/backend && gunicorn config.wsgi:application --bind 127.0.0.1:8000"
# --max-old-space-size caps Node's V8 heap so it garbage-collects more
# aggressively instead of growing to fill available memory — a small,
# free way to shave peak RSS in a 512MB container. Full static export
# (removing the Node process entirely) was considered and ruled out:
# trends/[slug] and content/[id] are genuinely dynamic — new slugs/ids
# get created at runtime by users, so they can't be pre-generated at
# build time the way static export requires.
frontend: sh -c "cd /app/frontend && NODE_OPTIONS='--max-old-space-size=128' npm run start -- -p 3000"
# --pool=solo runs tasks in the single main process instead of Celery's
# default prefork pool, which forks a child worker process per unit of
# concurrency (concurrency itself defaults to the HOST's full CPU count,
# not Render's fractional 0.1-CPU grant on the free tier — so left
# unset, this could silently fork several extra full-memory Python
# processes). solo is single-threaded, but that's fine for our current
# task volume and worth it for the memory it saves in a 512MB container.
worker: sh -c "cd /app/backend && celery -A config worker --beat --pool=solo -l info"
