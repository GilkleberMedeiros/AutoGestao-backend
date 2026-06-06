from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from apps.users.services.user_deletion import UserDeleteService
from apps.core.exceptions import ExternalServiceError


class UserDeleteServiceTestCase__SendVerificationCodeEmail(TestCase):
  @patch("apps.users.services.user_deletion.render_to_string")
  @patch.object(UserDeleteService, "_generate_token")
  @patch.object(UserDeleteService, "_set_token")
  def test_send_verification_code_email_success(
    self, mock_set_token, mock_gen_token, mock_render
  ):
    user_mock = MagicMock()
    user_mock.id = "user-123"

    mock_gen_token.return_value = "12345678"
    mock_set_token.return_value = "user-deletion-confirmation-12345678"
    mock_render.return_value = "rendered content"

    token = UserDeleteService.send_verification_code_email(user_mock)

    self.assertEqual(token, "12345678")
    mock_gen_token.assert_called_once()
    mock_set_token.assert_called_once_with("user-123", "12345678")
    mock_render.assert_called_once_with(
      UserDeleteService.template,
      {
        "verification_token": "12345678",
        "verification_token_timeout": int(
          UserDeleteService.verification_token_lifetime.total_seconds() / 60
        ),
      },
    )
    user_mock.email_user.assert_called_once_with(
      "Confirme que você quer deletar sua conta - App AutoGestão",
      "rendered content",
      from_email=UserDeleteService.from_email,
      fail_silently=False,
    )

  @patch("apps.users.services.user_deletion.render_to_string")
  @patch.object(UserDeleteService, "_generate_token")
  @patch.object(UserDeleteService, "_set_token")
  @patch.object(UserDeleteService, "delete_token")
  def test_send_verification_code_email_failure(
    self, mock_delete_token, mock_set_token, mock_gen_token, mock_render
  ):
    user_mock = MagicMock()
    user_mock.id = "user-123"
    user_mock.email_user.side_effect = Exception("SMTP error")

    mock_gen_token.return_value = "12345678"
    mock_set_token.return_value = "user-deletion-confirmation-12345678"
    mock_render.return_value = "rendered content"

    with self.assertRaises(ExternalServiceError):
      UserDeleteService.send_verification_code_email(user_mock)

    mock_delete_token.assert_called_once_with("user-deletion-confirmation-12345678")


class UserDeleteServiceTestCase__SendWarnEmail(TestCase):
  @patch("apps.users.services.user_deletion.render_to_string")
  def test_send_warn_email_success(self, mock_render):
    user_mock = MagicMock()
    mock_render.return_value = "rendered warn content"

    UserDeleteService.send_warn_email(user_mock)

    mock_render.assert_called_once_with(UserDeleteService.warn_email_template, {})
    user_mock.email_user.assert_called_once_with(
      "Sua conta pode ser deletada - App AutoGestão",
      "rendered warn content",
      from_email=UserDeleteService.from_email,
      fail_silently=False,
    )

  @patch("apps.users.services.user_deletion.render_to_string")
  def test_send_warn_email_failure(self, mock_render):
    user_mock = MagicMock()
    user_mock.email_user.side_effect = Exception("SMTP error")
    mock_render.return_value = "rendered warn content"

    with self.assertRaises(ExternalServiceError):
      UserDeleteService.send_warn_email(user_mock)


class UserDeleteServiceTestCase__FormatToken(TestCase):
  def test_format_token(self):
    formatted = UserDeleteService.format_token("abc")
    self.assertEqual(formatted, "user-deletion-confirmation-abc")


class UserDeleteServiceTestCase___GenerateToken(TestCase):
  def test_generate_token_length_and_digits(self):
    token = UserDeleteService._generate_token()
    self.assertEqual(len(token), 8)
    self.assertTrue(token.isdigit())


class UserDeleteServiceTestCase___SetToken(TestCase):
  @patch("apps.users.services.user_deletion.get_current_timezone")
  @patch("apps.users.services.user_deletion.datetime")
  def test_set_token(self, mock_datetime, mock_timezone):
    mock_cache = MagicMock()
    UserDeleteService.cache_db = mock_cache

    mock_tz = MagicMock()
    mock_timezone.return_value = mock_tz
    now_val = datetime(2026, 6, 6, 12, 0, 0)
    mock_datetime.now.return_value = now_val

    user_id = "user-123"
    token = "12345678"

    formatted = UserDeleteService._set_token(user_id, token)

    expected_key = "user-deletion-confirmation-12345678"
    self.assertEqual(formatted, expected_key)

    expected_timeout = UserDeleteService.verification_token_lifetime.total_seconds()
    expected_invalid_at = now_val + timedelta(seconds=expected_timeout)

    mock_cache.set.assert_called_once_with(
      expected_key,
      {"user_id": user_id, "invalid_at": expected_invalid_at},
      timeout=expected_timeout,
    )

  @patch("apps.users.services.user_deletion.get_current_timezone")
  @patch("apps.users.services.user_deletion.datetime")
  def test_set_token_with_custom_timeout(self, mock_datetime, mock_timezone):
    mock_cache = MagicMock()
    UserDeleteService.cache_db = mock_cache

    mock_tz = MagicMock()
    mock_timezone.return_value = mock_tz
    now_val = datetime(2026, 6, 6, 12, 0, 0)
    mock_datetime.now.return_value = now_val

    user_id = "user-123"
    token = "12345678"

    formatted = UserDeleteService._set_token(user_id, token, timeout=60)

    expected_key = "user-deletion-confirmation-12345678"
    self.assertEqual(formatted, expected_key)

    mock_cache.set.assert_called_once_with(
      expected_key,
      {"user_id": user_id, "invalid_at": now_val + timedelta(seconds=60)},
      timeout=60,
    )


class UserDeleteServiceTestCase___GetConfirmationData(TestCase):
  def test_get_confirmation_data(self):
    mock_cache = MagicMock()
    UserDeleteService.cache_db = mock_cache
    mock_cache.get.return_value = {"user_id": "123"}

    res = UserDeleteService.get_confirmation_data("12345678")
    self.assertEqual(res, {"user_id": "123"})
    mock_cache.get.assert_called_once_with("user-deletion-confirmation-12345678", None)


class UserDeleteServiceTestCase___VerifyCode(TestCase):
  @patch.object(UserDeleteService, "get_confirmation_data")
  @patch("apps.users.services.user_deletion.get_current_timezone")
  @patch("apps.users.services.user_deletion.datetime")
  def test_verify_code_success(self, mock_datetime, mock_timezone, mock_get_data):
    now_val = datetime(2026, 6, 6, 12, 0, 0)
    mock_datetime.now.return_value = now_val

    mock_get_data.return_value = {
      "user_id": "user-123",
      "invalid_at": now_val + timedelta(seconds=60),
    }

    res = UserDeleteService._verify_code("user-123", "12345678")
    self.assertTrue(res)
    mock_get_data.assert_called_once_with("12345678")

  @patch.object(UserDeleteService, "get_confirmation_data")
  def test_verify_code_no_data(self, mock_get_data):
    mock_get_data.return_value = None
    res = UserDeleteService._verify_code("user-123", "12345678")
    self.assertFalse(res)

  @patch.object(UserDeleteService, "get_confirmation_data")
  @patch("apps.users.services.user_deletion.get_current_timezone")
  @patch("apps.users.services.user_deletion.datetime")
  def test_verify_code_expired(self, mock_datetime, mock_timezone, mock_get_data):
    now_val = datetime(2026, 6, 6, 12, 0, 0)
    mock_datetime.now.return_value = now_val

    mock_get_data.return_value = {
      "user_id": "user-123",
      "invalid_at": now_val - timedelta(seconds=60),
    }

    res = UserDeleteService._verify_code("user-123", "12345678")
    self.assertFalse(res)

  @patch.object(UserDeleteService, "get_confirmation_data")
  @patch("apps.users.services.user_deletion.get_current_timezone")
  @patch("apps.users.services.user_deletion.datetime")
  def test_verify_code_wrong_user(self, mock_datetime, mock_timezone, mock_get_data):
    now_val = datetime(2026, 6, 6, 12, 0, 0)
    mock_datetime.now.return_value = now_val

    mock_get_data.return_value = {
      "user_id": "user-123",
      "invalid_at": now_val + timedelta(seconds=60),
    }

    res = UserDeleteService._verify_code("user-999", "12345678")
    self.assertFalse(res)


class UserDeleteServiceTestCase___DeleteUser(TestCase):
  @patch.object(UserDeleteService, "_verify_code")
  @patch.object(UserDeleteService, "delete_token")
  def test_delete_user_success(self, mock_delete_token, mock_verify):
    mock_verify.return_value = True
    user_mock = MagicMock()
    user_mock.id = "user-123"

    res = UserDeleteService.delete_user(user_mock, "12345678")
    self.assertTrue(res)
    user_mock.delete.assert_called_once()
    mock_delete_token.assert_called_once_with("12345678")

  @patch.object(UserDeleteService, "_verify_code")
  def test_delete_user_invalid_code(self, mock_verify):
    mock_verify.return_value = False
    user_mock = MagicMock()
    user_mock.id = "user-123"

    res = UserDeleteService.delete_user(user_mock, "12345678")
    self.assertFalse(res)
    user_mock.delete.assert_not_called()

  @patch.object(UserDeleteService, "_verify_code")
  def test_delete_user_db_error(self, mock_verify):
    mock_verify.return_value = True
    user_mock = MagicMock()
    user_mock.id = "user-123"
    user_mock.delete.side_effect = Exception("DB error")

    with self.assertRaises(ExternalServiceError):
      UserDeleteService.delete_user(user_mock, "12345678")

  @patch.object(UserDeleteService, "_verify_code")
  @patch.object(UserDeleteService, "delete_token")
  def test_delete_user_delete_token_fails(self, mock_delete_token, mock_verify):
    mock_verify.return_value = True
    mock_delete_token.side_effect = Exception("Cache error")
    user_mock = MagicMock()
    user_mock.id = "user-123"

    res = UserDeleteService.delete_user(user_mock, "12345678")
    self.assertTrue(res)  # User deletion succeeded, return True


class UserDeleteServiceTestCase__DeleteToken(TestCase):
  def test_delete_token(self):
    mock_cache = MagicMock()
    UserDeleteService.cache_db = mock_cache

    UserDeleteService.delete_token("12345678")
    mock_cache.delete.assert_called_once_with("user-deletion-confirmation-12345678")
