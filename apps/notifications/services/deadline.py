import json
from uuid import uuid4, UUID
from apps.notifications.schemas.deadline import (
  DeadlineNotificationCreateReq,
  UpdateDeadlineNotificationReq,
)

from apps.notifications.services.base import BaseNotificationService
from apps.notifications.services.notification import NotificationService
from apps.notifications.dto import DeadlineNotificationDTO, NotificationTypes


class DeadlineNotificationService(NotificationService):
  @staticmethod
  def create(
    user_id: str, data: DeadlineNotificationCreateReq
  ) -> DeadlineNotificationDTO:
    cache = NotificationService._get_cache()
    notif_id = uuid4()

    notification: DeadlineNotificationDTO = {
      "id": notif_id,
      "user_id": UUID(user_id),
      "title": data.title,
      "message": data.message,
      "type": NotificationTypes.DEADLINE,
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
  def update(
    user_id: str, notif_id: str, data: UpdateDeadlineNotificationReq
  ) -> DeadlineNotificationDTO:
    return NotificationService.update(user_id, notif_id, data)
