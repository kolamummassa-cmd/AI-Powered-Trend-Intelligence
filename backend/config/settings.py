# DEPRECATED — do not use.
#
# Settings now live in config/settings/ as a package (base.py, dev.py,
# prod.py) so environment-specific configuration is explicit rather than
# hidden behind a single DEBUG flag. This file is kept only because the
# sandbox filesystem would not allow deleting it; it is never imported —
# manage.py, wsgi.py, asgi.py and celery.py all point at
# 'config.settings.dev' or 'config.settings.prod' directly. Safe to
# delete manually once this repo is on your own machine/CI.
raise ImportError(
    "config.settings is deprecated. Use config.settings.dev or "
    "config.settings.prod instead."
)
