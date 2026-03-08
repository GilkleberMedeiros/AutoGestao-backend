from django.test import TestCase
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from apps.authentication.lib.email_valiation_manager.manager import (
  EmailValidationManager,
)
from apps.core.exceptions import ExternalServiceError
from django.utils import timezone
from apps.users.models import User


# Send Flow


@patch("apps.authentication.lib.email_valiation_manager.manager.render_to_string")
@patch(
  "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager._set_token"
)
@patch(
  "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager._generate_token"
)
class TestEmailValidation_SendValidationEmail(TestCase):
  def setUp(self):
    self.request = MagicMock()
    self.user = MagicMock()
    self.user.id = "user_id"

  def test_send_validation_email_success(
    self, generate_token: MagicMock, set_token: MagicMock, render_to_string: MagicMock
  ):
    token = "test-token"
    generate_token.return_value = token
    set_token.return_value = f"email-validation-{token}"

    result = EmailValidationManager.send_validation_email(self.request, self.user)

    self.assertEqual(result, token)
    generate_token.assert_called_once()
    set_token.assert_called_once_with(self.user.id, token)
    self.user.email_user.assert_called_once()
    render_to_string.assert_called_once()

  def test_send_validation_email_uses_defaults(
    self, generate_token: MagicMock, set_token: MagicMock, render_to_string: MagicMock
  ):
    EmailValidationManager.send_validation_email(self.request, self.user)

    args, kwargs = self.user.email_user.call_args
    self.assertEqual(kwargs["from_email"], EmailValidationManager.validation_from_email)
    render_to_string.assert_called_once()
    render_args, render_kwargs = render_to_string.call_args
    self.assertEqual(render_args[0], EmailValidationManager.validation_template)

  def test_send_validation_email_uses_custom_values(
    self, generate_token: MagicMock, set_token: MagicMock, render_to_string: MagicMock
  ):
    custom_subject = "Custom Subject"
    custom_template = "custom/template.html"
    custom_from = "custom@example.com"

    EmailValidationManager.send_validation_email(
      self.request,
      self.user,
      subject=custom_subject,
      validation_template=custom_template,
      from_email=custom_from,
    )

    args, kwargs = self.user.email_user.call_args
    self.assertEqual(args[0], custom_subject)
    self.assertEqual(kwargs["from_email"], custom_from)
    render_to_string.assert_called_once()
    render_args, render_kwargs = render_to_string.call_args
    self.assertEqual(render_args[0], custom_template)

  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager.delete_token"
  )
  def test_send_validation_email_failure(
    self,
    delete_token: MagicMock,
    generate_token: MagicMock,
    set_token: MagicMock,
    render_to_string: MagicMock,
  ):
    self.user.email_user.side_effect = Exception("SMTP Error")
    formatted_token = "email-validation-token"
    set_token.return_value = formatted_token

    with self.assertRaises(ExternalServiceError):
      EmailValidationManager.send_validation_email(self.request, self.user)

    delete_token.assert_called_once_with(formatted_token)


class TestEmailValidation_FormatToken(TestCase):
  def test_format_token(self):
    token = "token"
    formatted_token = EmailValidationManager.format_token(token)

    self.assertIsInstance(formatted_token, str)
    self.assertNotEqual(formatted_token, "")
    self.assertNotEqual(formatted_token, token)
    self.assertIn(token, formatted_token)


class TestEmailValidation_GenerateToken(TestCase):
  def test_generate_token(self):
    token = EmailValidationManager._generate_token()

    self.assertIsInstance(token, str)
    self.assertNotEqual(token, "")


@patch(
  "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager.cache_db"
)
class TestEmailValidation_SetToken(TestCase):
  def test_set_token_donot_raises_exception(self, cache_db: MagicMock):
    user_id = "user_id"
    token = "token"
    timeout = 60

    try:
      EmailValidationManager._set_token(user_id, token, timeout)
    except Exception as e:
      self.fail(e)

  def test_set_token_calls_cache_set(self, cache_db: MagicMock):
    user_id = "user_id"
    token = "token"
    timeout = 60

    EmailValidationManager._set_token(user_id, token, timeout)

    cache_db.set.assert_called_once()

  def test_set_token_stores_correct_data(self, cache_db: MagicMock):
    data = None

    def set_data_mock(key, value, timeout):
      nonlocal data
      data = value

    cache_db.set = set_data_mock

    user_id = "user_id"
    token = "token"
    timeout = 60

    EmailValidationManager._set_token(user_id, token, timeout)

    self.assertIsNotNone(data)
    self.assertIsInstance(data, dict)
    self.assertEqual(data.get("user_id"), user_id)
    self.assertIsNotNone(data.get("invalid_at", None))
    self.assertIsInstance(data.get("invalid_at"), datetime)


# Validate Flow
class TestEmailValidation_ValidateUserEmail(TestCase):
  def setUp(self):
    self.user = MagicMock()
    self.user.id = "user_id"
    self.token = "token"

  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager.delete_token"
  )
  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager._validate_token"
  )
  def test_validate_user_email_success(self, _validate_token: MagicMock, delete_token: MagicMock):
    _validate_token.return_value = True

    result = EmailValidationManager.validate_user_email(self.user, self.token)

    self.assertTrue(result)
    _validate_token.assert_called_once_with(self.user.id, self.token)
    self.user.validate_email.assert_called_once()
    delete_token.assert_called_once_with(self.token)

  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager._validate_token"
  )
  def test_validate_user_email_failure_invalid_token(self, _validate_token: MagicMock):
    _validate_token.return_value = False

    result = EmailValidationManager.validate_user_email(self.user, self.token)

    self.assertFalse(result)
    self.user.validate_email.assert_not_called()

  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager._validate_token"
  )
  def test_validate_user_email_failure_db_error(self, _validate_token: MagicMock):
    _validate_token.return_value = True
    self.user.validate_email.side_effect = Exception("DB Error")

    with self.assertRaises(ExternalServiceError):
      EmailValidationManager.validate_user_email(self.user, self.token)

  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager.delete_token"
  )
  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager._validate_token"
  )
  def test_validate_user_email_partial_success_delete_failure(
    self, _validate_token: MagicMock, delete_token: MagicMock
  ):
    _validate_token.return_value = True
    delete_token.side_effect = Exception("Cache Error")

    result = EmailValidationManager.validate_user_email(self.user, self.token)

    self.assertTrue(result)
    self.user.validate_email.assert_called_once()

  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager.delete_token"
  )
  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager._validate_token"
  )
  def test_validate_user_email_on_db(self, _validate_token: MagicMock, delete_token: MagicMock):
    _validate_token.return_value = True
    user = User.objects.create_user(
      name="Test User", email="test@example.com", password="password123", phone="123456789"
    )

    self.assertFalse(user.is_email_valid)

    EmailValidationManager.validate_user_email(user, self.token)

    user.refresh_from_db()
    self.assertTrue(user.is_email_valid)


class TestEmailValidation_ValidateToken(TestCase):
  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager.get_validation_data"
  )
  def test_validate_token_success(self, get_validation_data: MagicMock):
    user_id = "user_id"
    token = "token"
    get_validation_data.return_value = {
      "user_id": user_id,
      "invalid_at": timezone.now() + timedelta(minutes=10),
    }

    result = EmailValidationManager._validate_token(user_id, token)

    self.assertTrue(result)

  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager.get_validation_data"
  )
  def test_validate_token_failure_not_found(self, get_validation_data: MagicMock):
    get_validation_data.return_value = None

    result = EmailValidationManager._validate_token("user_id", "token")

    self.assertFalse(result)

  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager.get_validation_data"
  )
  def test_validate_token_failure_expired(self, get_validation_data: MagicMock):
    user_id = "user_id"
    token = "token"
    get_validation_data.return_value = {
      "user_id": user_id,
      "invalid_at": timezone.now() - timedelta(minutes=10),
    }

    result = EmailValidationManager._validate_token(user_id, token)

    self.assertFalse(result)

  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager.get_validation_data"
  )
  def test_validate_token_failure_user_mismatch(self, get_validation_data: MagicMock):
    token = "token"
    get_validation_data.return_value = {
      "user_id": "other_user",
      "invalid_at": timezone.now() + timedelta(minutes=10),
    }

    result = EmailValidationManager._validate_token("user_id", token)

    self.assertFalse(result)


class TestEmailValidation_GetValidationData(TestCase):
  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager.cache_db"
  )
  def test_get_validation_data_calls_cache_get(self, cache_db: MagicMock):
    token = "token"
    formatted_token = EmailValidationManager.format_token(token)

    EmailValidationManager.get_validation_data(token)

    cache_db.get.assert_called_once_with(formatted_token, None)


class TestEmailValidation_DeleteToken(TestCase):
  @patch(
    "apps.authentication.lib.email_valiation_manager.manager.EmailValidationManager.cache_db"
  )
  def test_delete_token_calls_cache_delete(self, cache_db: MagicMock):
    token = "token"
    formatted_token = EmailValidationManager.format_token(token)

    EmailValidationManager.delete_token(token)

    cache_db.delete.assert_called_once_with(formatted_token)
