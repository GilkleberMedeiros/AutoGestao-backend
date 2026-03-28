"""
Test ValidEmailPermissionMiddleware
"""

from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.authentication.utils.jwt_auth import JWTAuth


class ValidEmailPermissionMiddlewareTestCase(AuthenticatedTestCase):
  """
  Test suite for ValidEmailPermissionMiddleware.

  The middleware should:
  1. Check if the user is authenticated
  2. Check if the user's email is valid
  3. Return 401 if unauthenticated
  4. Return 403 if email is not valid
  5. Let the request through if both are true
  """

  TEST_ROUTE_PATH = "/api/test-routes/middlewares/valid-email-permission-middleware/"

  user_create_data = {
    "name": "testuser",
    "email": "testuser.example@gmail.com",
    "password": "testpassword",
    "phone": "5584000000000",
  }
  user_create_model = User
  login_data = {"email": "testuser.example@gmail.com", "password": "testpassword"}

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()

  def setUp(self):
    """Set up test client and authenticate."""
    self.client = APIClient(path_prefix=self.TEST_ROUTE_PATH)
    self.setUpAuth()

    # By default in AuthenticatedTestCase, the user might not have is_email_valid=True
    # Let's ensure it's False by default to test the baseline
    self.user.is_email_valid = False
    self.user.save()

  def tearDown(self):
    self.tearDownAuth()
    return super().tearDown()

  @classmethod
  def tearDownClass(cls):
    cls.tearDownClassUser()
    return super().tearDownClass()

  def _make_request(self, headers=None):
    if headers is None:
      headers = {}
    return self.client.get(self.TEST_ROUTE_PATH, headers=headers)

  def _get_valid_token(self, user=None):
    if user is not None:
      return JWTAuth.create_tokens(user)["access"]
    return self.credentials["access"]

  def test_authenticated_user_with_valid_email(self):
    """
    Test the happy path where the user has a valid email and the middleware correctly validates it.
    """
    self.user.is_email_valid = True
    self.user.save()

    token = self._get_valid_token()
    response = self._make_request({"Authorization": f"Bearer {token}"})

    self.assertEqual(response.status_code, 200)
    response_data = response.json()
    self.assertTrue(response_data["success"])
    self.assertEqual(response_data["details"], f"email-valid-{self.user.id}")

  def test_unauthenticated_user_rejected_by_middleware(self):
    """
    Test the exception path where user isn't authenticated and middleware returns its own message.
    """
    # No authorization header provided
    response = self._make_request()

    self.assertEqual(response.status_code, 401)
    response_data = response.json()
    self.assertFalse(response_data["success"])
    self.assertEqual(response_data["details"], "User not authenticated")

  def test_authenticated_user_with_invalid_email_rejected_by_middleware(self):
    """
    Test the exception path where user doesn't have a valid email and middleware returns its own message.
    """
    # user.is_email_valid is False by default in setUp
    token = self._get_valid_token()
    response = self._make_request({"Authorization": f"Bearer {token}"})

    self.assertEqual(response.status_code, 403)
    response_data = response.json()
    self.assertFalse(response_data["success"])
    self.assertEqual(response_data["details"], "User email not valid. Permission rejected.")

  def test_multiple_users_with_different_email_validity(self):
    """
    Test to ensure different users get evaluated with their correct states.
    """
    self.user.is_email_valid = True
    self.user.save()

    # Create second user with invalid email
    user2 = User.objects.create_user(
      name="seconduser",
      email="seconduser@example.com",
      password="testpassword456",
      phone="5584991234567",
    )
    user2.is_email_valid = False
    user2.save()

    token1 = self._get_valid_token(self.user)
    token2 = self._get_valid_token(user2)

    # First user (valid email)
    response1 = self._make_request({"Authorization": f"Bearer {token1}"})
    self.assertEqual(response1.status_code, 200)
    response_data1 = response1.json()
    self.assertTrue(response_data1["success"])
    self.assertEqual(response_data1["details"], f"email-valid-{self.user.id}")

    # Second user (invalid email)
    response2 = self._make_request({"Authorization": f"Bearer {token2}"})
    self.assertEqual(response2.status_code, 403)
    response_data2 = response2.json()
    self.assertFalse(response_data2["success"])
    self.assertEqual(response_data2["details"], "User email not valid. Permission rejected.")
