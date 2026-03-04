"""
Base Test Client for API Testing.
"""

from django.test import Client, TestCase


class APIClient(Client):
  r"""
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

  def get(self, path: str = "", *args, **kwargs):
    """Make a GET request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().get(path, *args, **kwargs)

  def post(self, path: str = "", data=None, *args, **kwargs):
    """Make a POST request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().post(path, data=data, *args, **kwargs)

  def put(self, path: str = "", data="", *args, **kwargs):
    """Make a PUT request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().put(path, data=data, *args, **kwargs)

  def patch(self, path: str = "", data="", *args, **kwargs):
    """Make a PATCH request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().patch(path, data=data, *args, **kwargs)

  def delete(self, path: str = "", *args, **kwargs):
    """Make a DELETE request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().delete(path, *args, **kwargs)

  def head(self, path: str = "", *args, **kwargs):
    """Make a HEAD request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().head(path, *args, **kwargs)

  def options(self, path: str = "", *args, **kwargs):
    """Make an OPTIONS request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().options(path, *args, **kwargs)

  def trace(self, path: str = "", *args, **kwargs):
    """Make a TRACE request with default content_type."""
    path = self._prepare_path(path)
    kwargs = self._prepare_kwargs(kwargs)
    return super().trace(path, *args, **kwargs)


class APITestCase(TestCase):
  """
  Test case that uses the APIClient by default.
  """

  client_class = APIClient


class JWTAuthenticatedTestCaseMixin:
  """
  Automanages jwt authentication for testing.

  This mixin provides automatic setup and teardown of JWT authentication
  for test cases. It:
  - Logs in before each test using login_data
  - Stores the login response and credentials
  - Logs out after each test

  Usage:
    class MyAuthenticatedTestCase(JWTAuthenticatedTestCaseMixin):
      login_data = {"email": "test@example.com", "password": "password"}

      def test_authenticated_endpoint(self):
        # setUpAuth is called automatically
        # Use self.credentials to access tokens
        self.assertIsNotNone(self.credentials["access"])
  """

  client_class = APIClient

  login_url = "/api/users/auth/login"
  logout_url = "/api/users/auth/logout"
  login_data = None

  # Will be set during setUpAuth
  login_response = None
  credentials = None

  @classmethod
  def setUpClassAuth(cls):
    """
    Log in and store credentials for authenticated tests.

    This method:
    - Sends login request with login_data
    - Extracts and stores the access token from response
    - Extracts and stores the refresh token from cookies
    - Stores the full login response

    Raises:
      AssertionError: If login fails or credentials cannot be extracted
    """
    cls.client = cls.client_class()

    if not cls.login_data:
      raise AssertionError(
        "login_data must be defined on the test case to use setUpAuth"
      )

    cls.login_response = cls.client.post(cls.login_url, cls.login_data)

    if cls.login_response.status_code != 200:
      raise AssertionError(
        f"Login failed with status code {cls.login_response.status_code}. "
        f"Response: {cls.login_response.json()}"
      )

    cls.credentials = cls._extract_credentials(cls.login_response)
    cls.credentials["refresh"] = cls.credentials["refresh"].value

    if not cls.credentials.get("access"):
      raise AssertionError("Could not extract access token from login response")

    if not cls.credentials.get("refresh"):
      raise AssertionError("Could not extract refresh token from login response")

  @classmethod
  def tearDownClassAuth(cls):
    """
    Log out and clean up authentication.

    This method sends a logout request to invalidate the session.
    It does not raise exceptions if logout fails to avoid masking
    test assertion errors.
    """
    cls.client = cls.client_class()

    try:
      logout_response = cls.client.get(cls.logout_url)

      if logout_response.status_code != 200:
        print(f"Warning: Logout returned status code {logout_response.status_code}")
    except Exception as e:
      print(f"Warning: Error during logout: {e}")
    finally:
      cls.login_response = None
      cls.credentials = None

  def setUpAuth(self):
    return self.setUpClassAuth()

  def tearDownAuth(self):
    """
    Log out and clean up authentication.

    This method sends a logout request to invalidate the session.
    It does not raise exceptions if logout fails to avoid masking
    test assertion errors.
    """
    self.tearDownClassAuth()

  @staticmethod
  def _extract_credentials(response):
    """
    Extract JWT credentials from login response.

    Args:
      response: Django test client response from login endpoint

    Returns:
      dict: Dictionary with 'access' and 'refresh' tokens

    Raises:
      AssertionError: If response data is not in expected format
    """
    response_data = response.json()

    if not isinstance(response_data, dict):
      raise AssertionError(f"Login response is not a dict. Got {type(response_data)}")

    access_token = response_data.get("access")
    refresh_token = response.cookies.get("refresh_token")

    return {
      "access": access_token,
      "refresh": refresh_token,
    }


class AuthenticatedTestCase(APITestCase, JWTAuthenticatedTestCaseMixin):
  """
  Automanages authentication and user creation for testing.

  This test case combines APITestCase and JWTAuthenticatedTestCaseMixin to provide:
  - Automatic user creation and deletion
  - Automatic JWT authentication for each test
  - APIClient with sensible defaults

  Set:
    - self.setUpUser or cls.setUpClassUser to set up user before authenticating.
    - self.setUpAuth or cls.setUpClassAuth to set up authentication.
    - self.tearDownAuth or cls.tearDownClassAuth to tear down authentication.
    - self.tearDownUser or cls.tearDownClassUser to delete created user.

  Usage:
    class MyAuthenticatedTestCase(AuthenticatedTestCase):
      def test_authenticated_endpoint(self):
        # User is automatically created
        # Credentials are automatically set in setUp
        response = self.client.get(
          "/api/protected-endpoint",
          headers={"Authorization": f"Bearer {self.credentials['access']}"}
        )
        self.assertEqual(response.status_code, 200)
  """

  # Should be set by subclass
  user_create_data = None
  user_create_model = None

  login_data = None

  # Will be set after setUpClass
  user = None

  @classmethod
  def setUpClassUser(cls):
    """Create test user for authentication."""
    try:
      cls.user = cls.user_create_model.objects.create_user(**cls.user_create_data)
    except Exception as e:
      raise Exception(f"Error creating user for {cls.__name__}!\nException: {e}")

  @classmethod
  def tearDownClassUser(cls):
    """Delete test user created in setUpClassUser."""
    try:
      if cls.user:
        cls.user.delete()
    except Exception as e:
      print(f"Warning: Error deleting user in {cls.__name__}: {e}")

  def setUpUser(self):
    self.setUpClassUser()

  def tearDownUser(self):
    self.tearDownClassUser()
