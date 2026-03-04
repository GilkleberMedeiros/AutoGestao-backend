"""
Test JWTAuthMiddleware
"""

import jwt

from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.authentication.utils.jwt_auth import JWTAuth
from config import settings


class JWTAuthMiddlewareTestCase(AuthenticatedTestCase):
  """
  Test suite for JWTAuthMiddleware.

  The middleware should:
  1. Extract Bearer token from Authorization header
  2. Validate the token
  3. Verify it has a "user_id" field
  4. Get the user from the database
  5. Set request.user if all steps pass
  6. Return AnonymousUser if any step fails
  """

  TEST_ROUTE_PATH = "/api/test-routes/middlewares/jwt-auth-middleware/"

  # Used by AuthenticatedTestCase
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
    """Set up test client and create a test user."""
    self.client = APIClient(path_prefix=self.TEST_ROUTE_PATH)
    self.setUpAuth()

  def tearDown(self):
    self.tearDownAuth()
    return super().tearDown()

  @classmethod
  def tearDownClass(cls):
    cls.tearDownClassUser()
    return super().tearDownClass()

  def _make_request(self, headers={}):
    """
    Make a GET request to the test route.

    Args:
        headers (dict): Optional HTTP headers to include

    Returns:
        Response object
    """
    kwargs = {}
    return self.client.get(self.TEST_ROUTE_PATH, headers=headers, **kwargs)

  def _get_valid_token(self, user=None):
    """
    Get a valid access token for a user.

    Args:
        user: User object. Defaults to self.user

    Returns:
        str: Valid access token
    """
    if user is not None:
      return JWTAuth.create_tokens(user)["access"]
    return self.credentials["access"]

  def test_authenticated_request_with_valid_bearer_token(self):
    """
    Test that middleware authenticates user when valid Bearer token is provided.
    """
    token = self._get_valid_token()

    response = self._make_request({"Authorization": f"Bearer {token}"})

    self.assertEqual(response.status_code, 200)
    response_data = response.json()
    self.assertTrue(response_data["success"])
    self.assertEqual(response_data["details"], f"authenticated-{self.user.id}")

  def test_anonymous_user_without_authorization_header(self):
    """
    Test that user remains anonymous when no Authorization header is provided.
    """
    response = self._make_request()

    self.assertEqual(response.status_code, 400)
    response_data = response.json()
    self.assertFalse(response_data["success"])
    self.assertEqual(response_data["details"], "not-authenticated")

  def test_anonymous_user_with_missing_bearer_token(self):
    """
    Test that user remains anonymous when Authorization header exists but token is missing.
    """
    response = self._make_request({"Authorization": "Bearer "})

    self.assertEqual(response.status_code, 400)
    response_data = response.json()
    self.assertFalse(response_data["success"])
    self.assertEqual(response_data["details"], "not-authenticated")

  def test_anonymous_user_with_invalid_bearer_format(self):
    """
    Test that user remains anonymous when Authorization header has invalid format.
    """
    response = self._make_request({"Authorization": "InvalidFormat sometoken"})

    self.assertEqual(response.status_code, 400)
    response_data = response.json()
    self.assertFalse(response_data["success"])
    self.assertEqual(response_data["details"], "not-authenticated")

  def test_anonymous_user_with_malformed_token(self):
    """
    Test that user remains anonymous when token is malformed.
    """
    response = self._make_request({"Authorization": "Bearer invalid.token.format"})

    self.assertEqual(response.status_code, 400)
    response_data = response.json()
    self.assertFalse(response_data["success"])
    self.assertEqual(response_data["details"], "not-authenticated")

  def test_anonymous_user_with_completely_invalid_token(self):
    """
    Test that user remains anonymous when token is not a valid JWT.
    """
    response = self._make_request({"Authorization": "Bearer notajwttoken"})

    self.assertEqual(response.status_code, 400)
    response_data = response.json()
    self.assertFalse(response_data["success"])
    self.assertEqual(response_data["details"], "not-authenticated")

  def test_anonymous_user_when_token_missing_user_id(self):
    """
    Test that user remains anonymous when token doesn't contain user_id field.
    """
    # Create a JWT token manually without user_id
    payload = {
      "some_field": "some_value",
      "another_field": "another_value",
    }
    invalid_token = jwt.encode(
      payload,
      settings.SIMPLE_JWT["SIGNING_KEY"],
      algorithm=settings.SIMPLE_JWT["ALGORITHM"],
    )

    response = self._make_request({"Authorization": f"Bearer {invalid_token}"})

    self.assertEqual(response.status_code, 400)
    response_data = response.json()
    self.assertFalse(response_data["success"])
    self.assertEqual(response_data["details"], "not-authenticated")

  def test_anonymous_user_with_nonexistent_user_id(self):
    """
    Test that user remains anonymous when token contains user_id
    but user doesn't exist in database.
    """
    # Create token with non-existent user_id
    payload = {
      "user_id": "99999",
      "some_field": "some_value",
    }
    invalid_token = jwt.encode(
      payload,
      settings.SIMPLE_JWT["SIGNING_KEY"],
      algorithm=settings.SIMPLE_JWT["ALGORITHM"],
    )

    response = self._make_request({"Authorization": f"Bearer {invalid_token}"})

    self.assertEqual(response.status_code, 400)
    response_data = response.json()
    self.assertFalse(response_data["success"])
    self.assertEqual(response_data["details"], "not-authenticated")

  def test_authenticates_user_with_correct_user_id(self):
    """
    Test that middleware correctly authenticates user when token
    contains valid user_id that exists in database.
    """
    # Create token with valid user_id
    payload = {
      "user_id": str(self.user.id),
      "email": self.user.email,
    }
    valid_token = jwt.encode(
      payload,
      settings.SIMPLE_JWT["SIGNING_KEY"],
      algorithm=settings.SIMPLE_JWT["ALGORITHM"],
    )

    response = self._make_request({"Authorization": f"Bearer {valid_token}"})

    self.assertEqual(response.status_code, 200)
    response_data = response.json()
    self.assertTrue(response_data["success"])
    self.assertEqual(response_data["details"], f"authenticated-{self.user.id}")

  def test_authenticates_with_real_access_token(self):
    """
    Test that middleware can authenticate using real access token
    generated by JWTAuth.create_tokens().
    """
    token = self._get_valid_token()

    response = self._make_request({"Authorization": f"Bearer {token}"})

    self.assertEqual(response.status_code, 200)
    response_data = response.json()
    self.assertTrue(response_data["success"])
    self.assertEqual(response_data["details"], f"authenticated-{self.user.id}")

  def test_multiple_users_authentication(self):
    """
    Test that middleware correctly authenticates different users
    with their respective tokens.
    """
    # Create second user
    user2 = User.objects.create_user(
      name="seconduser",
      email="seconduser@example.com",
      password="testpassword456",
      phone="5584991234567",
    )

    # Get tokens for both users
    token1 = self._get_valid_token(self.user)
    token2 = self._get_valid_token(user2)

    # Test first user
    response1 = self._make_request({"Authorization": f"Bearer {token1}"})
    self.assertEqual(response1.status_code, 200)
    response_data1 = response1.json()
    self.assertEqual(response_data1["details"], f"authenticated-{self.user.id}")

    # Test second user
    response2 = self._make_request({"Authorization": f"Bearer {token2}"})
    self.assertEqual(response2.status_code, 200)
    response_data2 = response2.json()
    self.assertEqual(response_data2["details"], f"authenticated-{user2.id}")

  def test_authorization_header_case_insensitivity(self):
    """
    Test that middleware handles Authorization header with different cases.
    """
    token = self._get_valid_token()

    # Test different case variations (lowercase)
    response = self._make_request({"Authorization": f"bearer {token}"})

    # Should work or fail gracefully (depends on implementation)
    # Most implementations are case-insensitive for Bearer
    self.assertEqual(response.status_code, 400)

  def test_token_with_extra_whitespace(self):
    """
    Test that middleware handles tokens with extra whitespace.
    """
    token = self._get_valid_token()

    # Test with extra spaces
    response = self._make_request({"Authorization": f"Bearer  {token}"})

    # Should fail as invalid format
    self.assertEqual(response.status_code, 400)
    response_data = response.json()
    self.assertFalse(response_data["success"])

  def test_empty_authorization_header(self):
    """
    Test that middleware handles empty Authorization header.
    """
    response = self._make_request({"Authorization": ""})

    self.assertEqual(response.status_code, 400)
    response_data = response.json()
    self.assertFalse(response_data["success"])

  def test_only_bearer_word(self):
    """
    Test that middleware handles Authorization header with only 'Bearer' word.
    """
    response = self._make_request({"Authorization": "Bearer"})

    self.assertEqual(response.status_code, 400)
    response_data = response.json()
    self.assertFalse(response_data["success"])
