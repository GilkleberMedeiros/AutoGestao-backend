from unittest.mock import patch, MagicMock

from test.api.base import AuthenticatedTestCase
from apps.users.models import User


@patch("apps.authentication.routes.validate.EmailValidationManager")
class TestValidateEmail(AuthenticatedTestCase):
  TEST_URL = "/api/users/validate/email/"

  user_create_data = {
    "name": "testuser_validate",
    "email": "test.validate@gmail.com",
    "password": "testpassword",
    "phone": "5511999999998",
  }
  user_create_model = User

  login_data = {"email": "test.validate@gmail.com", "password": "testpassword"}

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

  def setUp(self):
    self.user.is_email_valid = False
    self.user.save()

  def test_validate_email_success(self, mock_manager: MagicMock):
    mock_manager.return_value.validate_user_email.return_value = True

    response = self.client.post(
      f"{self.TEST_URL}valid-token",
      HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}",
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response_data.get("success"), True)
    self.assertIsNotNone(response_data.get("details", None))

  def test_validate_email_invalid_token(self, mock_manager: MagicMock):
    mock_manager.return_value.validate_user_email.return_value = False

    response = self.client.post(
      f"{self.TEST_URL}invalid-token",
      HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}",
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertEqual(response_data.get("success"), False)
    self.assertIsNotNone(response_data.get("details", None))

  def test_validate_email_already_valid(self, mock_manager: MagicMock):
    self.user.is_email_valid = True
    self.user.save()

    response = self.client.post(
      f"{self.TEST_URL}any-token",
      HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}",
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 200)
    self.assertIsNotNone(response_data.get("details", None))

  def test_validate_email_db_error(self, mock_manager: MagicMock):
    from apps.core.exceptions import ExternalServiceError

    mock_manager.return_value.validate_user_email.side_effect = ExternalServiceError(
      "DB Error"
    )

    response = self.client.post(
      f"{self.TEST_URL}token", HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}"
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 500)
    self.assertIsNotNone(response_data.get("details", None))

  def test_validate_email_unauthenticated(self, mock_manager: MagicMock):
    response = self.client.post(f"{self.TEST_URL}token")
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsNotNone(response_data.get("details", None))
