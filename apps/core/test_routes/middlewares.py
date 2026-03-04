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
