from ninja import Router
from typing import List

from apps.core.schemas.response import BaseAPIResponse
from apps.notifications.schemas.notification import (
  NotificationSchema,
  NotificationCreateReq,
  UpdateNotificationReq,
  SyncNotificationReq,
  SyncNotificationSchema,
)
from apps.notifications.services.notification import NotificationService
from apps.notifications.services.sync import SyncNotificationService

router = Router()


@router.post("/", response=NotificationSchema)
def create_notification(request, data: NotificationCreateReq):
  return NotificationService.create(str(request.user.id), data)


@router.patch("/sync", response=List[SyncNotificationSchema])
def sync_notifications(request, data: SyncNotificationReq):
  return SyncNotificationService.sync(
    str(request.user.id), [str(id) for id in data.already_synced_ids]
  )


@router.get("/{notif_id}", response={200: NotificationSchema, 404: BaseAPIResponse})
def get_notification(request, notif_id: str):
  notif = NotificationService.get(str(request.user.id), notif_id)
  if not notif:
    return 404, {"details": "Notification not found", "success": False}
  return notif


@router.patch("/{notif_id}", response={200: NotificationSchema, 404: BaseAPIResponse})
def update_notification(request, notif_id: str, data: UpdateNotificationReq):
  notif = NotificationService.update(str(request.user.id), notif_id, data)
  if not notif:
    return 404, {"details": "Notification not found", "success": False}
  return notif


@router.delete("/{notif_id}", response={200: BaseAPIResponse, 404: BaseAPIResponse})
def delete_notification(request, notif_id: str):
  """
  Deletes a notification. Fails silently if notification doesn't exist.
  """
  NotificationService.delete(str(request.user.id), notif_id)
  return {"details": "Notification deleted successfully", "success": True}
