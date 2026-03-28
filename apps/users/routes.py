from ninja import Router
from django.http import HttpRequest

from apps.core.schemas.response import BaseAPIResponse
from apps.users.schemas import UpdateUserReq, PartialUpdateUserReq
from apps.authentication.schemas import UserMeRes

router = Router()


@router.put("", response={200: UserMeRes, 400: BaseAPIResponse})
def update_user(request: HttpRequest, body: UpdateUserReq):
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User not authenticated", "success": False}

  user.name = body.name
  if user.email != body.email:
    user.is_email_valid = False  # Set email as invalid if it was changed
  user.email = body.email
  user.phone = body.phone
  user.save()

  return 200, user


@router.patch("", response={200: UserMeRes, 400: BaseAPIResponse})
def partial_update_user(request: HttpRequest, body: PartialUpdateUserReq):
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User not authenticated", "success": False}

  update_data = body.model_dump(exclude_unset=True)

  if "name" in update_data:
    user.name = update_data["name"]
  if "email" in update_data and update_data["email"] is not None:
    if user.email != update_data["email"]:
      user.is_email_valid = False  # Set email as invalid if it was changed
    user.email = update_data["email"]
  if "phone" in update_data:
    user.phone = update_data["phone"]

  user.save()

  return 200, user
