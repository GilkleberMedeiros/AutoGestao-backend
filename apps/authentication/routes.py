from ninja import Router
from django.http import HttpRequest, HttpResponse
from django.utils.timezone import get_current_timezone
from datetime import datetime

from apps.core.schemas.response import BaseAPIResponse
from config.settings import SIMPLE_JWT
from apps.users.models import User
from .schemas import LoginReq, RegisterReq, UserMeRes, AccessTokenRes
from .utils.jwt_auth import JWTAuth


router = Router()


@router.post("/login", response={200: AccessTokenRes, 400: BaseAPIResponse})
def login(request: HttpRequest, response: HttpResponse, body: LoginReq):
  user = User.objects.filter(email=body.email).first()
  if not user or not user.check_password(body.password):
    return 400, {"details": "Invalid credentials", "success": False}

  tokens = JWTAuth.create_tokens(user)
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

  # Validate email is unique
  if User.objects.filter(email=body.email).exists():
    return 400, {"details": "Email already exists", "success": False}

  # Validate phone is unique
  if body.phone and User.objects.filter(phone=body.phone).exists():
    return 400, {"details": "Phone already exists", "success": False}

  try:
    User.objects.create_user(
      name=body.name,
      email=body.email,
      password=body.password,
      phone=body.phone,
    )
  except Exception as _:
    return 500, {"details": "Unknow Error when creating user", "success": False}

  return 201, {"details": "User created successfully", "success": True}


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

  if not refresh_token:
    return 400, {"details": "Refresh token not provided", "success": False}

  decoded = JWTAuth.verify_token(refresh_token)
  if not decoded:
    return 400, {"details": "Invalid refresh token", "success": False}

  user = User.objects.get(id=decoded["user_id"])
  tokens = JWTAuth.create_tokens(user)
  access_token = {"access": tokens["access"]}

  return 200, access_token  # Only return Acess Token on refresh


@router.get("/me", response={200: UserMeRes, 400: BaseAPIResponse})
def me(request: HttpRequest, response: HttpResponse):
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User not found", "success": False}
  user: User = user

  return 200, user
