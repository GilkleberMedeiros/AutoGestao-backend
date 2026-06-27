from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Body

from apps.core.exceptions import AppError, ResourceNotFoundError
from apps.core.schemas.response import BaseAPIResponse

from .schemas import (
  SyncRequestSchema,
  SyncResponseSchema,
  CreateNotificationReq,
  PartialUpdateNotificationReq,
  NotificationSchema,
)
from .services import NotificationService

router = Router()


@router.post(
  "sync",
  response={200: SyncResponseSchema, 400: BaseAPIResponse, 500: BaseAPIResponse},
  summary="Synchronize notifications",
  description="Filters and returns notifications not already known by the client",
)
def sync(request: HttpRequest, body: SyncRequestSchema = Body(...)):
  """
  Retrieve filtered notifications for authenticated user.

  Endpoint: POST /notifications/sync
  Authentication: Required
  Response: List of notifications excluding known IDs, ordered by delivery time

  Args:
      request: HTTP request with authenticated user
      body: SyncRequestSchema with optional known_notification_ids

  Returns:
      SyncResponseSchema with filtered notifications

  Raises:
      ValidationError: For invalid request payload (handled by Django Ninja)
  """
  known_ids = [UUID(id_str) for id_str in (body.known_notification_ids or [])]

  try:
    notifications = NotificationService.sync(request.user, known_ids)

    return 200, {
      "notifications": [
        {
          "id": notification.id,
          "title": notification.title,
          "message": notification.message,
          "read": notification.read,
          "deliver_at": notification.deliver_at,
          "type": notification.type,
          "extra_fields": notification.extra_fields,
          "relation": notification.notificationrelation_set.first(),
        }
        for notification in notifications
      ]
    }
  except ValueError:
    return 400, {
      "details": "known_notification_ids list exceeds maximum allowed size",
      "success": False,
    }
  except Exception:
    return 500, {"details": "Unknown error occurred", "success": False}


@router.post(
  path="",
  response={
    201: NotificationSchema,
    404: BaseAPIResponse,
    400: BaseAPIResponse,
    500: BaseAPIResponse,
  },
  summary="Create a new notification",
)
def create_notification(request: HttpRequest, body: CreateNotificationReq):
  """
  Create a new notification for the authenticated user.

  Endpoint: POST /notifications
  Authentication: Required
  Request Body: CreateNotificationReq with title, deliver_at, optional message and relation

  Args:
      request: HTTP request with authenticated user
      body: CreateNotificationReq with notification details

  Returns:
      NotificationDTO with created notification details

  Raises:
      BusinessRuleError: For invalid relation type or missing required relation details
      ResourceNotFoundError: If the related entity does not exist
      ValidationError: For invalid request payload (handled by Django Ninja)
  """
  try:
    notification = NotificationService.create(
      request.user, body.model_dump(exclude_unset=True)
    )
    return 201, {
      "id": notification.id,
      "title": notification.title,
      "message": notification.message,
      "read": notification.read,
      "deliver_at": notification.deliver_at,
      "type": notification.type,
      "extra_fields": notification.extra_fields,
      "relation": notification.notificationrelation_set.first(),
    }
  except ResourceNotFoundError as e:
    return 404, {"details": str(e), "success": False}
  except AppError as e:
    return 400, {"details": str(e), "success": False}
  except Exception:
    return 500, {"details": "Unknown error occurred", "success": False}


@router.patch(
  path="{notification_id}",
  response={
    200: NotificationSchema,
    404: BaseAPIResponse,
    400: BaseAPIResponse,
    500: BaseAPIResponse,
  },
  summary="Update an existing notification",
)
def update_notification(
  request: HttpRequest, notification_id: str, body: PartialUpdateNotificationReq
):
  """
  Partially update an existing notification for the authenticated user.

  Endpoint: PATCH /notifications/{notification_id}
  Authentication: Required
  Request Body: PartialUpdateNotificationReq with fields to update

  Args:
      request: HTTP request with authenticated user
      notification_id: ID of the notification to update
      body: PartialUpdateNotificationReq with fields to update

  Returns:
      NotificationDTO with updated notification details

  Raises:
      ResourceNotFoundError: If the notification does not exist for the user
      ValidationError: For invalid request payload (handled by Django Ninja)
  """
  try:
    updated_notification = NotificationService.partial_update(
      request.user, notification_id, body.model_dump(exclude_unset=True)
    )
    return {
      "id": updated_notification.id,
      "title": updated_notification.title,
      "message": updated_notification.message,
      "read": updated_notification.read,
      "deliver_at": updated_notification.deliver_at,
      "type": updated_notification.type,
      "extra_fields": updated_notification.extra_fields,
      "relation": updated_notification.notificationrelation_set.first(),
    }
  except ResourceNotFoundError as e:
    return 404, {"details": str(e), "success": False}
  except AppError as e:
    return 400, {"details": str(e), "success": False}
  except Exception:
    return 500, {"details": "Unknown error occurred", "success": False}


@router.delete(
  path="{notification_id}",
  response={
    200: BaseAPIResponse,
    404: BaseAPIResponse,
    400: BaseAPIResponse,
    500: BaseAPIResponse,
  },
  summary="Delete a notification",
)
def delete_notification(request: HttpRequest, notification_id: str):
  """
  Delete a notification for the authenticated user.

  Endpoint: DELETE /notifications/{notification_id}
  Authentication: Required

  Args:
      request: HTTP request with authenticated user
      notification_id: ID of the notification to delete

  Returns:
      BaseAPIResponse indicating success or failure

  Raises:
      ResourceNotFoundError: If the notification does not exist for the user
  """
  try:
    result = NotificationService.delete(request.user, notification_id)
    result.update({"details": "Notification deleted successfully."})
    return result
  except ResourceNotFoundError as e:
    return 404, {"details": str(e), "success": False}
  except AppError as e:
    return 400, {"details": str(e), "success": False}
  except Exception:
    return 500, {"details": "Unknown error occurred", "success": False}
