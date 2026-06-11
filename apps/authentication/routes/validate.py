"""
Routes for email & Phone validation.
"""

from ninja import Router
from django.http import HttpRequest

from apps.core.schemas.response import BaseAPIResponse
from apps.core.exceptions import ExternalServiceError
from apps.authentication.services.email_validation import EmailValidationService
from apps.users.models import User
from apps.authentication.services.phone_validation import PhoneValidationService

router = Router(
  tags=["Authentication", "Validate"],
)


@router.post(
  "/request-validation/email",
  response={200: BaseAPIResponse, 400: BaseAPIResponse, 500: BaseAPIResponse},
)
def request_email_validation(request: HttpRequest):
  user: User = request.user
  if not user.is_authenticated:
    return 400, {"details": "User is not authenticated.", "success": False}

  if user.is_email_valid:
    return 200, {"details": "User email is already validated.", "success": True}

  validation_manager = EmailValidationService()

  try:
    _ = validation_manager.send_validation_email(user)
  except ExternalServiceError:
    return 500, {"details": "Failed to send validation email.", "success": False}

  return 200, {"details": "Validation email sent successfully.", "success": True}


@router.post(
  "/request-validation/phone",
  response={200: BaseAPIResponse, 400: BaseAPIResponse, 500: BaseAPIResponse},
)
def request_phone_validation(request: HttpRequest):
  user: User = request.user
  if not user.is_authenticated:
    return 400, {"details": "User is not authenticated.", "success": False}

  if user.is_phone_valid:
    return 200, {"details": "User phone is already validated.", "success": True}

  validation_manager = PhoneValidationService()

  try:
    _ = validation_manager.send_validation_sms(user)
  except ExternalServiceError:
    return 500, {"details": "Failed to send validation sms.", "success": False}

  return 200, {"details": "Validation sms sent successfully.", "success": True}


@router.post(
  "/email/{validation_token}",
  response={200: BaseAPIResponse, 400: BaseAPIResponse, 500: BaseAPIResponse},
)
def validate_email(request: HttpRequest, validation_token: str):
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User is not authenticated.", "success": False}

  if user.is_email_valid:
    return 200, {"details": "User email is already validated.", "success": True}

  validation_manager = EmailValidationService()

  try:
    token_valid = validation_manager.validate_user_email(user, validation_token)
  except ExternalServiceError:
    return 500, {"details": "Failed to save validation status.", "success": False}

  if not token_valid:
    return 400, {"details": "Invalid validation token.", "success": False}

  return 200, {"details": "Email validated successfully.", "success": True}


@router.post(
  "/phone/{validation_token}",
  response={200: BaseAPIResponse, 400: BaseAPIResponse, 500: BaseAPIResponse},
)
def validate_phone(request: HttpRequest, validation_token: str):
  user = request.user
  if not user.is_authenticated:
    return 400, {"details": "User is not authenticated.", "success": False}

  if user.is_phone_valid:
    return 200, {"details": "User phone is already validated.", "success": True}

  validation_manager = PhoneValidationService()

  try:
    token_valid = validation_manager.validate_user_phone(user, validation_token)
  except ExternalServiceError:
    return 500, {"details": "Failed to save validation status.", "success": False}

  if not token_valid:
    return 400, {"details": "Invalid validation token.", "success": False}

  return 200, {"details": "Phone validated successfully.", "success": True}
