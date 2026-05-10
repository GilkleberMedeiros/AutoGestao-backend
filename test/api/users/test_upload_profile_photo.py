"""
Test API Upload Profile Photo Endpoint.

Route: POST /api/users/profile-photo
"""

from io import BytesIO

from django.test.client import MULTIPART_CONTENT

from apps.users.models import User
from test.api.base import APIClient
from test.api.conftest import AuthenticatedTestCase


class UploadProfilePhotoTestCase(AuthenticatedTestCase):
  URL = "/api/users/profile-photo"

  # Used by AuthenticatedTestCase
  user_create_data = {
    "name": "testuser",
    "email": "testuser.profilephoto@gmail.com",
    "password": "testpassword",
    "phone": "5584100000000",
  }
  user_create_model = User

  login_data = {
    "email": "testuser.profilephoto@gmail.com",
    "password": "testpassword",
  }

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    super().setUpClassUser()
    super().setUpClassAuth()
    cls.png_file = cls._make_png_file()
    cls.jpeg_file = cls._make_jpeg_file()

  def setUp(self):
    super().setUp()
    self.client = APIClient(path_prefix=self.URL)
    self.upload = lambda data, headers, **kwargs: self.client.post(
      "",
      data=data,
      headers=headers,
      # MULTIPART_CONTENT instructs the test client to use multipart/form-data
      # encoding (with a proper auto-generated boundary) instead of the
      # APIClient's default application/json.
      content_type=MULTIPART_CONTENT,
      **kwargs,
    )

  def tearDown(self):
    super().tearDown()
    self.upload = None
    self.client = None

  @classmethod
  def tearDownClass(cls):
    super().tearDownClassAuth()
    super().tearDownClassUser()
    super().tearDownClass()

  def _auth_headers(self):
    return {"Authorization": f"Bearer {self.credentials['access']}"}

  def test_returns_200_on_successful_png_upload(self):
    response = self.upload({"file": self.png_file}, self._auth_headers())
    self.assertEqual(response.status_code, 200)

  def test_returns_200_on_successful_jpeg_upload(self):
    response = self.upload({"file": self.jpeg_file}, self._auth_headers())
    self.assertEqual(response.status_code, 200)

  def test_returns_user_data_on_successful_upload(self):
    """On success the endpoint returns the full UserMeRes schema."""
    response = self.upload({"file": self.png_file}, self._auth_headers())
    response_data = response.json()

    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("id"))
    self.assertIsNotNone(response_data.get("name"))
    self.assertIsNotNone(response_data.get("email"))
    self.assertIn("is_email_valid", response_data)
    self.assertIn("is_phone_valid", response_data)

  def test_returns_profile_photo_url_in_response(self):
    """The profile_photo field in the response should be non-null after upload."""
    response = self.upload({"file": self.png_file}, self._auth_headers())
    response_data = response.json()

    self.assertIsNotNone(response_data.get("profile_photo"))

  def test_profile_photo_saved_to_database_after_upload(self):
    self.upload({"file": self.png_file}, self._auth_headers())

    user = User.objects.get(pk=self.user.pk)
    self.assertTrue(bool(user.profile_photo))

  def test_can_overwrite_existing_profile_photo(self):
    """Uploading a second photo should succeed and replace the first."""
    self.upload({"file": self.png_file}, self._auth_headers())
    response = self.upload({"file": self.jpeg_file}, self._auth_headers())

    self.assertEqual(response.status_code, 200)

  def test_returns_error_when_unauthenticated(self):
    response = self.upload({"file": self.png_file}, headers={})
    self.assertEqual(response.status_code, 401)

  def test_returns_error_body_when_unauthenticated(self):
    response = self.upload({"file": self.png_file}, headers={})
    response_data = response.json()

    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details"))
    self.assertEqual(response_data.get("success"), False)

  def test_returns_error_with_invalid_token(self):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = self.upload({"file": self.png_file}, headers=headers)
    self.assertEqual(response.status_code, 401)

  def test_returns_400_when_file_is_not_image(self):
    txt_file = BytesIO(b"not an image")
    txt_file.name = "document.txt"

    response = self.upload({"file": txt_file}, self._auth_headers())
    self.assertEqual(response.status_code, 400)

  def test_returns_error_body_when_file_is_not_image(self):
    txt_file = BytesIO(b"not an image")
    txt_file.name = "document.txt"

    response = self.upload({"file": txt_file}, self._auth_headers())
    response_data = response.json()

    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details"))
    self.assertEqual(response_data.get("success"), False)

  def test_returns_400_when_gif_uploaded(self):
    """GIF is an image but not in the allowed list (jpeg, png)."""
    gif = BytesIO(
      b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
    )
    gif.name = "animation.gif"

    response = self.upload({"file": gif}, self._auth_headers())
    self.assertEqual(response.status_code, 400)

  def test_returns_400_when_webp_uploaded(self):
    """WebP is an image but not in the allowed list (jpeg, png)."""
    webp = BytesIO(
      b"RIFF\x1c\x00\x00\x00WEBPVP8 \x10\x00\x00\x000\x01\x00\x9d\x01*\x01\x00\x01\x00\x02\x00\x34\x25\xa4\x00\x03p\x00\xfe\xfb\x94\x00\x00"
    )
    webp.name = "image.webp"

    response = self.upload({"file": webp}, self._auth_headers())
    self.assertEqual(response.status_code, 400)

  def test_returns_422_when_no_file_provided(self):
    response = self.upload({}, self._auth_headers())
    self.assertEqual(response.status_code, 422)
