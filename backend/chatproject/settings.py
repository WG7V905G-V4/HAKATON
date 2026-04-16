import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIR   = BASE_DIR.parent / "ui"

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-key")
DEBUG      = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "chat",
    "ui_bridge",   # ← новое приложение-мост
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    # CsrfViewMiddleware убрана для совместимости с ui/*.py логикой
    # (signup/hobbies/etc. не передают csrf-токен)
    # Если нужна CSRF-защита на chat/ — включи обратно и добавь @csrf_exempt только там
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "chatproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [UI_DIR],          # HTML-файлы берём из ui/
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "chatproject.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME":   BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en"
TIME_ZONE     = "Europe/Moscow"
USE_I18N      = True
USE_TZ        = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [UI_DIR]   # CSS / JS / картинки из ui/

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

HF_API_KEY = os.getenv("HF_API_KEY", "")
HF_MODEL   = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")