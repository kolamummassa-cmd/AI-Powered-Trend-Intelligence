# Run by honcho (see docker/start.sh) inside the single container.
# honcho's default behavior: if any one of these exits, it stops all the
# others and exits too — so Render's restart policy restarts the whole
# container rather than leaving a half-dead set of processes running.
proxy: nginx -g "daemon off;"
web: sh -c "cd /app/backend && gunicorn config.wsgi:application --bind 127.0.0.1:8000"
frontend: sh -c "cd /app/frontend && npm run start -- -p 3000"
worker: sh -c "cd /app/backend && celery -A config worker -l info"
beat: sh -c "cd /app/backend && celery -A config beat -l info"
