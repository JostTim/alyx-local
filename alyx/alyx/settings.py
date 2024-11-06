"""
Django settings for alyx project.

For more information on this file, see
https://docs.djangoproject.com/en/stable/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/stable/ref/settings/
"""

import os
from pathlib import Path
import structlog
from django.conf.locale.en import formats as en_formats
from tzlocal import get_localzone


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
try:
    from .settings_secret import *  # noqa
except ImportError:
    # We're probably autobuilding some documentation so let's just import something
    # to keep Django happy...
    from .settings_secret_template import *  # noqa

# Lab-specific settings
try:
    from .settings_lab import *  # noqa
except ImportError:
    from .settings_lab_template import *  # noqa


def read_db_password(secret_file_path: Path | str):
    with open(secret_file_path) as f:
        return f.read().strip()


en_formats.DATETIME_FORMAT = "d/m/Y H:i"
DATE_INPUT_FORMATS = ("%d/%m/%Y",)
# changes by timothe on 28-11-2022 to try to fix "time offset" issues
USE_DEPRECATED_PYTZ = True  # Support for using pytz will be removed in Django 5.0

IS_DOCKER = os.path.exists("/.dockerenv")

if "GITHUB_ACTIONS" in os.environ:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "githubactions",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "HOST": "localhost",
            "PORT": "5432",
        }
    }
elif IS_DOCKER:
    # settings.py
    DB_PASSWORD_FILE = Path("/run/secrets/db-root-password")
    DB_PASSWORD = read_db_password(DB_PASSWORD_FILE) if DB_PASSWORD_FILE.is_file() else "default_password"
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "alyx",  # Your database name
            "USER": "postgres",  # Your database user
            "PASSWORD": DB_PASSWORD,  # Your database password
            "HOST": "db",  # Name of the service defined in docker-compose.yml
            "PORT": "5432",  # The default port for PostgreSQL
        }
    }


# Custom User model with UUID primary key
AUTH_USER_MODEL = "misc.LabMember"

BASE_DIR = Path(__file__).resolve().parent.parent

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(asctime)s [%(levelname)s] " + "{%(filename)s:%(lineno)s} %(message)s",
            "datefmt": "%d/%m %H:%M:%S",
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        },
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
    },
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/uploaded/log/alyx_db.log",
            "maxBytes": 16777216,
            "backupCount": 5,
            "formatter": "simple",
        },
        "console": {"level": "WARNING", "class": "logging.StreamHandler", "formatter": "simple"},
        "json_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/uploaded/log/alyx_db_json.log",
            "maxBytes": 16777216,
            "backupCount": 5,
            "formatter": "json_formatter",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": True,
        },
        "django_structlog": {
            "handlers": ["json_file"],
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": "WARNING",
        "propagate": True,
    },
}

if "TRAVIS" in os.environ or "READTHEDOCS" in os.environ:
    LOGGING["handlers"]["file"]["filename"] = "alyx.log"


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# Production settings. Used mainly for SSL security. As we go local, i deactiated them.
# There is still authentification, but "risk" for man in the middle attack
# (only, the middle man have to be IN pasteur's private network so it's much less likely and data is backuped regularly.
if not DEBUG:
    pass
    # #EDITED BY TIMOTHE ON 22/11/2022 TO BE ABLE TO CONNECT WITH HTTP.
    # CSRF_COOKIE_SECURE = False #previous value was True

    # X_FRAME_OPTIONS = 'DENY'
    # SESSION_COOKIE_SECURE = True
    # #EDITED BY TIMOTHE ON 22/11/2022 TO BE ABLE TO CONNECT WITH HTTP.
    # SECURE_SSL_REDIRECT = False #previous value was True
    # SECURE_BROWSER_XSS_FILTER = True
    # SECURE_CONTENT_TYPE_NOSNIFF = True
    # SECURE_HSTS_SECONDS = 30
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True

# Application definition

INSTALLED_APPS = (
    # 'dal',
    # 'dal_select2',
    # 'viewflow', #https://github.com/viewflow/viewflow
    # 'viewflow.workflow', may be interesting. Dropped it for now
    # 'material', #https://github.com/kmmbvnr/django-material
    # 'material.admin', Decided to remove it because it is less clear than the original theme
    # 'martor', #https://github.com/agusmakmun/django-markdown-editor #removed, not for admin page but for custom forms.
    # 'mdeditor', #https://pypi.org/project/django-mdeditor-widget/ # removed, simply doesn't work
    "markdownx",  # https://github.com/neutronX/django-markdownx
    "jsoneditor",  # https://github.com/nnseva/django-jsoneditor
    "django_admin_listfilter_dropdown",  # https://github.com/mrts/django-admin-list-filter-dropdown
    "django_filters",
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "mptt",
    "polymorphic",
    "rangefilter",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_docs",
    "reversion",
    "test_without_migrations",
    # alyx-apps
    "actions",
    "data",
    "misc",
    "experiments",
    "jobs",
    "subjects",
    "django_cleanup.apps.CleanupConfig",  # needs to be last in the list
)

JSON_EDITOR_JS = "https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/9.10.2/jsoneditor.js"
JSON_EDITOR_CSS = "https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/9.10.2/jsoneditor.css"

MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "alyx.base.QueryPrintingMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
)

ROOT_URLCONF = "alyx.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR / "templates")],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                # "django.template.loaders.cached.Loader",
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
                "alyx.base.LoggingFilesystemLoader",
                "alyx.base.LoggingAppDirectoriesLoader",
            ],
        },
    },
]


WSGI_APPLICATION = "alyx.wsgi.application"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "STRICT_JSON": False,
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    # 'DEFAULT_RENDERER_CLASSES': (
    #     'rest_framework.renderers.JSONRenderer',
    # ),
    "EXCEPTION_HANDLER": "alyx.base.rest_filters_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "PAGE_SIZE": 250,
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/


USE_I18N = False
USE_L10N = False
# ADDED BY TIMOTHE ON 28-11-2022 to avoid time issues :
# USE_TZ was previously at False and TIME_ZONE variable did not exist
USE_TZ = True
TIME_ZONE = get_localzone().key  # "Europe/Paris"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

# this is where the collected static assets will be copied
STATIC_ROOT = str(BASE_DIR.parent.absolute() / "uploaded" / "static")
STATIC_URL = "/static/"

STATICFILES_DIRS = (
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # this is from where we collect static assets
    str(BASE_DIR / "static"),
)

MEDIA_ROOT = str(BASE_DIR.parent / "uploaded" / "media")
# MEDIA_ROOT = "/backups/uploaded/"
MEDIA_URL = "/media/"

# The location for saving and/or serving the cache tables.
# May be a local path, http address or s3 uri (i.e. s3://)
TABLES_ROOT = str(BASE_DIR / "uploaded" / "tables/")

UPLOADED_IMAGE_WIDTH = 800

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# ADDED BY TIMOTHE ON 13/04/2023 TO CONNECT FROM VARIOUS LOCATIONS IN THE LAB
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "157.99.138.172", "haiss-alyx", "haiss-alyx.local"]
