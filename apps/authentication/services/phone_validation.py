from django.core.cache import caches
from django.utils.timezone import get_current_timezone

from datetime import datetime, timedelta
import secrets

from config import settings
from apps.users.models import User
from apps.core.exceptions import ExternalServiceError


class PhoneValidationService:
  """
  Manage Phone Validation process.
  Send validation code to user phone and validate it.
  Stores validation codes in cache db.
  """

  cache_db = caches["default"]
  validation_token_lifetime = settings.PHONE_VALIDATION_TOKEN_LIFETIME

  @classmethod
  def send_validation_code(
    cls,
    user: User,
  ) -> str:
    """
    Send validation code to user phone.
    """
    code = cls._generate_token()
    formatted_token = cls._set_token(user.id, code)

    try:
      user.phone_user(f"Seu código de validação do app AutoGestão é: {code}")
    except Exception:
      cls.delete_token(formatted_token)  # delete token if SMS fails
      raise ExternalServiceError("Failed to send validation SMS.")

    return code

  @staticmethod
  def format_token(token: str) -> str:
    """
    Format token to be used as key in cache."""
    return f"phone-validation-{token}"

  @staticmethod
  def _generate_token():
    """
    Generate a 6-digit code for phone validation.
    """
    return f"{secrets.randbelow(1000000):06d}"

  @classmethod
  def _set_token(cls, user_id: str, token: str, timeout: int = None):
    """
    Set token in cache db.
    receives user_id, token and timeout(in seconds) as parameters.
    """
    formatted_token = cls.format_token(token)
    tz = get_current_timezone()
    timeout = timeout or cls.validation_token_lifetime.total_seconds()
    cls.cache_db.set(
      formatted_token,
      {"user_id": user_id, "invalid_at": datetime.now(tz) + timedelta(seconds=timeout)},
      timeout=timeout,
    )
    return formatted_token

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
    if str(data["user_id"]) != str(user_id):
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
