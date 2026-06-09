import secrets
import string
from datetime import datetime, timedelta

from django.core.cache import caches
from django.conf import settings
from django.utils.timezone import get_current_timezone
from django.template.loader import render_to_string

from apps.users.models import User
from apps.core.exceptions import ExternalServiceError


class UserDeleteService:
  """
  Manage User deletion process.
  Send Warn Email (and SMS) to User to warn about deletion process.
  Send Email with verification code to confirm deletion and
  process authentication.
  Stores verication token/code in cache db and validates it before permanent deletion.
  """

  cache_db = caches["default"]
  warn_email_template = settings.WARN_USER_DELETION_EMAIL_TEMPLATE
  warn_sms_template = settings.WARN_USER_DELETION_SMS_TEMPLATE
  template = settings.CONFIRM_USER_DELETION_EMAIL_TEMPLATE
  from_email = settings.DEFAULT_FROM_EMAIL
  from_sms = settings.DEFAULT_FROM_SMS
  verification_token_lifetime = settings.USER_DELETION_VERIFICATION_TOKEN_LIFETIME

  @classmethod
  def send_verification_code_email(
    cls,
    user: User,
    *,
    subject: str = "Confirme que você quer deletar sua conta - App AutoGestão",
    template: str = None,
    from_email: str = None,
  ) -> str:
    """
    Send verification code to user email.
    """
    token = cls._generate_token()
    formatted_token = cls._set_token(user.id, token)

    if not template:
      template = cls.template
    if not from_email:
      from_email = cls.from_email

    try:
      user.email_user(
        subject,
        render_to_string(
          template,
          {
            "verification_token": token,
            "verification_token_timeout": int(
              cls.verification_token_lifetime.total_seconds() / 60
            ),
          },
        ),
        from_email=from_email,
        fail_silently=False,
      )
    except Exception:
      cls.delete_token(formatted_token)  # delete token if email fails
      raise ExternalServiceError("Failed to send validation email.")

    return token

  @classmethod
  def send_warn_email(
    cls,
    user: User,
    *,
    subject: str = "Sua conta pode ser deletada - App AutoGestão",
    warn_email_template: str = None,
    from_email: str = None,
  ) -> None:
    """
    Send warn email to user email.
    """
    if not warn_email_template:
      warn_email_template = cls.warn_email_template
    if not from_email:
      from_email = cls.from_email

    try:
      user.email_user(
        subject,
        render_to_string(warn_email_template, {}),
        from_email=from_email,
        fail_silently=False,
      )
    except Exception:
      raise ExternalServiceError("Failed to send warn email.")

  @classmethod
  def send_warn_sms(
    cls,
    user: User,
    *,
    warn_sms_template: str = None,
    from_sms: str = None,
  ) -> None:
    """
    Send warn sms to user sms.
    """
    if not warn_sms_template:
      warn_sms_template = cls.warn_sms_template
    if not from_sms:
      from_sms = cls.from_sms

    try:
      user.sms_user(
        render_to_string(warn_sms_template, {}),
        from_sms=from_sms,
      )
    except Exception:
      raise ExternalServiceError("Failed to send warn sms.")

  @staticmethod
  def format_token(token: str) -> str:
    """
    Format token to be used as key in cache."""
    return f"user-deletion-confirmation-{token}"

  @staticmethod
  def _generate_token():
    """
    Generate a token for deletion request verification.
    """
    digits = string.digits
    token = "".join(secrets.choice(digits) for _ in range(8))
    return token

  @classmethod
  def _set_token(cls, user_id: str, token: str, timeout: int = None):
    """
    Set token/code in cache db.
    receives user_id, token and timeout(in seconds) as parameters.
    """
    token = cls.format_token(token)
    tz = get_current_timezone()
    timeout = timeout or cls.verification_token_lifetime.total_seconds()
    cls.cache_db.set(
      token,
      {"user_id": user_id, "invalid_at": datetime.now(tz) + timedelta(seconds=timeout)},
      timeout=timeout,
    )
    return token

  @classmethod
  def get_confirmation_data(cls, token: str) -> dict | None:
    return cls.cache_db.get(cls.format_token(token), None)

  @classmethod
  def _verify_code(cls, user_id: str, token: str):
    """
    Verify given confirm deletion code on cache db.
    """
    data = cls.get_confirmation_data(token)
    if not data:
      return False
    if data["invalid_at"] < datetime.now(get_current_timezone()):
      return False
    if data["user_id"] != user_id:
      return False
    return True

  @classmethod
  def delete_user(cls, user: User, token: str) -> bool:
    """
    Verify cconfirm deletion code and delete user if valid.
    """
    if not cls._verify_code(user.id, token):
      return False

    try:
      user.delete()
    except Exception:
      raise ExternalServiceError("Failed to delete user.")

    try:
      cls.delete_token(token)
    except Exception:
      return True

    return True

  @classmethod
  def delete_token(cls, token: str):
    cls.cache_db.delete(cls.format_token(token))
