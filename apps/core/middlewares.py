from django.http import HttpRequest, HttpResponse

from abc import ABC, abstractmethod
from typing import Callable, Any, AnyStr, Tuple, Generator
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
  This Mixin provides methods to match routes using regex.
  """

  @staticmethod
  def get_routes_match(routes: list[str], path: str) -> list[re.Match[AnyStr]]:
    matchs = []

    for route in routes:
      m = re.match(route, path)
      if m:
        matchs.append(m)

    return matchs

  @staticmethod
  def get_first_route_match(routes: list[str], path: str) -> re.Match[AnyStr] | None:
    for route in routes:
      m = re.match(route, path)
      if m:
        return m

    return None


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


class MatchRouteMiddlewareMixin(RegexMiddlewareMixin, HTTPMethodMiddlewareMixin):
  """
  This high level Mixin provides methods to match routes through regex and HTTP methods.
  """

  _routes: list[tuple[str, list[str]]] | list[str] = []

  def get_routes_match(
    self, request: HttpRequest, routes: list[str | tuple[str, list[str]]] = None
  ) -> list[re.Match[AnyStr]]:
    matchs = []
    if routes is None:
      routes = self._routes

    for route, http_methods in self._iter_routes(request):
      m = re.match(route, request.path)
      # Verify if the route matches and the HTTP method is allowed.
      if m and self.get_http_method_match(request, http_methods):
        matchs.append(m)

    return matchs

  def get_first_route_match(
    self, request: HttpRequest, routes: list[str | tuple[str, list[str]]] = None
  ) -> re.Match[AnyStr] | None:
    if routes is None:
      routes = self._routes

    for route, http_methods in self._iter_routes(request):
      m = re.match(route, request.path)
      # Verify if the route matches and the HTTP method is allowed.
      if m and self.get_http_method_match(request, http_methods):
        return m

    return None

  def _iter_routes(
    self, request: HttpRequest, routes: list[str | tuple[str, list[str]]] = None
  ) -> Generator[Tuple[str, list[str]], None, None]:
    """
    Iterate over the routes defined in _routes. Handling its particularities such as:
      - '*' and '["*"]' shorthands that indicates that all HTTP methods are allowed.
      - If a route is not a tuple, it means it's just a route string, in which case
      all HTTP methods are allowed by default.
    """
    if routes is None:
      routes = self._routes

    routes_len = len(routes)

    if routes_len == 0:
      return

    for route_spec in routes:
      if isinstance(route_spec, tuple):
        route, http_methods = route_spec

        # '*' and '["*"]' are shorthands to indicate that all HTTP methods are allowed.
        if http_methods == "*" or http_methods == ["*"]:
          yield route, self.ALL_HTTP_METHODS
          continue

        yield route_spec
      # If route_spec is not a tuple, it means it's just a route string.
      # So we yield it with a default list of HTTP methods.
      else:
        yield route_spec, self.ALL_HTTP_METHODS

    return


class JWTAuthenticationMiddleware(BaseMiddleware, MatchRouteMiddlewareMixin):
  _routes = [
    r"^/?api/test-routes/middlewares/jwt-auth-middleware/?$",  # Test route to test this middleware.
    r"^/?api/test-routes/middlewares/valid-email-permission-middleware/?$",
    r"^/?api/users/?$",
    r"^/?api/users/auth/me?$",
    r"^/?api/users/validate/.*$",
    r"^/?api/clients/?$",
    r"^/?api/clients/[a-zA-Z0-9-/]+/?$",  # Bind to sub-routes that needs id on path.
    r"^/?api/projects/?$",
    r"^/?api/projects/[a-zA-Z0-9-/]+/?$",
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
    r"^/?api/clients/[a-zA-Z0-9-/]+/?$",  # Bind to sub-routes that needs id on path.
    r"^/?api/projects/?$",
    r"^/?api/projects/[a-zA-Z0-9-/]+/?$",
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
