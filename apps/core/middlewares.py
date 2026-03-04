from django.http import HttpRequest, HttpResponse

from abc import ABC, abstractmethod
from typing import Callable, Any
import re

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


class JWTAuthenticationMiddleware(BaseMiddleware):
  authenticate_routes = [
    r"^/?api/test-routes/middlewares/jwt-auth-middleware/?$",  # Test route to test this middleware.
  ]

  def __init__(self, get_response: Callable[[Any], HttpResponse]):
    self.get_response = get_response

  def __call__(self, request: HttpRequest) -> HttpResponse:
    path = request.path
    match_route = None
    for route in self.authenticate_routes:
      m = re.match(route, path)
      if m:
        match_route = m
        break

    # If got a listed route match try to get token
    access_token = ""
    if match_route:
      access_token = request.headers.get("Authorization", "").replace("Bearer ", "")

    try:
      token_value = JWTAuth.verify_token(access_token)
    except Exception:
      return self.get_response(request)

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
