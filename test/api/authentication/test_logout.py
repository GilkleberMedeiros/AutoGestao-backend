"""
Test API Logout Endpoint.
"""

from django.test import TestCase, Client
import jwt

from apps.users.models import User
from config import settings


class LogoutTestCase(TestCase):
  URL = "/api/users/auth/logout"

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
    self.logout = lambda *args, **kwargs: self.client.get(
      self.URL, content_type="application/json", *args, **kwargs
    )

    # djando.test.Client automatically manages cookies.
    # Get Refresh Cookie
    login_data = {"email": "testuser.example@gmail.com", "password": "testpassword"}
    _ = self.client.post(
      "/api/users/auth/login", login_data, content_type="application/json"
    )

  def test_logout_successfully(self):

    response = self.logout()
    refresh_token = response.cookies.get("refresh_token", None)

    with self.assertRaises(Exception) as _:
      _ = jwt.decode(
        refresh_token,
        settings.JWT_PUBKEY,
        algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
      )
    self.assertEqual(response.status_code, 200)
