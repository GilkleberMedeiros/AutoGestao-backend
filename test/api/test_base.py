"""
Tests for APIClient.
"""

from django.test import TestCase
from test.api.base import APIClient, APITestCase, JWTAuthenticatedTestCaseMixin
from apps.users.models import User


class APIClientTestCase(TestCase):
  """Test the APIClient functionality."""

  def test_default_content_type(self):
    """Verify default content type is application/json."""
    client = APIClient()
    self.assertEqual(client.content_type, "application/json")

  def test_custom_content_type(self):
    """Verify custom content type can be set on instantiation."""
    client = APIClient(content_type="application/xml")
    self.assertEqual(client.content_type, "application/xml")

  def test_default_path_prefix(self):
    """Verify default path_prefix is empty string."""
    client = APIClient()
    self.assertEqual(client.path_prefix, "")

  def test_custom_path_prefix(self):
    """Verify custom path_prefix can be set on instantiation."""
    client = APIClient(path_prefix="/api/")
    self.assertEqual(client.path_prefix, "/api")  # Trailing slash removed

  def test_path_preparation_without_path_prefix(self):
    """Verify path is not modified when path_prefix is not set."""
    client = APIClient()
    path = client._prepare_path("/users/")
    self.assertEqual(path, "/users/")

  def test_path_preparation_with_path_prefix(self):
    """Verify path is prefixed with path_prefix when set."""
    client = APIClient(path_prefix="/api/")
    path = client._prepare_path("users/")
    self.assertEqual(path, "/api/users/")

  def test_path_preparation_with_path_prefix_removes_leading_slash(self):
    """Verify leading slash is removed from path before prepending path_prefix."""
    client = APIClient(path_prefix="/api/")
    path = client._prepare_path("/users/")
    self.assertEqual(path, "/api/users/")

  def test_kwargs_preparation_adds_content_type(self):
    """Verify content_type is added to kwargs if not present."""
    client = APIClient(content_type="application/json")
    kwargs = {}
    prepared = client._prepare_kwargs(kwargs)
    self.assertEqual(prepared["content_type"], "application/json")

  def test_kwargs_preparation_preserves_custom_content_type(self):
    """Verify custom content_type in kwargs is not overridden."""
    client = APIClient(content_type="application/json")
    kwargs = {"content_type": "application/xml"}
    prepared = client._prepare_kwargs(kwargs)
    self.assertEqual(prepared["content_type"], "application/xml")

  def test_client_inheritance(self):
    """Verify APIClient is a subclass of Client."""
    client = APIClient()
    from django.test import Client

    self.assertIsInstance(client, Client)


class JWTAuthenticatedTestCaseMixinTestCase(TestCase):
  """Test the JWTAuthenticatedTestCaseMixin functionality."""

  @classmethod
  def setUpClass(cls):
    """Create a test user for authentication tests."""
    super().setUpClass()
    cls.test_user = User.objects.create_user(
      name="testuser",
      email="testuser@example.com",
      password="testpassword123",
      phone="5584999999999",
    )

  def test_jwt_mixin_has_correct_defaults(self):
    """Verify JWTAuthenticatedTestCaseMixin has correct class attributes."""
    self.assertEqual(JWTAuthenticatedTestCaseMixin.login_url, "/api/users/auth/login")
    self.assertEqual(JWTAuthenticatedTestCaseMixin.logout_url, "/api/users/auth/logout")
    self.assertIsNone(JWTAuthenticatedTestCaseMixin.login_data)

  def test_extract_credentials_from_login_response(self):
    """Verify _extract_credentials correctly extracts tokens."""
    client = APIClient()
    response = client.post(
      "/api/users/auth/login",
      {"email": "testuser@example.com", "password": "testpassword123"},
    )

    credentials = JWTAuthenticatedTestCaseMixin._extract_credentials(response)

    self.assertIsInstance(credentials, dict)
    self.assertIn("access", credentials)
    self.assertIn("refresh", credentials)
    self.assertIsNotNone(credentials["access"])
    self.assertIsNotNone(credentials["refresh"])

  def test_extract_credentials_returns_none_for_missing_tokens(self):
    """Verify _extract_credentials handles missing tokens gracefully."""
    from unittest.mock import Mock

    # Create a mock response with no tokens
    mock_response = Mock()
    mock_response.json.return_value = {}
    mock_response.cookies = {}

    credentials = JWTAuthenticatedTestCaseMixin._extract_credentials(mock_response)

    self.assertEqual(credentials["access"], None)
    self.assertEqual(credentials["refresh"], None)

  def test_api_test_case_client_is_api_client(self):
    """Verify APITestCase uses APIClient with defaults."""

    class DummyAPITestCase(APITestCase):
      pass

    test_case = DummyAPITestCase("__init__")
    test_case._pre_setup()

    self.assertIsInstance(test_case.client, APIClient)
    self.assertEqual(test_case.client.content_type, "application/json")

    test_case._post_teardown()
