"""
Tests for APIClient.
"""

from django.test import TestCase
from test.api.base import APIClient


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
