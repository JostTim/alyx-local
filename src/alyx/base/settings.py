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


# # Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# try:
#     from .settings_secret import *  # type: ignore
# except ImportError:
#     # We're probably autobuilding some documentation so let's just import something
#     # to keep Django happy...
#     from .settings_secret_template import *
# # Lab-specific settings
# try:
#     from .settings_lab import *  # type: ignore
# except ImportError:
#     from .settings_lab_template import *

DEFAULT_LAB_NAME = "defaultlab"
DEFAULT_PROTOCOL = "1"

AUTH_USER_MODEL = "misc.LabMember"

en_formats.DATETIME_FORMAT = "d/m/Y H:i"
DATE_INPUT_FORMATS = ("%d/%m/%Y",)

# changes by timothe on 28-11-2022 to try to fix "time offset" issues
USE_DEPRECATED_PYTZ = True  # Support for using pytz will be removed in Django 5.0

USE_TZ = True
TIME_ZONE = get_localzone().key  # "Europe/Paris"

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

    def read_db_password(secret_file_path: Path | str):
        with open(secret_file_path) as f:
            return f.read().strip()

    DB_PASSWORD_FILE = Path("/run/secrets/db-secure-password")
    if not DB_PASSWORD_FILE.is_file():
        raise IOError(
            "No 'db-secure-password' file was found. "
            "You should provide one under the path ./docker/postgres/db-secure-password"
        )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "alyx",  # The database name
            "USER": "postgres",  # The database user
            "PASSWORD": read_db_password(DB_PASSWORD_FILE),  # The database password
            "HOST": "db",  # Name of the service defined in docker-compose.yml
            "PORT": "5432",  # The default port for PostgreSQL
        }
    }


# Custom User model with UUID primary key
AUTH_USER_MODEL = "misc.LabMember"

BASE_DIR = Path(__file__).resolve().parent.parent

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
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "simple"},
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
    # UI add-ons
    "markdownx",  # https://github.com/neutronX/django-markdownx
    "jsoneditor",  # https://github.com/nnseva/django-jsoneditor
    "django_admin_listfilter_dropdown",  # https://github.com/mrts/django-admin-list-filter-dropdown
    # alyx-apps
    "alyx.actions",
    "alyx.data",
    "alyx.misc",
    "alyx.experiments",
    "alyx.jobs",
    "alyx.subjects",
    # needs to be last in the list
    "django_cleanup.apps.CleanupConfig",
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
    "alyx.base.base.QueryPrintingMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
)

ROOT_URLCONF = "alyx.base.urls"

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
                # "alyx.base.LoggingFilesystemLoader",
                # "alyx.base.LoggingAppDirectoriesLoader",
            ],
        },
    },
]


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
    "EXCEPTION_HANDLER": "alyx.base.base.rest_filters_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "PAGE_SIZE": 250,
}

# Internationalization
USE_I18N = False
USE_L10N = False

STATIC_URL = "/static/"

# this is where the static assets will be collected to be copied to serving location
STATICFILES_DIRS = (str(BASE_DIR / "static"),)

# this is where the collected static assets will be copied and served
STATIC_ROOT = str(BASE_DIR.parent.absolute() / "uploaded" / "static")


MEDIA_ROOT = str(BASE_DIR.parent.absolute() / "uploaded" / "media")
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

WSGI_APPLICATION = "alyx.base.wsgi.application"


# TODO use config file for that instead of hard coded text
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "157.99.138.172", "haiss-alyx", "haiss-alyx.local"]
