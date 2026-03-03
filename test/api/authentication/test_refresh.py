"""
Test API Refresh Endpoint
"""

from django.test import TestCase, Client
from django.utils.timezone import get_current_timezone
import jwt
from datetime import datetime, timedelta

from apps.users.models import User
from config import settings


class RefreshTestCase(TestCase):
  URL = "/api/users/auth/refresh"

  @classmethod
  def setUpClass(cls):
    super().setUpClass()

    # Create User
    try:
      cls.user = User.objects.create_user(
        name="testuser",
        email="testuser.example@gmail.com",
        password="testpassword",
        phone="5584000000000",
      )
    except Exception as e:
      raise Exception(
        f"Unknown exception while creating user for LoginTestCase!\nException: \n{e}"
      )

  def setUp(self):
    self.client = Client()
    self.refresh = lambda *args, **kwargs: self.client.get(
      self.URL, content_type="application/json", *args, **kwargs
    )

    # djando.test.Client automatically manages cookies.
    login_data = {"email": "testuser.example@gmail.com", "password": "testpassword"}
    _ = self.client.post(
      "/api/users/auth/login", login_data, content_type="application/json"
    )

  def test_refresh_token_successfully(self):
    # Got refresh_token cookie on setUp method.

    response = self.refresh()
    response_data = response.json()

    self.assertEqual(response.status_code, 200)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("access", None))
    try:
      access_value = jwt.decode(
        response_data.get("access", None),
        settings.JWT_PUBKEY,
        algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
      )
    except Exception as e:
      self.fail(
        f"Returned access token on refresh endpoint isn't valid! \nERROR: \n{e}"
      )
    self.assertIsNotNone(access_value.get("user_id", None))
    self.assertEqual(access_value["user_id"], str(self.user.id))

  def test_doesnot_return_new_refresh_token(self):
    # Got refresh_token cookie on setUp method.

    response = self.refresh()
    response_data = response.json()
    refresh_token = response.cookies.get("refresh_token", None)

    self.assertEqual(response.status_code, 200)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("access", None))
    self.assertNotIn("refresh", response_data)
    self.assertIsNone(refresh_token)

  def test_returns_error_response_on_expired_refresh_cookie(self):
    # Create an expired refresh token by manually encoding a JWT with an exp in the past
    tz = get_current_timezone()
    now = datetime.now(tz)
    payload = {
      "user_id": str(self.user.id),
      "exp": int((now - timedelta(hours=1)).timestamp()),
      "iat": int((now - timedelta(days=1)).timestamp()),
    }
    expired_token = jwt.encode(
      payload, settings.JWT_PRIVKEY, algorithm=settings.SIMPLE_JWT["ALGORITHM"]
    )
    self.client.cookies["refresh_token"] = expired_token
    response = self.refresh()
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_returns_error_response_on_missing_refresh_cookie(self):
    # Got refresh_token cookie on setUp method.

    del self.client.cookies["refresh_token"]
    response = self.refresh()
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_returns_error_response_on_invalid_refresh_token(self):
    # Got refresh_token cookie on setUp method.

    self.client.cookies["refresh_token"] = "<invalid_refresh_token>"
    response = self.refresh()
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_returns_error_response_on_empty_string_refresh_token(self):
    # Got refresh_token cookie on setUp method.

    self.client.cookies["refresh_token"] = ""
    response = self.refresh()
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_returns_error_response_on_null_refresh_token(self):
    # Got refresh_token cookie on setUp method.

    self.client.cookies["refresh_token"] = None
    response = self.refresh()
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)
