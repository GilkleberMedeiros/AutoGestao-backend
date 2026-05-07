from django.http import HttpRequest, HttpResponse
from django.conf import settings
from django.core.cache import caches

from abc import ABC, abstractmethod
from typing import Callable, Any, AnyStr, Generator, TypedDict, Literal
import re
import json

from apps.authentication.utils.jwt_auth import JWTAuth
from apps.users.models import User


class BaseMiddleware(ABC):
  """
  This class must define and explain the Django Middleware classes Interface.
  """

  @abstractmethod
  def __init__(self, get_response: Callable[[Any], HttpResponse]):
    self.get_response = get_response
    # Runs once in app start (Configuration & Initialization)
    # get_response usually is like the view that proccess the request and returns an response.

  @abstractmethod
  def __call__(self, request: HttpRequest) -> HttpResponse:
    # Runs on every request.

    # Execute code before get response/execute view
    response = self.get_response(request)
    # Execute code after get response/execute view

    return response


class RegexMiddlewareMixin:
  """
  This Mixin provides a method to match routes path using regex.
  """

  @staticmethod
  def get_pattern_match(path_pattern: str | re.Pattern[AnyStr], path: str) -> bool:
    if isinstance(path_pattern, str):
      path_pattern = re.compile(path_pattern)
    return path_pattern.match(path)


class HTTPMethodMiddlewareMixin:
  """
  This Mixin provides methods to match HTTP methods.
  """

  ALL_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

  @staticmethod
  def get_http_method_match(request: HttpRequest, http_methods: list[str]) -> bool:
    for method in http_methods:
      if request.method == method:
        return True

    return False


class RouteSpecification(TypedDict):
  path_pattern: re.Pattern[AnyStr] | str
  http_methods: Literal["*"] | list[str] = "*"


class MatchRouteMiddlewareMixin(RegexMiddlewareMixin, HTTPMethodMiddlewareMixin):
  """
  This high level Mixin provides methods to match routes through regex and HTTP methods.
  _routes param should be either a str (using default ALL_HTTP_METHODS) or a dict as RouteSpecification.
  """

  _routes: list[RouteSpecification | str] = []

  def check_match(self, request: HttpRequest, route_spec: RouteSpecification) -> bool:
    """
    Check if a request matches a route specification. All route checks are made here.
    """
    return self.get_pattern_match(
      route_spec["path_pattern"], request.path
    ) and self.get_http_method_match(request, route_spec["http_methods"])

  def get_routes_match(
    self, request: HttpRequest, routes: list[RouteSpecification | str] = None
  ) -> list[RouteSpecification]:
    matchs = []
    if routes is None:
      routes = self._routes

    for route_spec in self._iter_routes(request, routes):
      m = self.check_match(request, route_spec)
      # Verify if the route matches and the HTTP method is allowed.
      if m:
        matchs.append(route_spec)

    return matchs

  def get_first_route_match(
    self, request: HttpRequest, routes: list[RouteSpecification | str] = None
  ) -> RouteSpecification | None:
    if routes is None:
      routes = self._routes

    for route_spec in self._iter_routes(request, routes):
      m = self.check_match(request, route_spec)
      if m:
        return route_spec

    return None

  def _iter_routes(
    self, request: HttpRequest, routes: list[str | RouteSpecification] = None
  ) -> Generator[RouteSpecification, None, None]:
    """
    Iterate over the routes defined in _routes. Handling its particularities such as:
      - '*' and '["*"]' shorthands that indicates that all HTTP methods are allowed.
      - If a route is not a tuple, it means it's just a route string, in which case
      all HTTP methods are allowed by default.
    """
    if routes is None:
      routes = self._routes

    for route_spec in routes:
      if isinstance(route_spec, str):
        route_spec: RouteSpecification = {
          "path_pattern": route_spec,
          "http_methods": self.ALL_HTTP_METHODS,
        }

      if route_spec["http_methods"] == "*" or route_spec["http_methods"] == ["*"]:
        route_spec = route_spec.copy()
        route_spec["http_methods"] = self.ALL_HTTP_METHODS

      yield route_spec

    return


class JWTAuthenticationMiddleware(BaseMiddleware, MatchRouteMiddlewareMixin):
  _routes = [
    r"^/?api/test-routes/middlewares/jwt-auth-middleware/?$",  # Test route to test this middleware.
    r"^/?api/test-routes/middlewares/valid-email-permission-middleware/?$",
    r"^/?api/users/?$",
    r"^/?api/users/auth/me?$",
    r"^/?api/users/validate/.*$",
    r"^/?api/clients/?$",
    r"^/?api/clients/[a-zA-Z0-9-]+/?$",  # Bind to sub-routes that needs id on path.
    r"^/?api/clients/[a-zA-Z0-9-]+/emails/?$",
    r"^/?api/clients/[a-zA-Z0-9-]+/emails/[a-zA-Z0-9-]+/?$",
    r"^/?api/clients/emails/[a-zA-Z0-9-]+/?$",
    r"^/?api/clients/[a-zA-Z0-9-]+/phones/?$",
    r"^/?api/clients/[a-zA-Z0-9-]+/phones/[a-zA-Z0-9-]+/?$",
    r"^/?api/clients/phones/[a-zA-Z0-9-]+/?$",
    r"^/?api/projects/?$",
    r"^/?api/projects/[a-zA-Z0-9-]+/?$",
    r"^/?api/projects/[a-zA-Z0-9-]+/close/?$",
    r"^/?api/projects/[a-zA-Z0-9-]+/reopen/?$",
    r"^/?api/projects/[a-zA-Z0-9-]+/tasks/?$",
    r"^/?api/projects/[a-zA-Z0-9-]+/tasks/[a-zA-Z0-9-]+/?$",
    r"^/?api/finances/groups/?$",
    r"^/?api/finances/groups/[a-zA-Z0-9-]+/?$",
    r"^/?api/finances/groups/[a-zA-Z0-9-]+/movementations/?$",
    r"^/?api/finances/groups/[a-zA-Z0-9-]+/movementations/[a-zA-Z0-9-]+/?$",
  ]

  def __init__(self, get_response: Callable[[Any], HttpResponse]):
    self.get_response = get_response

  def __call__(self, request: HttpRequest) -> HttpResponse:
    match_route = self.get_first_route_match(request)

    # If not matched route, skip authentication
    if not match_route:
      return self.get_response(request)

    # Try to get token from header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
      return self._deny_request("Authentication token not provided.")
    if not auth_header.startswith("Bearer "):
      return self._deny_request("Authentication token must start with 'Bearer '.")

    access_token = auth_header.replace("Bearer ", "")

    token_value = JWTAuth.verify_token(access_token)
    if not token_value:
      return self._deny_request("Authentication token is invalid or expired.")

    userid = token_value.get("user_id", None)
    if not userid:
      return self._deny_request("User id not found on authentication token.")

    user = None
    try:
      user = User.objects.filter(id=userid).first()
    except Exception:
      return self._deny_request(
        "Couldn't find a User associated with the authentication token."
      )

    if not user:
      return self._deny_request(
        "Couldn't find a User associated with the authentication token."
      )

    request.user = user

    return self.get_response(request)

  def _deny_request(
    self, message: str = "User is not authenticated.", status: int = 401
  ):
    return HttpResponse(
      content=json.dumps({"details": message, "success": False}),
      status=status,
      content_type="application/json",
    )


class ValidEmailPermissionMiddleware(BaseMiddleware, MatchRouteMiddlewareMixin):
  """
  This middleware checks if the user's email is valid.
  If the user's email is not valid, it will return a 400 response.
  This middleware also expect the user to be already authenticated.
  """

  _routes = [
    r"^/?api/test-routes/middlewares/valid-email-permission-middleware/?$",  # Test route to test this middleware.
    r"^/?api/clients/?$",
    r"^/?api/clients/[a-zA-Z0-9-]+/?$",  # Bind to sub-routes that needs id on path.
    r"^/?api/clients/[a-zA-Z0-9-]+/emails/?$",
    r"^/?api/clients/[a-zA-Z0-9-]+/emails/[a-zA-Z0-9-]+/?$",
    r"^/?api/clients/emails/[a-zA-Z0-9-]+/?$",
    r"^/?api/clients/[a-zA-Z0-9-]+/phones/?$",
    r"^/?api/clients/[a-zA-Z0-9-]+/phones/[a-zA-Z0-9-]+/?$",
    r"^/?api/clients/phones/[a-zA-Z0-9-]+/?$",
    r"^/?api/projects/?$",
    r"^/?api/projects/[a-zA-Z0-9-]+/?$",
    r"^/?api/projects/[a-zA-Z0-9-]+/close/?$",
    r"^/?api/projects/[a-zA-Z0-9-]+/reopen/?$",
    r"^/?api/projects/[a-zA-Z0-9-]+/tasks/?$",
    r"^/?api/projects/[a-zA-Z0-9-]+/tasks/[a-zA-Z0-9-]+/?$",
    r"^/?api/finances/groups/?$",
    r"^/?api/finances/groups/[a-zA-Z0-9-]+/?$",
    r"^/?api/finances/groups/[a-zA-Z0-9-]+/movementations/?$",
    r"^/?api/finances/groups/[a-zA-Z0-9-]+/movementations/[a-zA-Z0-9-]+/?$",
  ]

  def __init__(self, get_response: Callable[[Any], HttpResponse]):
    self.get_response = get_response

  def __call__(self, request: HttpRequest) -> HttpResponse:
    match_route = self.get_first_route_match(request)

    if match_route:
      user = request.user
      if not user.is_authenticated:
        return self._deny_request("User is not authenticated.", 401)
      if not user.is_email_valid:
        return self._deny_request("User email is not valid. Permission rejected.", 403)

    response = self.get_response(request)

    return response

  def _deny_request(self, message: str, status: int):
    return HttpResponse(
      content=json.dumps({"details": message, "success": False}),
      status=status,
      content_type="application/json",
    )


class RateLimitRouteSpecification(RouteSpecification):
  time_ms: int


class RateLimitMiddleware(BaseMiddleware, MatchRouteMiddlewareMixin):
  """
  This middleware implements rate-limiting.
  It overrides the mixin methods to support a third parameter: time in milliseconds.
  """

  _routes: list[RateLimitRouteSpecification] = [
    {
      "path_pattern": r"^/?api/test-routes/middlewares/rate-limit-middleware/?$",
      "time_ms": 500,
      "http_methods": "*",
    },
    {
      "path_pattern": r"^/?api/.*?$",
      "time_ms": 500,
      "http_methods": "*",
    },  # 500ms == 2 requests per second
  ]

  # Only apply rate limiting to tests routes if testing is enabled.
  if settings.TESTING:
    _routes = [
      {
        "path_pattern": r"^/?api/test-routes/middlewares/rate-limit-middleware/?$",
        "time_ms": 500,
        "http_methods": "*",
      }
    ]

  def __init__(self, get_response: Callable[[Any], HttpResponse]):
    self.get_response = get_response
    self.cache_db = caches["default"]

  def __call__(self, request: HttpRequest) -> HttpResponse:
    match_route = self.get_first_route_match(request)  # type: ignore

    if match_route is not None and match_route.get("time_ms") is not None:
      # Use User ID, if authenticated, and IP address to identify the user
      user = getattr(request, "user", None)
      ip_address = request.META.get("REMOTE_ADDR", "unknown-ip")
      identifier = self._make_identifier(user, ip_address)

      cache_key = f"rate_limit_{identifier}_{request.path}"

      if self.cache_db.get(cache_key):
        return HttpResponse(
          content=json.dumps({"details": "Too Many Requests", "success": False}),
          status=429,
          content_type="application/json",
        )
      else:
        # Cache timeout expects seconds (can be fractional like 0.5s for 500ms)
        self.cache_db.set(cache_key, 1, timeout=match_route["time_ms"] / 1000.0)

    response = self.get_response(request)
    return response

  def _make_identifier(self, user: User | None, ip_address: str) -> str:
    """Make request identifier string."""
    if user is not None and user.is_authenticated:
      return f"RequestID(user_id={user.id}, ip_address={ip_address})"
    return f"RequestID(ip_address={ip_address})"

  def get_first_route_match(
    self, request: HttpRequest, routes: list[RateLimitRouteSpecification] | None = None
  ) -> RateLimitRouteSpecification | None:
    return super().get_first_route_match(request, routes)
