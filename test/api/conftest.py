"""
unittest fixtures for API testing.
"""

from test.api.base import (
  APIClient,
  AuthUserTestCaseMixin,
  JWTAuthenticatedTestCaseMixin,
)
from django.test import TestCase, override_settings

from io import BytesIO

from django.test.client import MULTIPART_CONTENT
from PIL import Image


class APITestCase(TestCase):
  """
  Test case that uses the APIClient by default.

  setUp method creates APIClient instance and store on self.client.

  Set URL attribute to specify the base URL for the APIClient.
  """

  URL: str = None  # Base Url to fetch on test execution

  client_class = APIClient

  def setUp(self):
    super().setUp()

    self.client = APIClient(path_prefix=self.URL)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AuthenticatedTestCase(
  APITestCase, AuthUserTestCaseMixin, JWTAuthenticatedTestCaseMixin
):
  """
  Automanages authentication and user creation for testing.

  This Fixture combines APITestCase, AuthUserTestCaseMixin and JWTAuthenticatedTestCaseMixin to provide:
  - Automatic user creation (for authentication)
  - JWT Authentication credentials
  - APIClient with sensible defaults (client_class attribute default)
  - Faster authentication by overriding password hashers with MD5PasswordHasher

  This class eliges the subclass to define data for:
    - user creation (user_create_data and user_create_model)
    - login (login_data)

  So, be sure to define these attributes in the subclass.

  Usage:
    class MyAuthenticatedTestCase(AuthenticatedTestCase):
      def test_authenticated_endpoint(self):
        # User is automatically created
        # Credentials are automatically set in setUp
        response = self.client.get(
          "/api/protected-endpoint",
          headers={"Authorization": f"Bearer {self.credentials['access']}"}
        )
        self.assertEqual(response.status_code, 200)
  """

  # authenticated user
  user = None

  login_response = None
  # Authentication Credentials (access and refresh tokens)
  credentials = None

  @classmethod
  def setUpClass(cls):
    super().setUpClass()

    if cls.user is None:
      cls.setUpClassUser()

    if cls.credentials is None:
      cls.setUpClassAuth()

  def setUp(self):
    super().setUp()

    self.client.cookies["refresh_token"] = self.credentials["refresh"]

  @classmethod
  def tearDownClass(cls):
    cls.credentials = None
    cls.login_response = None
    cls.user = None
    super().tearDownClass()

  @classmethod
  def upload_user_profile_photo(cls, photo: BytesIO):
    """
    Uploads user profile photo and saves it in the class. Must be called after setUpClass method.

    Args:
      photo: BytesIO instance
    """

    user = cls.user
    if not user:
      raise RuntimeError("User is not set. Please set user before calling this method.")

    if not cls.client:
      raise RuntimeError(
        "Client is not set. Please set client before calling this method."
      )

    if not cls.credentials:
      raise RuntimeError(
        "Credentials are not set. Please set credentials before calling this method."
      )

    response = cls.client.post(
      "/api/users/profile-photo",
      data={"file": photo},
      content_type=MULTIPART_CONTENT,
      headers={"Authorization": f"Bearer {cls.credentials['access']}"},
    )

    if response.status_code != 200:
      raise RuntimeError("Failed to upload user profile photo")

    cls.user.refresh_from_db()

  @staticmethod
  def _make_png_file(name: str = "test.png") -> BytesIO:
    """
    Makes a png file for user profile photo.
    """
    img_io = BytesIO()
    Image.new("RGBA", (60, 30), color="green").save(img_io, "PNG")
    img_io.seek(0)
    img_io.name = name
    return img_io

  @staticmethod
  def _make_jpeg_file(name: str = "test.jpeg") -> BytesIO:
    """
    Makes a jpeg file for user profile photo.
    """
    img_io = BytesIO()
    Image.new("RGB", (60, 30), color="red").save(img_io, "JPEG")
    img_io.seek(0)
    img_io.name = name
    return img_io
