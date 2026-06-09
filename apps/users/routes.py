from ninja import Router, File, Query
from ninja.files import UploadedFile
from django.http import HttpRequest

from apps.core.schemas.response import BaseAPIResponse
from apps.users.services.user import (
  UserService,
  UserEmailAlreadyExistsError,
  UserPhoneAlreadyExistsError,
)
from apps.users.services.user_deletion import UserDeleteService
from apps.users.schemas import UpdateUserReq, PartialUpdateUserReq
from apps.authentication.schemas import UserMeRes

router = Router()


@router.put("", response={200: UserMeRes, 400: BaseAPIResponse})
def update_user(request: HttpRequest, body: UpdateUserReq):
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User not authenticated", "success": False}

  try:
    updated_user = UserService.update_user(user, body)

    return 200, updated_user
  except (UserEmailAlreadyExistsError, UserPhoneAlreadyExistsError) as e:
    return 400, {"details": str(e), "success": False}


@router.patch("", response={200: UserMeRes, 400: BaseAPIResponse})
def partial_update_user(request: HttpRequest, body: PartialUpdateUserReq):
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User not authenticated", "success": False}

  try:
    updated_user = UserService.partial_update_user(user, body)

    return 200, updated_user
  except (UserEmailAlreadyExistsError, UserPhoneAlreadyExistsError) as e:
    return 400, {"details": str(e), "success": False}


@router.post("/profile-photo", response={200: UserMeRes, 400: BaseAPIResponse})
def upload_profile_photo(request: HttpRequest, file: File[UploadedFile]):
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User not authenticated", "success": False}

  if file.content_type not in ["image/jpeg", "image/png"]:
    return 400, {
      "details": "Invalid file type. Should be image, jpeg or png",
      "success": False,
    }

  user.profile_photo = file
  user.save()

  return 200, user


@router.delete("", response={200: BaseAPIResponse, 400: BaseAPIResponse})
def delete_user(request: HttpRequest, verification_code: str | None = Query(None)):
  """
  This routes deletes the User.
  If the verification_code param is given within query string, verify code and
  permanetly deletes user.
  Otherwise, if the verification_code isn't given, send an email to User
  containing the verification code (sends warn email and SMS too).

  """
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User not authenticated", "success": False}

  if verification_code is None or not verification_code:
    UserDeleteService.send_verification_code_email(user)
    UserDeleteService.send_warn_email(user)
    UserDeleteService.send_warn_sms(user)
    # Send warn sms if has method.
    return 200, {"details": "Verification code sent.", "success": True}

  try:
    was_delete = UserDeleteService.delete_user(user, verification_code)
    if not was_delete:
      return 400, {"details": "Invalid verification code.", "success": False}
  except Exception:
    return 500, {
      "details": "Something went wrong during user deletion process.",
      "success": False,
    }

  return 200, {"details": "User account deleted successfully.", "success": True}
