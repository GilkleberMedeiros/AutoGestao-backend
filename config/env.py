"""
This file is used to load environment variables from a .env file preprocessing them.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


class MissingRequiredEnvVarError(Exception):
  pass


# Base project dir. Must be same as config/settings.py
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()


# Debugging
DEBUG = bool(os.environ.get("DEBUG", False))

USE_DEBUG_DB = bool(os.environ.get("USE_DEBUG_DB", DEBUG))
USE_DEBUG_CACHE = bool(os.environ.get("USE_DEBUG_CACHE", DEBUG))
USE_DEBUG_STORAGE = bool(os.environ.get("USE_DEBUG_STORAGE", DEBUG))

TESTING = bool(os.environ.get("TESTING", False))

# Secrets
DJANGO_SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", None)
if DJANGO_SECRET_KEY is None:
  raise MissingRequiredEnvVarError("DJANGO_SECRET_KEY is required.")

# JWT Auth
JWT_PRIVKEY_PATH = os.environ.get("JWT_PRIVKEY_PATH", None)
JWT_PUBKEY_PATH = os.environ.get("JWT_PUBKEY_PATH", None)
if JWT_PRIVKEY_PATH is None or JWT_PUBKEY_PATH is None:
  raise MissingRequiredEnvVarError("JWT_PRIVKEY_PATH and JWT_PUBKEY_PATH are required.")
JWT_ALGO = os.environ.get("JWT_ALGO", "ES256")
JWT_ACCESS_LIFETIME = int(os.environ.get("JWT_ACCESS_LIFETIME", 15))
JWT_REFRESH_LIFETIME = int(os.environ.get("JWT_REFRESH_LIFETIME", 2880))

# Databases
_DEFAULT_DB_NAME = os.environ.get("DEFAULT_DB_NAME", "autogestao")
_DEFAULT_DB_USER = os.environ.get("DEFAULT_DB_USER", None)
_DEFAULT_DB_PASSWORD = os.environ.get("DEFAULT_DB_PASSWORD", None)
if (_DEFAULT_DB_USER is None or _DEFAULT_DB_PASSWORD is None) and not USE_DEBUG_DB:
  raise MissingRequiredEnvVarError(
    "DEFAULT_DB_USER and DEFAULT_DB_PASSWORD are required if USE_DEBUG_DB is False."
  )
_DEFAULT_DB_HOST = os.environ.get("DEFAULT_DB_HOST", "localhost")
_DEFAULT_DB_PORT = os.environ.get("DEFAULT_DB_PORT", "5432")
# Build default database
DEFAULT_DB = {
  "ENGINE": "django.db.backends.postgresql",
  "NAME": _DEFAULT_DB_NAME,
  "USER": _DEFAULT_DB_USER,
  "PASSWORD": _DEFAULT_DB_PASSWORD,
  "HOST": _DEFAULT_DB_HOST,
  "PORT": _DEFAULT_DB_PORT,
}
if USE_DEBUG_DB:
  DEFAULT_DB = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": BASE_DIR / "db.sqlite3",
  }

# Caches
CACHE_URL = os.environ.get("CACHE_URL", "redis://127.0.0.1:6379")
DEFAULT_CACHE = {
  "BACKEND": "django.core.cache.backends.redis.RedisCache",
  "LOCATION": CACHE_URL,
}
if USE_DEBUG_CACHE:
  DEFAULT_CACHE = {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "unique-snowflake",
  }

# Object Storages
AWS_STORAGE_BUCKET_NAME = os.environ.get(
  "AWS_STORAGE_BUCKET_NAME", "autogestao-storage"
)
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", None)
if AWS_S3_REGION_NAME is None and not USE_DEBUG_STORAGE:
  raise MissingRequiredEnvVarError("AWS_S3_REGION_NAME is required.")

DEFAULT_STORAGE_BACKEND = "storages.backends.s3boto3.S3Boto3Storage"
if USE_DEBUG_STORAGE:
  DEFAULT_STORAGE_BACKEND = "django.core.files.storage.FileSystemStorage"

# AWS Keys
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
if (
  AWS_ACCESS_KEY_ID is None or AWS_SECRET_ACCESS_KEY is None
) and not USE_DEBUG_STORAGE:
  raise MissingRequiredEnvVarError(
    "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required."
  )

# Email
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", None)
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", None)
if EMAIL_HOST_USER is None or EMAIL_HOST_PASSWORD is None:
  raise MissingRequiredEnvVarError(
    "EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are required."
  )
EMAIL_USE_TLS = bool(os.environ.get("EMAIL_USE_TLS", True))
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", None)
if DEFAULT_FROM_EMAIL is None:
  DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
