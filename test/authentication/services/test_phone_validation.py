from django.test import TestCase
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from apps.authentication.services.phone_validation import PhoneValidationService
from apps.core.exceptions import ExternalServiceError
from django.utils import timezone
from apps.users.models import User


# Send Flow


@patch(
  "apps.authentication.services.phone_validation.PhoneValidationService._set_token"
)
@patch(
  "apps.authentication.services.phone_validation.PhoneValidationService._generate_token"
)
class TestPhoneValidation_SendValidationCode(TestCase):
  def setUp(self):
    self.user = MagicMock()
    self.user.id = "user_id"
    self.user.phone = "123456789"

  def test_send_validation_code_success(
    self, generate_token: MagicMock, set_token: MagicMock
  ):
    code = "123456"
    generate_token.return_value = code
    set_token.return_value = f"phone-validation-{code}"

    result = PhoneValidationService.send_validation_code(self.user)

    self.assertEqual(result, code)
    generate_token.assert_called_once()
    set_token.assert_called_once_with(self.user.id, code)
    self.user.phone_user.assert_called_once()
    self.assertIn(code, self.user.phone_user.call_args[0][0])

  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService.delete_token"
  )
  def test_send_validation_code_failure(
    self,
    delete_token: MagicMock,
    generate_token: MagicMock,
    set_token: MagicMock,
  ):
    self.user.phone_user.side_effect = Exception("SMS Error")
    formatted_token = "phone-validation-code"
    set_token.return_value = formatted_token

    with self.assertRaises(ExternalServiceError):
      PhoneValidationService.send_validation_code(self.user)

    delete_token.assert_called_once_with(formatted_token)


class TestPhoneValidation_FormatToken(TestCase):
  def test_format_token(self):
    token = "token"
    formatted_token = PhoneValidationService.format_token(token)

    self.assertIsInstance(formatted_token, str)
    self.assertNotEqual(formatted_token, "")
    self.assertNotEqual(formatted_token, token)
    self.assertIn(token, formatted_token)


class TestPhoneValidation_GenerateToken(TestCase):
  def test_generate_token(self):
    token = PhoneValidationService._generate_token()

    self.assertIsInstance(token, str)
    self.assertEqual(len(token), 6)
    self.assertTrue(token.isdigit())


@patch("apps.authentication.services.phone_validation.PhoneValidationService.cache_db")
class TestPhoneValidation_SetToken(TestCase):
  def test_set_token_calls_cache_set(self, cache_db: MagicMock):
    user_id = "user_id"
    token = "token"
    timeout = 60

    PhoneValidationService._set_token(user_id, token, timeout)

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

    PhoneValidationService._set_token(user_id, token, timeout)

    self.assertIsNotNone(data)
    self.assertIsInstance(data, dict)
    self.assertEqual(str(data.get("user_id")), str(user_id))
    self.assertIsNotNone(data.get("invalid_at", None))
    self.assertIsInstance(data.get("invalid_at"), datetime)


# Validate Flow
class TestPhoneValidation_ValidateUserPhone(TestCase):
  def setUp(self):
    self.user = MagicMock()
    self.user.id = "user_id"
    self.token = "token"

  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService.delete_token"
  )
  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService._validate_token"
  )
  def test_validate_user_phone_success(
    self, _validate_token: MagicMock, delete_token: MagicMock
  ):
    _validate_token.return_value = True

    result = PhoneValidationService.validate_user_phone(self.user, self.token)

    self.assertTrue(result)
    _validate_token.assert_called_once_with(self.user.id, self.token)
    self.user.validate_phone.assert_called_once()
    delete_token.assert_called_once_with(self.token)

  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService._validate_token"
  )
  def test_validate_user_phone_failure_invalid_token(self, _validate_token: MagicMock):
    _validate_token.return_value = False

    result = PhoneValidationService.validate_user_phone(self.user, self.token)

    self.assertFalse(result)
    self.user.validate_phone.assert_not_called()

  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService._validate_token"
  )
  def test_validate_user_phone_failure_db_error(self, _validate_token: MagicMock):
    _validate_token.return_value = True
    self.user.validate_phone.side_effect = Exception("DB Error")

    with self.assertRaises(ExternalServiceError):
      PhoneValidationService.validate_user_phone(self.user, self.token)

  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService.delete_token"
  )
  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService._validate_token"
  )
  def test_validate_user_phone_partial_success_delete_failure(
    self, _validate_token: MagicMock, delete_token: MagicMock
  ):
    _validate_token.return_value = True
    delete_token.side_effect = Exception("Cache Error")

    result = PhoneValidationService.validate_user_phone(self.user, self.token)

    self.assertTrue(result)
    self.user.validate_phone.assert_called_once()

  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService.delete_token"
  )
  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService._validate_token"
  )
  def test_validate_user_phone_on_db(
    self, _validate_token: MagicMock, delete_token: MagicMock
  ):
    _validate_token.return_value = True
    user = User.objects.create_user(
      name="Test User",
      email="test_phone@example.com",
      password="password123",
      phone="987654321",
    )

    self.assertFalse(user.is_phone_valid)

    PhoneValidationService.validate_user_phone(user, self.token)

    user.refresh_from_db()
    self.assertTrue(user.is_phone_valid)


class TestPhoneValidation_ValidateToken(TestCase):
  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService.get_validation_data"
  )
  def test_validate_token_success(self, get_validation_data: MagicMock):
    user_id = "user_id"
    token = "token"
    get_validation_data.return_value = {
      "user_id": user_id,
      "invalid_at": timezone.now() + timedelta(minutes=10),
    }

    result = PhoneValidationService._validate_token(user_id, token)

    self.assertTrue(result)

  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService.get_validation_data"
  )
  def test_validate_token_failure_not_found(self, get_validation_data: MagicMock):
    get_validation_data.return_value = None

    result = PhoneValidationService._validate_token("user_id", "token")

    self.assertFalse(result)

  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService.get_validation_data"
  )
  def test_validate_token_failure_expired(self, get_validation_data: MagicMock):
    user_id = "user_id"
    token = "token"
    get_validation_data.return_value = {
      "user_id": user_id,
      "invalid_at": timezone.now() - timedelta(minutes=10),
    }

    result = PhoneValidationService._validate_token(user_id, token)

    self.assertFalse(result)

  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService.get_validation_data"
  )
  def test_validate_token_failure_user_mismatch(self, get_validation_data: MagicMock):
    token = "token"
    get_validation_data.return_value = {
      "user_id": "other_user",
      "invalid_at": timezone.now() + timedelta(minutes=10),
    }

    result = PhoneValidationService._validate_token("user_id", token)

    self.assertFalse(result)


class TestPhoneValidation_GetValidationData(TestCase):
  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService.cache_db"
  )
  def test_get_validation_data_calls_cache_get(self, cache_db: MagicMock):
    token = "token"
    formatted_token = PhoneValidationService.format_token(token)

    PhoneValidationService.get_validation_data(token)

    cache_db.get.assert_called_once_with(formatted_token, None)


class TestPhoneValidation_DeleteToken(TestCase):
  @patch(
    "apps.authentication.services.phone_validation.PhoneValidationService.cache_db"
  )
  def test_delete_token_calls_cache_delete(self, cache_db: MagicMock):
    token = "token"
    formatted_token = PhoneValidationService.format_token(token)

    PhoneValidationService.delete_token(token)

    cache_db.delete.assert_called_once_with(formatted_token)
