import json
from uuid import uuid4, UUID
from apps.notifications.schemas.notification import (
  NotificationCreateReq,
  UpdateNotificationReq,
)

from apps.core.exceptions import ResourceNotFoundError
from apps.notifications.services.base import BaseNotificationService
from apps.notifications.dto import NotificationDTO, NotificationTypes


class NotificationService(BaseNotificationService):
  @staticmethod
  def create(user_id: str, data: NotificationCreateReq) -> NotificationDTO:
    cache = NotificationService._get_cache()
    notif_id = uuid4()

    notification: NotificationDTO = {
      "id": notif_id,
      "user_id": UUID(user_id),
      "title": data.title,
      "message": data.message,
      "type": NotificationTypes.PERSONAL,
      "deliver_at": data.deliver_at,
    }

    # Store in Redis
    key = BaseNotificationService._format_notification_key(user_id, str(notif_id))
    ttl = BaseNotificationService._get_notification_ttl(notification["deliver_at"])
    cache.set(key, json.dumps(notification, default=str), timeout=ttl)

    # Keep track of all notification IDs for the user in a set-like list
    BaseNotificationService._add_to_notification_index(user_id, str(notif_id))

    return notification

  @staticmethod
  def get(user_id: str, notif_id: str) -> NotificationDTO:
    cache = NotificationService._get_cache()
    key = BaseNotificationService._format_notification_key(user_id, notif_id)
    data = cache.get(key)
    if not data:
      return None
    # We use json.loads instead of parse_raw because we might have extra fields like threshold
    d = json.loads(data)
    # Ensure id and user_id are UUID objects for consistency
    if "id" in d:
      d["id"] = UUID(d["id"])
    if "user_id" in d:
      d["user_id"] = UUID(d["user_id"])
    return d

  @staticmethod
  def update(
    user_id: str, notif_id: str, data: UpdateNotificationReq
  ) -> NotificationDTO:
    cache = NotificationService._get_cache()
    d = NotificationService.get(user_id, notif_id)
    if not d:
      raise ResourceNotFoundError("Notification not found")

    update_data = data.dict(exclude_unset=True)
    for attr, value in update_data.items():
      d[attr] = value

    key = BaseNotificationService._format_notification_key(user_id, notif_id)
    # Handle optional deliver_at for TTL
    ttl = None
    if "deliver_at" in d:
      ttl = BaseNotificationService._get_notification_ttl(d["deliver_at"])
    
    cache.set(key, json.dumps(d, default=str), timeout=ttl)

    return d

  @staticmethod
  def delete(user_id: str, notif_id: str):
    """
    Deletes a notification from the cache. Fails silently if notification doesn't exist.
    """
    cache = NotificationService._get_cache()
    key = BaseNotificationService._format_notification_key(user_id, notif_id)
    cache.delete(key)

    # Remove from notification index
    BaseNotificationService._remove_from_notification_index(user_id, notif_id)
    return True
