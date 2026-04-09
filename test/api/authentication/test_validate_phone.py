from unittest.mock import patch, MagicMock

from test.api.base import AuthenticatedTestCase
from apps.users.models import User


@patch("apps.authentication.routes.validate.PhoneValidationService")
class TestValidatePhone(AuthenticatedTestCase):
  TEST_URL = "/api/users/validate/phone/"

  user_create_data = {
    "name": "testuser_validate_phone",
    "email": "test.validate_phone@gmail.com",
    "password": "testpassword",
    "phone": "5511977777777",
  }
  user_create_model = User

  login_data = {"email": "test.validate_phone@gmail.com", "password": "testpassword"}

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

  def setUp(self):
    self.user.is_phone_valid = False
    self.user.phone = self.user_create_data["phone"]
    self.user.save()

  @classmethod
  def tearDownClass(cls):
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def test_validate_phone_success(self, mock_manager: MagicMock):
    mock_manager.return_value.validate_user_phone.return_value = True

    response = self.client.post(
      f"{self.TEST_URL}123456",
      HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}",
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response_data.get("success"), True)
    self.assertIsNotNone(response_data.get("details", None))

  def test_validate_phone_invalid_code(self, mock_manager: MagicMock):
    mock_manager.return_value.validate_user_phone.return_value = False

    response = self.client.post(
      f"{self.TEST_URL}invalid",
      HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}",
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertEqual(response_data.get("success"), False)
    self.assertIsNotNone(response_data.get("details", None))

  def test_validate_phone_already_valid(self, mock_manager: MagicMock):
    self.user.is_phone_valid = True
    self.user.save()

    response = self.client.post(
      f"{self.TEST_URL}any-code",
      HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}",
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 200)
    self.assertIsNotNone(response_data.get("details", None))

  def test_validate_phone_db_error(self, mock_manager: MagicMock):
    from apps.core.exceptions import ExternalServiceError

    mock_manager.return_value.validate_user_phone.side_effect = ExternalServiceError(
      "DB Error"
    )

    response = self.client.post(
      f"{self.TEST_URL}code", HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}"
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 500)
    self.assertIsNotNone(response_data.get("details", None))

  def test_validate_phone_unauthenticated(self, mock_manager: MagicMock):
    response = self.client.post(f"{self.TEST_URL}code")
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsNotNone(response_data.get("details", None))
