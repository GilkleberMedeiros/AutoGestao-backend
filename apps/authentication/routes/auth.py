from ninja import Router
from django.http import HttpRequest, HttpResponse
from django.utils.timezone import get_current_timezone
from datetime import datetime

from apps.core.schemas.response import BaseAPIResponse
from config.settings import SIMPLE_JWT
from apps.users.models import User
from apps.authentication.schemas import LoginReq, RegisterReq, UserMeRes, AccessTokenRes
from apps.authentication.services.email_validation import EmailValidationService
from apps.authentication.services.auth import (
  AuthService,
  UserInvalidCredentialsError,
  UserEmailAlreadyExistsError,
  UserPhoneAlreadyExistsError,
  MissingRefreshTokenError,
  InvalidRefreshTokenError,
)


router = Router()


@router.post("/login", response={200: AccessTokenRes, 400: BaseAPIResponse})
def login(request: HttpRequest, response: HttpResponse, body: LoginReq):

  try:
    tokens = AuthService.login(body)
  except UserInvalidCredentialsError:
    return 400, {"details": "User credentials are invalid", "success": False}
  except Exception:
    return 500, {"details": "Unknown Error when logging in", "success": False}

  tz = get_current_timezone()
  response.set_cookie(
    "refresh_token",
    tokens["refresh"],
    httponly=True,
    expires=SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] + datetime.now(tz),
  )
  token = {
    "access": tokens["access"]
  }  # Return only access token on login, refresh token is stored in HttpOnly cookie

  return 200, token


@router.post(
  "/register",
  response={201: BaseAPIResponse, 400: BaseAPIResponse, 500: BaseAPIResponse},
)
def register(request: HttpRequest, response: HttpResponse, body: RegisterReq):
  """
  Register a new user.
  Try sending an validation email for user immediately after registration.
  """

  try:
    user = AuthService.register(body)
  except UserEmailAlreadyExistsError:
    return 400, {"details": "User email already exists", "success": False}
  except UserPhoneAlreadyExistsError:
    return 400, {"details": "User phone already exists", "success": False}
  except Exception:
    return 500, {"details": "Unknown Error when registering user", "success": False}

  # Send validation email for user immediately after registration
  try:
    EmailValidationService.send_validation_email(request, user)
  except Exception as _:
    return 201, {
      "details": "User created successfully! "
      "But failed to send validation email. "
      "Request an email validation attempt.",
      "success": True,
    }

  return 201, {
    "details": "User created successfully! Sent Validation Email.",
    "success": True,
  }


@router.get("/logout", response={200: BaseAPIResponse})
def logout(request: HttpRequest, response: HttpResponse):
  response.delete_cookie("refresh_token")
  return 200, {"details": "Logged out successfully", "success": True}


@router.get(
  "/refresh",
  response={200: AccessTokenRes, 400: BaseAPIResponse},
)
def refresh(request: HttpRequest, response: HttpResponse):
  refresh_token = request.COOKIES.get("refresh_token")

  try:
    tokens = AuthService.refresh(refresh_token)
  except InvalidRefreshTokenError:
    return 400, {"details": "Invalid refresh token", "success": False}
  except MissingRefreshTokenError:
    return 400, {"details": "Missing refresh token", "success": False}
  except Exception:
    return 500, {"details": "Unknown Error when refreshing token", "success": False}

  access_token = {"access": tokens["access"]}

  return 200, access_token  # Only return Acess Token on refresh


@router.get("/me", response={200: UserMeRes, 400: BaseAPIResponse})
def me(request: HttpRequest, response: HttpResponse):
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User not found", "success": False}
  user: User = user

  return 200, user
