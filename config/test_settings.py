import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-key-not-for-deployment")

from .settings import *  # noqa: F403


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
