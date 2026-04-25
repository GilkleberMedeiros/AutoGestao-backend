from ninja import Router
from django.http import HttpRequest

from apps.core.schemas.response import BaseAPIResponse
from apps.users.schemas import UpdateUserReq, PartialUpdateUserReq
from apps.users.service import UserService
from apps.authentication.schemas import UserMeRes

router = Router()


@router.put("", response={200: UserMeRes, 400: BaseAPIResponse})
def update_user(request: HttpRequest, body: UpdateUserReq):
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User not authenticated", "success": False}

  updated_user = UserService.update_user(user, body)

  return 200, updated_user


@router.patch("", response={200: UserMeRes, 400: BaseAPIResponse})
def partial_update_user(request: HttpRequest, body: PartialUpdateUserReq):
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User not authenticated", "success": False}

  updated_user = UserService.partial_update_user(user, body)

  return 200, updated_user
