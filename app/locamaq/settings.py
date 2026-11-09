"""Configuração do sistema de gestão LocaMaq.

Dois modos:
- Desenvolvimento (padrão no PC): DEBUG ligado, banco em app/db.sqlite3.
- Produção (LOCAMAQ_PRODUCAO=1, no servidor): exige LOCAMAQ_SECRET_KEY e LOCAMAQ_HOSTS,
  liga cookies seguros e aceita rodar sob um prefixo (LOCAMAQ_PREFIXO=/crm).
Nenhum segredo fica neste arquivo.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent

PRODUCAO = os.environ.get("LOCAMAQ_PRODUCAO") == "1"
DEBUG = not PRODUCAO

if PRODUCAO:
    SECRET_KEY = os.environ["LOCAMAQ_SECRET_KEY"]
    ALLOWED_HOSTS = [h.strip() for h in os.environ["LOCAMAQ_HOSTS"].split(",") if h.strip()]
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
else:
    # Chave só para o PC. Em produção a chave vem da variável de ambiente.
    SECRET_KEY = "dev-inseguro-locamaq-nao-usar-em-producao"
    ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
    # No PC, deixa a própria origem abrir o sistema num quadro (teste de largura de celular).
    X_FRAME_OPTIONS = "SAMEORIGIN"

PREFIXO = os.environ.get("LOCAMAQ_PREFIXO", "").rstrip("/")
if PREFIXO:
    FORCE_SCRIPT_NAME = PREFIXO
    SESSION_COOKIE_PATH = PREFIXO + "/"
    CSRF_COOKIE_PATH = PREFIXO + "/"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "crm",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Todo o sistema exige login; as exceções (login, API do n8n) estão marcadas nas views.
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "locamaq.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "crm.context_processors.navegacao",
            ],
        },
    },
]

WSGI_APPLICATION = "locamaq.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("LOCAMAQ_DB", str(BASE_DIR / "db.sqlite3")),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = f"{PREFIXO}/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if PRODUCAO
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "crm:inicio"
LOGOUT_REDIRECT_URL = "login"

# Pasta com os CSVs da base fictícia (importados pelo comando importar_base).
LOCAMAQ_DADOS = Path(os.environ.get("LOCAMAQ_DADOS", REPO_DIR / "data" / "processed"))

# Entrada de leads (POST /api/leads/), de duas formas:
# - LOCAMAQ_API_TOKEN: exige "Authorization: Bearer <chave>";
# - LOCAMAQ_API_REDE_INTERNA=1: aceita só chamadas diretas da rede interna do Docker (o n8n no
#   mesmo servidor), sem passar pelo proxy. O proxy bloqueia /crm/api/ para quem vem de fora.
# Sem nenhuma das duas, a API fica desligada.
LOCAMAQ_API_TOKEN = os.environ.get("LOCAMAQ_API_TOKEN", "")
LOCAMAQ_API_REDE_INTERNA = os.environ.get("LOCAMAQ_API_REDE_INTERNA") == "1"

# Último número de lead já usado fora do sistema (planilha/n8n). O próximo lead criado aqui
# nunca recebe número menor ou igual a este. Ex.: 75 -> próximo LEAD_0076/aa.
LOCAMAQ_LEAD_PISO = int(os.environ.get("LOCAMAQ_LEAD_PISO", "0") or 0)

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO" if PRODUCAO else "WARNING"},
}
