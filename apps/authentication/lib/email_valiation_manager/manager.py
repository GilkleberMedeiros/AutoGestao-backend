from django.http import HttpRequest
from django.core.cache import caches
from django.template.loader import render_to_string
from django.utils.timezone import get_current_timezone

from uuid import uuid4
from datetime import datetime, timedelta

from config import settings
from apps.users.models import User
from apps.core.exceptions import ExternalServiceError


class EmailValidationManager:
  """
  Manage Email Validation process.
  Send validation email to user email and validate it.
  Stores validation tokens in cache db.
  """

  cache_db = caches["default"]
  validation_template = settings.EMAIL_VALIDATION_TEMPLATE
  validation_from_email = settings.DEFAULT_FROM_EMAIL
  validation_token_lifetime = settings.EMAIL_VALIDATION_TOKEN_LIFETIME

  @classmethod
  def send_validation_email(
    cls,
    request: HttpRequest,
    user: User,
    *,
    subject: str = "Validação de Email - App AutoGestão",
    validation_template: str = None,
    from_email: str = None,
  ) -> str:
    """
    Send validation email to user email.
    """
    token = cls._generate_token()
    formatted_token = cls._set_token(user.id, token)

    if not validation_template:
      validation_template = cls.validation_template
    if not from_email:
      from_email = cls.validation_from_email

    try:
      user.email_user(
        subject,
        render_to_string(
          validation_template,
          {
            "validation_token": token,
            "validation_token_timeout": cls.validation_token_lifetime.total_seconds()
            / 60,
          },
        ),
        from_email=from_email,
        fail_silently=False,
      )
    except Exception:
      cls.delete_token(formatted_token)  # delete token if email fails
      raise ExternalServiceError("Failed to send validation email.")

    return token

  @staticmethod
  def format_token(token: str) -> str:
    """
    Format token to be used as key in cache."""
    return f"email-validation-{token}"

  @staticmethod
  def _generate_token():
    """
    Generate a token for email validation.
    """
    token = str(uuid4())
    return token

  @classmethod
  def _set_token(cls, user_id: str, token: str, timeout: int = None):
    """
    Set token in cache db.
    receives user_id, token and timeout(in seconds) as parameters.
    """
    token = cls.format_token(token)
    tz = get_current_timezone()
    timeout = timeout or cls.validation_token_lifetime.total_seconds()
    cls.cache_db.set(
      token,
      {"user_id": user_id, "invalid_at": datetime.now(tz) + timedelta(seconds=timeout)},
      timeout=timeout,
    )
    return token

  @classmethod
  def get_validation_data(cls, token: str) -> dict | None:
    return cls.cache_db.get(cls.format_token(token), None)

  @classmethod
  def _validate_token(cls, user_id: str, token: str):
    data = cls.get_validation_data(token)
    if not data:
      return False
    if data["invalid_at"] < datetime.now(get_current_timezone()):
      return False
    if data["user_id"] != user_id:
      return False
    return True

  @classmethod
  def validate_user_email(cls, user: User, token: str) -> bool:
    if not cls._validate_token(user.id, token):
      return False

    try:
      user.validate_email()
    except Exception:
      raise ExternalServiceError("Failed to save validation status.")

    try:
      cls.delete_token(token)
    except Exception:
      return True

    return True

  @classmethod
  def delete_token(cls, token: str):
    cls.cache_db.delete(cls.format_token(token))
