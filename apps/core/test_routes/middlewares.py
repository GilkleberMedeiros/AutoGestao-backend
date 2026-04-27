"""
Routes with the only purposes to tests middlewares!
"""

from ninja import Router
from django.http import HttpRequest

from apps.core.schemas.response import BaseAPIResponse


router = Router()


@router.get(
  "jwt-auth-middleware/", response={200: BaseAPIResponse, 400: BaseAPIResponse}
)
def test_jwt_auth_middleware(request: HttpRequest):
  if not request.user.is_authenticated:
    return 400, {"details": "not-authenticated", "success": False}

  return 200, {"details": f"authenticated-{request.user.id}", "success": True}


@router.get(
  "valid-email-permission-middleware/",
  response={200: BaseAPIResponse, 400: BaseAPIResponse},
)
def test_valid_email_permission_middleware(request: HttpRequest):
  if not request.user.is_authenticated:
    return 400, {"details": "not-authenticated", "success": False}
  if not request.user.is_email_valid:
    return 400, {"details": "email-not-valid", "success": False}

  return 200, {"details": f"email-valid-{request.user.id}", "success": True}


@router.get(
  "rate-limit-middleware/",
  response={200: BaseAPIResponse, 429: BaseAPIResponse},
)
def test_rate_limit_middleware(request: HttpRequest):
  return 200, {"details": "rate-limit-passed", "success": True}
