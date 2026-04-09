from unittest.mock import patch, MagicMock

from test.api.base import AuthenticatedTestCase
from apps.users.models import User


@patch("apps.authentication.routes.validate.PhoneValidationService")
class TestRequestPhoneValidation(AuthenticatedTestCase):
  TEST_URL = "/api/users/validate/request-validation/phone"

  user_create_data = {
    "name": "testuser_phone",
    "email": "test.phone@gmail.com",
    "password": "testpassword",
    "phone": "5511988888888",
  }
  user_create_model = User

  login_data = {"email": "test.phone@gmail.com", "password": "testpassword"}

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

  def test_request_phone_validation_success(self, mock_manager: MagicMock):
    response = self.client.post(
      self.TEST_URL, HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}"
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response_data.get("success"), True)
    self.assertIsNotNone(response_data.get("details", None))

  def test_calls_send_code(self, mock_manager: MagicMock):
    self.client.post(
      self.TEST_URL, HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}"
    )

    mock_manager.return_value.send_validation_code.assert_called_once()

  def test_request_phone_validation_already_valid(self, mock_manager: MagicMock):
    self.user.is_phone_valid = True
    self.user.save()

    response = self.client.post(
      self.TEST_URL, HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}"
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 200)
    self.assertIsNotNone(response_data.get("details", None))
    mock_manager.return_value.send_validation_code.assert_not_called()

  def test_request_phone_validation_unauthenticated(self, mock_manager: MagicMock):
    response = self.client.post(self.TEST_URL)
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsNotNone(response_data.get("details", None))

  def test_request_phone_validation_no_phone(self, mock_manager: MagicMock):
    self.user.phone = None
    self.user.save()

    response = self.client.post(
      self.TEST_URL, HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}"
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIn("phone", response_data.get("details", "").lower())

  def test_request_phone_validation_failure_sms_error(self, mock_manager: MagicMock):
    from apps.core.exceptions import ExternalServiceError

    mock_manager.return_value.send_validation_code.side_effect = ExternalServiceError(
      "Failed to send SMS"
    )

    response = self.client.post(
      self.TEST_URL, HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}"
    )
    response_data = response.json()

    self.assertEqual(response.status_code, 500)
    self.assertIsNotNone(response_data.get("details", None))
