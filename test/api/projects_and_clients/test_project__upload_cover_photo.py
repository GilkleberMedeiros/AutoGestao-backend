"""
Test API Upload Project Cover Photo Endpoint.

Route: POST /api/projects/{project_id}/upload-cover-photo
"""

import uuid
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import MULTIPART_CONTENT

from apps.projects_and_clients.models import Project
from apps.users.models import User
from test.api.base import APIClient
from test.api.projects_and_clients.test_project__upd import BaseProjectTestCase


class UploadProjectCoverPhotoTestCase(BaseProjectTestCase):
  def _create_project(self):
    return Project.objects.create(
      user=self.user,
      client=self.client_obj,
      name="Cover Photo Project",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      labor_fee=50.00,
      status="OPEN",
    )

  def _upload(self, project_id, data, headers=None, **kwargs):
    if headers is None:
      headers = {}

    return self.client.post(
      f"{project_id}/upload-cover-photo",
      data=data,
      headers=headers,
      content_type=MULTIPART_CONTENT,
      **kwargs,
    )

  def _auth_headers(self):
    return {"Authorization": f"Bearer {self.credentials['access']}"}

  def test_returns_200_on_successful_png_upload(self):
    project = self._create_project()
    response = self._upload(project.id, {"file": self._make_png_file()}, self._auth_headers())
    self.assertEqual(response.status_code, 200)

  def test_returns_200_on_successful_jpeg_upload(self):
    project = self._create_project()
    response = self._upload(
      project.id, {"file": self._make_jpeg_file()}, self._auth_headers()
    )
    self.assertEqual(response.status_code, 200)

  def test_returns_project_data_on_successful_upload(self):
    project = self._create_project()
    response = self._upload(project.id, {"file": self._make_png_file()}, self._auth_headers())
    response_data = response.json()

    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("id"))
    self.assertIsNotNone(response_data.get("name"))
    self.assertIn("cover_photo", response_data)

  def test_returns_cover_photo_url_in_response(self):
    project = self._create_project()
    response = self._upload(project.id, {"file": self._make_png_file()}, self._auth_headers())
    response_data = response.json()

    self.assertIsNotNone(response_data.get("cover_photo"))

  def test_cover_photo_saved_to_database_after_upload(self):
    project = self._create_project()
    self._upload(project.id, {"file": self._make_png_file()}, self._auth_headers())

    project.refresh_from_db()
    self.assertTrue(bool(project.cover_photo))

  def test_can_overwrite_existing_cover_photo(self):
    project = self._create_project()
    self._upload(project.id, {"file": self._make_png_file()}, self._auth_headers())
    response = self._upload(project.id, {"file": self._make_jpeg_file()}, self._auth_headers())

    self.assertEqual(response.status_code, 200)

  def test_returns_error_when_unauthenticated(self):
    project = self._create_project()
    response = self._upload(project.id, {"file": self._make_png_file()}, headers={})
    self.assertEqual(response.status_code, 401)

  def test_returns_error_body_when_unauthenticated(self):
    project = self._create_project()
    response = self._upload(project.id, {"file": self._make_png_file()}, headers={})
    response_data = response.json()

    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details"))
    self.assertEqual(response_data.get("success"), False)

  def test_returns_error_with_invalid_token(self):
    project = self._create_project()
    headers = {"Authorization": "Bearer invalidtoken"}
    response = self._upload(project.id, {"file": self._make_png_file()}, headers=headers)
    self.assertEqual(response.status_code, 401)

  def test_returns_400_when_file_content_type_is_not_allowed(self):
    project = self._create_project()
    gif = SimpleUploadedFile(
      "animation.gif",
      b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;",
      content_type="image/gif",
    )

    response = self._upload(project.id, {"file": gif}, self._auth_headers())

    self.assertEqual(response.status_code, 400)
    response_data = response.json()
    self.assertEqual(response_data.get("success"), False)
    self.assertIn("Invalid file type", response_data.get("details", ""))

  def test_returns_400_when_file_is_not_image(self):
    project = self._create_project()
    txt_file = SimpleUploadedFile(
      "document.txt", b"not an image", content_type="text/plain"
    )
    response = self._upload(project.id, {"file": txt_file}, self._auth_headers())
    self.assertEqual(response.status_code, 400)

  def test_returns_404_for_other_users_project(self):
    project = self._create_project()

    second_user = User.objects.create_user(
      name="seconduser",
      email="coverphoto.second@example.com",
      password="testpassword",
      phone="5584999999998",
      is_email_valid=True,
    )
    try:
      login_res = APIClient().post(
        "/api/users/auth/login",
        data={"email": "coverphoto.second@example.com", "password": "testpassword"},
      )
      second_token = login_res.json()["access"]

      response = self._upload(
        project.id,
        {"file": self._make_png_file()},
        headers={"Authorization": f"Bearer {second_token}"},
      )
      self.assertEqual(response.status_code, 404)
    finally:
      second_user.delete()

  def test_returns_404_when_project_not_found(self):
    response = self._upload(uuid.uuid4(), {"file": self._make_png_file()}, self._auth_headers())
    self.assertEqual(response.status_code, 404)

  def test_returns_422_when_no_file_provided(self):
    project = self._create_project()
    response = self._upload(project.id, {}, self._auth_headers())
    self.assertEqual(response.status_code, 422)

  def test_returns_403_for_user_with_invalid_email(self):
    project = self._create_project()
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()

    response = self._upload(
      project.id,
      {"file": self._make_png_file()},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(response.status_code, 403)

    self.user.is_email_valid = True
    self.user.save()

  def test_returns_400_when_missing_file_content_type(self):
    project = self._create_project()
    unknown = BytesIO(b"raw-bytes")
    unknown.name = "file.bin"
    response = self._upload(project.id, {"file": unknown}, self._auth_headers())
    self.assertEqual(response.status_code, 400)
