"""
Base Test Client for API Testing.
"""

from django.test import Client, TestCase


class APIClient(Client):
  """
  Custom test client for API testing with sensible defaults.

  Features:
  - Default content_type is 'application/json'
  - Customizable content_type on instantiation
  - Optional default API path prefix

  Example:
      # Create a client with default content type and API path
      client = APITestClient(path_prefix="/api/users/")

      # Make requests
      response = client.post("auth/login", {"email": "test@example.com"})
      # Actually requests: POST /api/users/auth/login

      # Override content type on instantiation
      client = APITestClient(content_type="application/xml")
  """

  def __init__(self, content_type="application/json", path_prefix="", **kwargs):
    """
    Initialize APITestClient.

    Args:
        content_type (str): Default content type for API requests.
                           Defaults to "application/json"
        path_prefix (str): Optional default API path prefix.
                       Will be prepended to relative paths in requests.
                       Defaults to empty string (no prefix)
        **kwargs: Additional arguments passed to parent Client

    Example:
        # Client with default json content type and /api/ prefix
        client = APITestClient(path_prefix="/api/")

        # Client with custom content type
        client = APITestClient(content_type="application/xml")
    """
    super().__init__(**kwargs)
    self.content_type = content_type
    self.path_prefix = path_prefix.rstrip("/")  # Remove trailing slash for consistency

  def _prepare_path(self, path: str = ""):
    """
    Prepare the request path by prepending path_prefix if applicable.

    Args:
        path (str): The request path

    Returns:
        str: The prepared path with path_prefix prefix if configured
    """
    if self.path_prefix and not path.startswith(self.path_prefix):
      # Remove leading slash from path to avoid double slashes
      path = path.lstrip("/")
      return f"{self.path_prefix}/{path}" if path else self.path_prefix
    return path

  def _prepare_kwargs(self, kwargs):
    """
    Prepare request kwargs by setting default content_type if not provided.

    Args:
        kwargs (dict): Request kwargs

    Returns:
        dict: Updated kwargs with default content_type if needed
    """
    if "content_type" not in kwargs:
      kwargs["content_type"] = self.content_type
    return kwargs

  def get(self, path, *args, **kwargs):
    """Make a GET request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().get(path, *args, **kwargs)

  def post(self, path, data=None, *args, **kwargs):
    """Make a POST request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().post(path, data=data, *args, **kwargs)

  def put(self, path, data="", *args, **kwargs):
    """Make a PUT request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().put(path, data=data, *args, **kwargs)

  def patch(self, path, data="", *args, **kwargs):
    """Make a PATCH request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().patch(path, data=data, *args, **kwargs)

  def delete(self, path, *args, **kwargs):
    """Make a DELETE request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().delete(path, *args, **kwargs)

  def head(self, path, *args, **kwargs):
    """Make a HEAD request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().head(path, *args, **kwargs)

  def options(self, path, *args, **kwargs):
    """Make an OPTIONS request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().options(path, *args, **kwargs)

  def trace(self, path, *args, **kwargs):
    """Make a TRACE request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().trace(path, *args, **kwargs)


class APITestCase(TestCase):
  """
  Test case that uses the APIClient by default.
  """

  client_class = APIClient
