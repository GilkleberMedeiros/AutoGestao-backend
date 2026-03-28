from django.http import HttpRequest, HttpResponse

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


class JWTAuthenticationMiddleware(BaseMiddleware, RegexMiddlewareMixin):
  authenticate_routes = [
    r"^/?api/test-routes/middlewares/jwt-auth-middleware/?$",  # Test route to test this middleware.
    r"^/?api/test-routes/middlewares/valid-email-permission-middleware/?$",
    r"^/?api/users/auth/me?$",
    r"^/?api/users/validate/.*$",
  ]

  def __init__(self, get_response: Callable[[Any], HttpResponse]):
    self.get_response = get_response

  def __call__(self, request: HttpRequest) -> HttpResponse:
    path = request.path
    match_route = self.get_first_route_match(self.authenticate_routes, path)

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


class ValidEmailPermissionMiddleware(BaseMiddleware, RegexMiddlewareMixin):
  """
  This middleware checks if the user's email is valid.
  If the user's email is not valid, it will return a 400 response.
  This middleware also expect the user to be already authenticated.
  """

  valid_email_routes = [
    r"^/?api/test-routes/middlewares/valid-email-permission-middleware/?$",  # Test route to test this middleware.
  ]

  def __init__(self, get_response: Callable[[Any], HttpResponse]):
    self.get_response = get_response

  def __call__(self, request: HttpRequest) -> HttpResponse:
    path = request.path
    match_route = self.get_first_route_match(self.valid_email_routes, path)

    if match_route:
      user = request.user
      if not user.is_authenticated:
        return HttpResponse(
          content=json.dumps({"details": "User not authenticated", "success": False}),
          status=401,
          content_type="application/json"
        )
      if not user.is_email_valid:
        return HttpResponse(
          content=json.dumps(
            {"details": "User email not valid. Permission rejected.", "success": False}
          ),
          status=403,
          content_type="application/json"
        )

    response = self.get_response(request)

    return response
