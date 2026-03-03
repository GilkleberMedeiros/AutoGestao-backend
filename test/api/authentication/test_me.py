"""
Test API Logout Endpoint.
"""

from django.http import HttpResponse
from django.test import TestCase, Client
import jwt
import uuid
from datetime import datetime, timedelta
from django.utils.timezone import get_current_timezone

from apps.users.models import User
from config import settings


class LogoutTestCase(TestCase):
  URL = "/api/users/auth/me"

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
    self.me = lambda headers, *args, **kwargs: self.client.get(
      self.URL, headers=headers, content_type="application/json", *args, **kwargs
    )

    self.login_response = self.login()
    self.credentials = self.get_jwt_credentials(self.login_response)

  def tearDown(self):
    super().tearDown()
    logout_res = self.client.get(
      "/api/users/auth/logout", content_type="application/json"
    )
    if logout_res.status_code != 200:
      raise Exception(
        "Got unexpected response when trying to logout!\n"
        f"Response data: {logout_res.json()}\nStatus code: {logout_res.status_code}"
      )
    self.credentials = None
    self.login_response = None

    self.me = None
    self.client = None

  def login(self):
    """Login to app and returns response."""
    # djando.test.Client automatically manages cookies.
    # Get Login Credentials
    login_data = {"email": "testuser.example@gmail.com", "password": "testpassword"}
    response = self.client.post(
      "/api/users/auth/login", login_data, content_type="application/json"
    )

    return response

  @staticmethod
  def get_jwt_credentials(response: HttpResponse):
    """Get credentials from response"""
    response_data = response.json()
    if not isinstance(response_data, dict):
      raise Exception(
        f"Given response body isn't from the expected type! Expected type dict, got type {type(response_data)} instead."
      )

    access = response_data.get("access", None)
    refresh = response.cookies.get("refresh_token", None)

    if not access:
      raise Exception(
        f"Couldn't get access token from given response! Got value {access} instead."
      )
    if not refresh:
      raise Exception(
        f"Couldn't get refresh token from given response! Got value {refresh} instead."
      )

    return {"access": access, "refresh": refresh}

  def test_user_me_successfully(self):
    access_token = self.credentials["access"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = self.me(headers)
    response_data = response.json()

    self.assertIsNotNone(response_data)

  def test_get_user_data(self):
    access_token = self.credentials["access"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = self.me(headers)
    response_data = response.json()

    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("id", None))
    self.assertIsNotNone(response_data.get("name", None))
    self.assertIsNotNone(response_data.get("email", None))
    self.assertIsNotNone(response_data.get("phone", None))

  def test_get_correct_user_data(self):
    access_token = self.credentials["access"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = self.me(headers)
    response_data = response.json()

    self.assertIsInstance(response_data, dict)
    self.assertEqual(str(self.user.id), response_data.get("id", None))
    self.assertEqual(self.user.name, response_data.get("name", None))
    self.assertEqual(self.user.email, response_data.get("email", None))
    self.assertEqual(self.user.phone, response_data.get("phone", None))

  def test_returns_error_response_on_invalid_access_token(self):
    # Send an invalid/malformed access token
    headers = {"Authorization": "Bearer <invalid_token>"}
    response = self.me(headers)
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_returns_error_response_on_missing_access_token(self):
    headers = {"Authorization": "Bearer "}
    response = self.me(headers)
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_returns_error_response_on_missing_authorization_header(self):
    headers = {}
    response = self.me(headers)
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_returns_error_response_on_token_for_inexistent_user(self):
    # Create a valid JWT token for a user that doesn't exist
    tz = get_current_timezone()
    now = datetime.now(tz)
    fake_user_id = str(uuid.uuid4())
    payload = {
      "user_id": fake_user_id,
      "exp": int((now + timedelta(hours=1)).timestamp()),
      "iat": int(now.timestamp()),
    }
    invalid_user_token = jwt.encode(
      payload, settings.JWT_PRIVKEY, algorithm=settings.SIMPLE_JWT["ALGORITHM"]
    )
    headers = {"Authorization": f"Bearer {invalid_user_token}"}
    response = self.me(headers)
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)

  def test_returns_error_response_on_missing_bearer_prefix(self):
    # Send authorization header without 'Bearer ' prefix
    access_token = self.credentials["access"]

    headers = {"Authorization": access_token}  # Missing 'Bearer ' prefix
    response = self.me(headers)
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)
