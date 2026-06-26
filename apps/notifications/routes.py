from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Body

from apps.core.schemas.response import BaseAPIResponse

from .schemas import SyncRequestSchema, SyncResponseSchema
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
