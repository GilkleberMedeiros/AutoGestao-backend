from django.http import HttpRequest, HttpResponse
from django.core.cache import caches
from django.conf import settings

from abc import ABC, abstractmethod
from typing import Callable, Any, AnyStr
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

  def get_routes_match(self, request: HttpRequest) -> list[re.Match[AnyStr]]:
    matchs = []

    for route, http_methods in self._iter_routes(request):
      m = re.match(route, request.path)
      # Verify if the route matches and the HTTP method is allowed.
      if m and self.get_http_method_match(request, http_methods):
        matchs.append(m)

    return matchs

  def get_first_route_match(self, request: HttpRequest) -> re.Match[AnyStr] | None:
    for route, http_methods in self._iter_routes(request):
      m = re.match(route, request.path)
      # Verify if the route matches and the HTTP method is allowed.
      if m and self.get_http_method_match(request, http_methods):
        return m

    return None

  def _iter_routes(self, request: HttpRequest) -> HttpResponse:
    routes_len = len(self._routes)

    if routes_len == 0:
      return

    if isinstance(self._routes[0], tuple):
      for route, http_methods in self._routes:
        yield route, http_methods
    else:
      for route in self._routes:
        yield route, ["GET", "POST", "PUT", "PATCH", "DELETE"]

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
    r"^/?api/fingroups/?$",
    r"^/?api/fingroups/[a-zA-Z0-9-/]+/?$",
    r"^/?api/dashboard/?$",
    r"^/?api/dashboard/[a-zA-Z0-9-/]+/?$",
    r"^/?api/notifications/?$",
    r"^/?api/notifications/[a-zA-Z0-9-/]+/?$",
  ]

  def __init__(self, get_response: Callable[[Any], HttpResponse]):
    self.get_response = get_response

  def __call__(self, request: HttpRequest) -> HttpResponse:
    match_route = self.get_first_route_match(request)

    # If got a listed route match try to get token
    auth_header = ""
    if match_route:
      auth_header = request.headers.get("Authorization", "")

    access_token = ""
    if auth_header and auth_header.startswith("Bearer "):
      access_token = auth_header.replace("Bearer ", "")

    token_value = None
    if access_token:
      try:
        token_value = JWTAuth.verify_token(access_token)
      except Exception:
        pass

    userid = None
    if token_value:
      userid = token_value.get("user_id", None)

    user = None
    if userid:
      try:
        user = User.objects.filter(id=userid).first()
      except Exception:
        return self.get_response(request)

    if user:
      request.user = user

    response = self.get_response(request)

    return response


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
    r"^/?api/fingroups/?$",
    r"^/?api/fingroups/[a-zA-Z0-9-/]+/?$",
    r"^/?api/dashboard/?$",
    r"^/?api/dashboard/[a-zA-Z0-9-/]+/?$",
    r"^/?api/notifications/?$",
    r"^/?api/notifications/[a-zA-Z0-9-/]+/?$",
  ]

  def __init__(self, get_response: Callable[[Any], HttpResponse]):
    self.get_response = get_response

  def __call__(self, request: HttpRequest) -> HttpResponse:
    match_route = self.get_first_route_match(request)

    if match_route:
      user = request.user
      if not user.is_authenticated:
        return HttpResponse(
          content=json.dumps({"details": "User not authenticated", "success": False}),
          status=401,
          content_type="application/json",
        )
      if not user.is_email_valid:
        return HttpResponse(
          content=json.dumps(
            {"details": "User email not valid. Permission rejected.", "success": False}
          ),
          status=403,
          content_type="application/json",
        )

    response = self.get_response(request)

    return response


class RateLimitMiddleware(BaseMiddleware, MatchRouteMiddlewareMixin):
  """
  This middleware implements rate-limiting.
  It overrides the mixin methods to support a third parameter: time in milliseconds.
  """

  _routes: list[tuple[str, list[str], int]] = [
    (
      r"^/?api/test-routes/middlewares/rate-limit-middleware/?$",
      ["GET", "POST", "PUT", "PATCH", "DELETE"],
      500,
    ),
    (
      r"^/?api/.*?$",
      ["GET", "POST", "PUT", "PATCH", "DELETE"],
      500,
    ),  # 500ms == 2 requests per second
  ]

  # Remove API Prod routes rate limiting if on test/dev
  if settings.DEBUG or settings.TESTING:
    _routes = [
      (
        r"^/?api/test-routes/middlewares/rate-limit-middleware/?$",
        ["GET", "POST", "PUT", "PATCH", "DELETE"],
        500,
      )
    ]

  def _iter_routes(self, request: HttpRequest):
    if not self._routes:
      return

    for route_info in self._routes:
      if len(route_info) == 3:
        route, http_methods, rate_limit_ms = route_info
        yield route, http_methods, rate_limit_ms

  def get_first_route_match_with_limit(
    self, request: HttpRequest
  ) -> tuple[re.Match[AnyStr], int] | tuple[None, None]:
    for route, http_methods, rate_limit_ms in self._iter_routes(request):
      m = re.match(route, request.path)
      if m and self.get_http_method_match(request, http_methods):
        return m, rate_limit_ms

    return None, None

  def __init__(self, get_response: Callable[[Any], HttpResponse]):
    self.get_response = get_response
    self.cache_db = caches["default"]

    # Remove API Prod routes rate limiting if not on test/dev
    if not settings.DEBUG and not settings.TESTING:
      self._routes = [
        (
          r"^/?api/test-routes/middlewares/rate-limit-middleware/?$",
          ["GET", "POST", "PUT", "PATCH", "DELETE"],
          500,
        )
      ]

  def __call__(self, request: HttpRequest) -> HttpResponse:
    match_route, rate_limit_ms = self.get_first_route_match_with_limit(request)  # type: ignore

    if match_route is not None and rate_limit_ms is not None:
      # Use User ID if authenticated, else IP address
      user = getattr(request, "user", None)
      identifier = (
        str(user.id)
        if user and user.is_authenticated
        else request.META.get("REMOTE_ADDR", "unknown")
      )

      cache_key = f"rate_limit_{identifier}_{request.path}"

      if self.cache_db.get(cache_key):
        return HttpResponse(
          content=json.dumps({"details": "Too Many Requests", "success": False}),
          status=429,
          content_type="application/json",
        )
      else:
        # Cache timeout expects seconds (can be fractional like 0.5s for 500ms)
        self.cache_db.set(cache_key, 1, timeout=rate_limit_ms / 1000.0)

    response = self.get_response(request)
    return response
