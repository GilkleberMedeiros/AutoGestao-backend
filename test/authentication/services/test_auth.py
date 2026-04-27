from django.test import TestCase
from unittest.mock import patch, MagicMock
from unittest import mock

from apps.authentication.schemas import LoginReq, RegisterReq
from apps.authentication.services.auth import (
  AuthService,
  UserInvalidCredentialsError,
  UserEmailAlreadyExistsError,
  UserPhoneAlreadyExistsError,
  MissingRefreshTokenError,
  InvalidRefreshTokenError,
)


class TestAuthService__Login(TestCase):
  def setUp(self) -> None:
    self.login_data = LoginReq(
      email="test_user@example.com",
      password="test_password",
    )
    self.user_mock = MagicMock()
    self.user_mock.check_password.return_value = True

  @patch("apps.authentication.services.auth.User")
  @patch("apps.authentication.services.auth.JWTAuth")
  def test_login_success(self, jwt_auth_mock: MagicMock, user_model_mock: MagicMock):
    """
    Test login returns correct tokens
    """
    user_model_mock.objects.filter.return_value.first.return_value = self.user_mock
    jwt_auth_mock.create_tokens.return_value = {
      "access": "fake_access",
      "refresh": "fake_refresh",
    }

    tokens = AuthService.login(self.login_data)

    self.assertIsNotNone(tokens["access"])
    self.assertIsNotNone(tokens["refresh"])
    user_model_mock.objects.filter.assert_called_once_with(email=self.login_data.email)
    self.user_mock.check_password.assert_called_once_with(self.login_data.password)

  @patch("apps.authentication.services.auth.User")
  def test_login_raises_user_invalid_credentials_error_when_user_not_found(
    self, user_model_mock: MagicMock
  ):
    """
    Test login raises UserInvalidCredentialsError when user not found
    """
    user_model_mock.objects.filter.return_value.first.return_value = None
    self.login_data.email = "invalid_user@example.com"

    with self.assertRaises(UserInvalidCredentialsError):
      AuthService.login(self.login_data)

  @patch("apps.authentication.services.auth.User")
  def test_login_raises_user_invalid_credentials_error_when_password_is_invalid(
    self, user_model_mock: MagicMock
  ):
    """
    Test login raises UserInvalidCredentialsError when password is invalid
    """
    self.user_mock.check_password.return_value = False
    user_model_mock.objects.filter.return_value.first.return_value = self.user_mock
    self.login_data.password = "invalid_password"

    with self.assertRaises(UserInvalidCredentialsError):
      AuthService.login(self.login_data)


class TestAuthService__Register(TestCase):
  def setUp(self) -> None:
    self.register_data = RegisterReq(
      name="Test User",
      email="test_user@example.com",
      password="test_password",
      phone="551199999999",
    )
    self.user_mock = MagicMock()

  @patch("apps.authentication.services.auth.User")
  def test_register_success(self, user_model_mock: MagicMock):
    """
    Test register returns correct user
    """
    user_model_mock.objects.filter.return_value.exists.return_value = False
    user_model_mock.create_user.return_value = self.user_mock

    user = AuthService.register(self.register_data)

    self.assertIsNotNone(user.email)
    user_model_mock.objects.filter.assert_has_calls(
      [
        mock.call(email=self.register_data.email),
        mock.call().exists(),
        mock.call(phone=self.register_data.phone),
        mock.call().exists(),
      ]
    )
    user_model_mock.objects.create_user.assert_called_once_with(
      name=self.register_data.name,
      email=self.register_data.email,
      password=self.register_data.password,
      phone=self.register_data.phone,
    )

  @patch("apps.authentication.services.auth.User")
  def test_register_raises_user_email_already_exists_error_when_user_email_already_exists(
    self, user_model_mock: MagicMock
  ):
    """
    Test register raises UserEmailAlreadyExistsError when user email already exists
    """
    user_model_mock.objects.filter.return_value.exists.return_value = True

    with self.assertRaises(UserEmailAlreadyExistsError):
      AuthService.register(self.register_data)

  @patch("apps.authentication.services.auth.User")
  def test_register_raises_user_phone_already_exists_error_when_user_phone_already_exists(
    self, user_model_mock: MagicMock
  ):
    """
    Test register raises UserPhoneAlreadyExistsError when user phone already exists
    """
    user_model_mock.objects.filter.return_value.exists.side_effect = [
      False,
      True,
    ]

    with self.assertRaises(UserPhoneAlreadyExistsError):
      AuthService.register(self.register_data)

  @patch("apps.authentication.services.auth.User")
  def test_register_allows_none_phone(self, user_model_mock: MagicMock):
    """
    Test register allows None phone
    """
    self.register_data.phone = None
    user_model_mock.objects.filter.return_value.exists.return_value = False
    user_model_mock.create_user.return_value = self.user_mock

    user = AuthService.register(self.register_data)

    self.assertIsNotNone(user.email)
    user_model_mock.objects.filter.assert_called_once_with(
      email=self.register_data.email
    )
    user_model_mock.objects.create_user.assert_called_once_with(
      name=self.register_data.name,
      email=self.register_data.email,
      password=self.register_data.password,
      phone=self.register_data.phone,
    )


class TestAuthService__Refresh(TestCase):
  def setUp(self) -> None:
    self.refresh_token = "fake_refresh_token"
    self.user_mock = MagicMock()
    self.user_mock.id = 1

  @patch("apps.authentication.services.auth.JWTAuth")
  @patch("apps.authentication.services.auth.User")
  def test_refresh_success(self, user_model_mock: MagicMock, jwt_auth_mock: MagicMock):
    """
    Test refresh returns correct tokens
    """
    jwt_auth_mock.verify_token.return_value = {
      "user_id": self.user_mock.id,
      "exp": 1234567890,
    }
    jwt_auth_mock.create_tokens.return_value = {
      "access": "fake_access",
      "refresh": "fake_refresh",
    }
    user_model_mock.objects.filter.return_value.first.return_value = self.user_mock

    tokens = AuthService.refresh(self.refresh_token)

    self.assertIsNotNone(tokens["access"])
    self.assertIsNotNone(tokens["refresh"])
    jwt_auth_mock.verify_token.assert_called_once_with(self.refresh_token)
    jwt_auth_mock.create_tokens.assert_called_once_with(self.user_mock)

  @patch("apps.authentication.services.auth.JWTAuth")
  def test_refresh_raises_missing_refresh_token_error(self, jwt_auth_mock: MagicMock):
    """
    Test refresh raises MissingRefreshTokenError when refresh token is not provided
    """
    with self.assertRaises(MissingRefreshTokenError):
      AuthService.refresh(None)

  @patch("apps.authentication.services.auth.JWTAuth")
  def test_refresh_raises_invalid_refresh_token_error_when_token_is_invalid(
    self, jwt_auth_mock: MagicMock
  ):
    """
    Test refresh raises InvalidRefreshTokenError when token is invalid
    """
    jwt_auth_mock.verify_token.return_value = None

    with self.assertRaises(InvalidRefreshTokenError):
      AuthService.refresh(self.refresh_token)

  @patch("apps.authentication.services.auth.JWTAuth")
  def test_refresh_raises_invalid_refresh_token_error_when_user_id_is_not_found(
    self, jwt_auth_mock: MagicMock
  ):
    """
    Test refresh raises InvalidRefreshTokenError when user id is not found
    """
    jwt_auth_mock.verify_token.return_value = {
      "exp": 1234567890,
    }

    with self.assertRaises(InvalidRefreshTokenError):
      AuthService.refresh(self.refresh_token)

  @patch("apps.authentication.services.auth.JWTAuth")
  @patch("apps.authentication.services.auth.User")
  def test_refresh_raises_invalid_refresh_token_error_when_user_is_not_found(
    self, user_model_mock: MagicMock, jwt_auth_mock: MagicMock
  ):
    """
    Test refresh raises InvalidRefreshTokenError when user is not found
    """
    jwt_auth_mock.verify_token.return_value = {
      "user_id": self.user_mock.id,
      "exp": 1234567890,
    }
    user_model_mock.objects.filter.return_value.first.return_value = None

    with self.assertRaises(InvalidRefreshTokenError):
      AuthService.refresh(self.refresh_token)
