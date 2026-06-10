from django.core.cache import caches
from django.template.loader import render_to_string
from django.utils.timezone import get_current_timezone

from uuid import uuid4
from datetime import datetime, timedelta

from config import settings
from apps.users.models import User
from apps.core.exceptions import ExternalServiceError


class PhoneValidationService:
  """
  Manage Phone Validation process.
  Send validation sms to user phone and validate it.
  Stores validation tokens in cache db.
  """

  cache_db = caches["default"]
  validation_template = settings.PHONE_VALIDATION_SMS_TEMPLATE
  validation_from_sms = settings.DEFAULT_FROM_SMS
  validation_token_lifetime = settings.PHONE_VALIDATION_TOKEN_LIFETIME

  @classmethod
  def send_validation_sms(
    cls,
    user: User,
    *,
    validation_template: str = None,
    from_sms: str = None,
  ) -> str:
    """
    Send validation sms to user phone.
    """
    token = cls._generate_token()
    formatted_token = cls._set_token(user.id, token)

    if not validation_template:
      validation_template = cls.validation_template
    if not from_sms:
      from_sms = cls.validation_from_sms

    try:
      user.sms_user(
        render_to_string(
          validation_template,
          {
            "validation_token": token,
            "validation_token_timeout": int(
              cls.validation_token_lifetime.total_seconds() / 60
            ),
          },
        ),
        from_sms=from_sms,
      )
    except Exception:
      cls.delete_token(formatted_token)  # delete token if sms fails
      raise ExternalServiceError("Failed to send validation sms.")

    return token

  @staticmethod
  def format_token(token: str) -> str:
    """
    Format token to be used as key in cache."""
    return f"phone-validation-{token}"

  @staticmethod
  def _generate_token():
    """
    Generate a token for phone validation.
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
  def validate_user_phone(cls, user: User, token: str) -> bool:
    if not cls._validate_token(user.id, token):
      return False

    try:
      user.validate_phone()
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
