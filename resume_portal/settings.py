"""
Django settings for the Resume Portal project.

All secrets and connection details come from the .env file at the project root.
"""
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env (if present)
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Core settings
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")

DEBUG = os.environ.get("DEBUG", "0") == "1"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

# Render injects the public hostname (e.g. resume-portal.onrender.com) via this
# env var. Add it automatically so the site never 400s on its own domain.
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Origins allowed to send POST requests over HTTPS (needed for the login/upload
# forms once served over https). Comma-separated, e.g.
# CSRF_TRUSTED_ORIGINS=https://resume-portal.onrender.com
CSRF_TRUSTED_ORIGINS = list(
    dict.fromkeys(
        [
            o.strip()
            for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
            if o.strip()
        ]
        + ([f"https://{RENDER_EXTERNAL_HOSTNAME}"] if RENDER_EXTERNAL_HOSTNAME else [])
    )
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # project apps
    "accounts",
    "portal",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "resume_portal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "resume_portal.wsgi.application"

# ---------------------------------------------------------------------------
# Database (Supabase Postgres). Falls back to SQLite if DATABASE_URL missing.
# ---------------------------------------------------------------------------
_db_url = os.environ.get("DATABASE_URL") or "sqlite:///db.sqlite3"
if _db_url.startswith("sqlite") and not DEBUG:
    # Never silently run production on a throwaway SQLite file (Render disks are
    # ephemeral). Fail loudly instead of losing data.
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("DATABASE_URL must be set to a Postgres URL in production.")

# Supabase's transaction-mode pooler (?pgbouncer=true) does not support
# persistent connections well with Django; use conn_max_age=0 in that case.
_is_pooler = "pooler.supabase.com" in _db_url or "pgbouncer" in _db_url
DB_CONFIG = dj_database_url.parse(_db_url, conn_max_age=0 if _is_pooler else 600)
if DB_CONFIG["ENGINE"] != "django.db.backends.sqlite3":
    # Supabase requires SSL. Keep only connection options psycopg2 understands;
    # strip pooler-specific query params (e.g. ?pgbouncer=true) that would crash
    # psycopg2.connect() with unexpected-keyword errors.
    _PQ_OPTIONS = {
        "sslmode",
        "sslrootcert",
        "sslcert",
        "sslkey",
        "connect_timeout",
        "application_name",
    }
    DB_CONFIG["OPTIONS"] = {
        k: v for k, v in DB_CONFIG.get("OPTIONS", {}).items() if k in _PQ_OPTIONS
    }
    DB_CONFIG["OPTIONS"].setdefault("sslmode", "require")
DATABASES = {"default": DB_CONFIG}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 6},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "portal:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# ---------------------------------------------------------------------------
# i18n / tz
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Production security (active only when DEBUG is off, e.g. on Render)
# ---------------------------------------------------------------------------
if not DEBUG:
    # HTTPS-only hardening applies when served behind a TLS-terminating proxy
    # (Render sets RENDER_EXTERNAL_HOSTNAME) or when explicitly enabled. Local
    # dev with DEBUG=0 over plain HTTP stays functional.
    _behind_proxy = bool(RENDER_EXTERNAL_HOSTNAME)
    _force_https = os.environ.get("SECURE_SSL_REDIRECT", "1" if _behind_proxy else "0") == "1"
    if _behind_proxy:
        # Render terminates TLS at its proxy; tell Django the request is HTTPS.
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    if _force_https:
        SECURE_SSL_REDIRECT = True
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # HTTP Strict Transport Security (enable once HTTPS works end-to-end).
    # HSTS Preload is only valid at >= 1 year and is an irreversible commitment.
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
    if SECURE_HSTS_SECONDS and _behind_proxy:
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        if SECURE_HSTS_SECONDS >= 31536000:
            SECURE_HSTS_PRELOAD = True

# ---------------------------------------------------------------------------
# Supabase (storage)
# ---------------------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_STORAGE_BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "resumes")

# Resume storage uses Supabase Storage when a real service-role key is
# configured; otherwise files are stored on the local server (MEDIA_ROOT).
SUPABASE_STORAGE_ENABLED = bool(SUPABASE_SERVICE_ROLE_KEY) and (
    SUPABASE_SERVICE_ROLE_KEY != "service-role-placeholder"
)

# Maximum resume file size in MB
MAX_RESUME_SIZE_MB = 1
