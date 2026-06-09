from unittest.mock import patch, MagicMock

from test.api.conftest import AuthenticatedTestCase
from apps.users.models import User


class UserDeleteRouteTestCase(AuthenticatedTestCase):
  URL = "/api/users"

  user_create_data = {
    "name": "testuser_delete",
    "email": "testdelete@example.com",
    "password": "testpassword",
    "phone": "5584900000099",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testdelete@example.com", "password": "testpassword"}

  @classmethod
  def setUpClass(cls):
    super().setUpClass()

  def setUp(self):
    super().setUp()

    self.user.is_email_valid = True
    self.user.save()

  def _get_valid_token(self):
    return self.credentials["access"]

  # --- Request Deletion (no verification_code) ---

  @patch("apps.users.routes.UserDeleteService")
  def test_request_deletion_success(self, mock_delete_service: MagicMock):
    res = self.client.delete(
      headers={"Authorization": f"Bearer {self._get_valid_token()}"},
    )

    self.assertEqual(res.status_code, 200)
    self.assertTrue(res.json()["success"])

    mock_delete_service.send_verification_code_email.assert_called_once_with(self.user)
    mock_delete_service.send_warn_email.assert_called_once_with(self.user)
    mock_delete_service.send_warn_sms.assert_called_once_with(self.user)
    mock_delete_service.delete_user.assert_not_called()

  def test_request_deletion_unauthenticated_returns_401(self):
    res = self.client.delete()
    self.assertEqual(res.status_code, 401)

  def test_request_deletion_invalid_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()

    res = self.client.delete(headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 403)

  # --- Confirm Deletion (with verification_code) ---

  @patch("apps.users.routes.UserDeleteService")
  def test_confirm_deletion_success(self, mock_delete_service: MagicMock):
    token = self._get_valid_token()

    mock_delete_service.delete_user.return_value = True

    res = self.client.delete(
      "?verification_code=12345678",
      headers={"Authorization": f"Bearer {token}"},
    )
    data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertTrue(data["success"])
    self.assertIn("deleted successfully", data["details"])

    mock_delete_service.delete_user.assert_called_once_with(self.user, "12345678")
    mock_delete_service.send_warn_email.assert_not_called()
    mock_delete_service.send_warn_sms.assert_not_called()
    mock_delete_service.send_verification_code_email.assert_not_called()

  @patch("apps.users.routes.UserDeleteService")
  def test_confirm_deletion_with_invalid_code_returns_error(
    self, mock_delete_service: MagicMock
  ):
    token = self._get_valid_token()
    mock_delete_service.delete_user.return_value = False

    res = self.client.delete(
      "?verification_code=00000000",
      headers={"Authorization": f"Bearer {token}"},
    )
    data = res.json()

    self.assertEqual(res.status_code, 400)
    self.assertFalse(data["success"])

    mock_delete_service.delete_user.assert_called_once_with(self.user, "00000000")
    mock_delete_service.send_verification_code_email.assert_not_called()
    mock_delete_service.send_warn_email.assert_not_called()
    mock_delete_service.send_warn_sms.assert_not_called()


class UserDeleteRouteTestCase__TestE2E_Success(UserDeleteRouteTestCase):
  @patch("apps.users.services.user_deletion.User.sms_user")
  @patch("apps.users.services.user_deletion.User.email_user")
  @patch("apps.users.routes.UserDeleteService._generate_token")
  def test_entire_deletion_flow_end_to_end_success(
    self, mock_code_gen: MagicMock, mock_email_user: MagicMock, mock_sms_user: MagicMock
  ):
    verification_code = "01010101"
    mock_code_gen.return_value = verification_code

    token = self._get_valid_token()

    # Request user deletion
    res1 = self.client.delete(headers={"Authorization": f"Bearer {token}"})

    # Verify token and Delete
    res2 = self.client.delete(
      f"?verification_code={verification_code}",
      headers={"Authorization": f"Bearer {token}"},
    )

    # Verify User was deleted from database
    not_user = User.objects.filter(id=self.user.id).first()
    self.assertIsNone(not_user)

    self.assertEqual(res1.status_code, 200)
    self.assertEqual(res2.status_code, 200)


class UserDeleteRouteTestCase__TestE2E_InvalidCode(UserDeleteRouteTestCase):
  @patch("apps.users.services.user_deletion.User.sms_user")
  @patch("apps.users.services.user_deletion.User.email_user")
  @patch("apps.users.routes.UserDeleteService._generate_token")
  def test_entire_deletion_flow_end_to_end_invalid_code(
    self, mock_code_gen: MagicMock, mock_email_user: MagicMock, mock_sms_user: MagicMock
  ):
    verification_code = "01010101"
    mock_code_gen.return_value = verification_code

    token = self._get_valid_token()

    # Request user deletion
    res1 = self.client.delete(headers={"Authorization": f"Bearer {token}"})

    # Verify token and Delete
    res2 = self.client.delete(
      "?verification_code=88888888",
      headers={"Authorization": f"Bearer {token}"},
    )

    # Verify User wasn't deleted from database
    not_user = User.objects.filter(id=self.user.id).first()
    self.assertIsNotNone(not_user)

    self.assertEqual(res1.status_code, 200)
    self.assertEqual(res2.status_code, 400)
