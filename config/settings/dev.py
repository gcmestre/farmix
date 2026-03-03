from .base import *  # noqa: F401, F403

DEBUG = True

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),  # noqa: F405
}

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Use plain static storage in dev
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
