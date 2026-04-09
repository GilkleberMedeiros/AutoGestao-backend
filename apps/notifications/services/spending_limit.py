import json
from uuid import uuid4, UUID
from apps.notifications.schemas.spending_limit import (
  SpendingLimitNotificationCreateReq,
  UpdateSpendingLimitNotificationReq,
)

from apps.core.exceptions import ResourceNotFoundError
from apps.notifications.services.base import BaseNotificationService
from apps.notifications.services.notification import NotificationService
from apps.notifications.dto import SpendingLimitNotificationDTO, NotificationTypes


class SpendingLimitNotificationService(NotificationService):
  @staticmethod
  def create(
    user_id: str, data: SpendingLimitNotificationCreateReq
  ) -> SpendingLimitNotificationDTO:
    cache = NotificationService._get_cache()
    notif_id = uuid4()

    notification: SpendingLimitNotificationDTO = {
      "id": notif_id,
      "user_id": UUID(user_id) if isinstance(user_id, str) else user_id,
      "title": data.title,
      "message": data.message,
      "type": NotificationTypes.SPENDING_LIMIT,
      "threshold": data.threshold,
      "period": data.period,
    }

    # Store in Redis (Persistent)
    key = BaseNotificationService._format_notification_key(user_id, str(notif_id))
    cache.set(key, json.dumps(notification, default=str), timeout=None)

    # Keep track of all notification IDs for the user in a set-like list
    BaseNotificationService._add_to_notification_index(user_id, str(notif_id))

    return notification

  @staticmethod
  def update(
    user_id: str, notif_id: str, data: UpdateSpendingLimitNotificationReq
  ) -> SpendingLimitNotificationDTO:
    cache = NotificationService._get_cache()
    d = NotificationService.get(user_id, notif_id)
    if not d:
      raise ResourceNotFoundError("Notification not found")

    update_data = data.dict(exclude_unset=True)
    for attr, value in update_data.items():
      d[attr] = value

    key = BaseNotificationService._format_notification_key(user_id, notif_id)
    cache.set(key, json.dumps(d, default=str), timeout=None)

    return d

  @staticmethod
  def delete(user_id: str, notif_id: str):
    """
    Deletes a notification from the cache. Fails silently if notification doesn't exist.
    """
    NotificationService.delete(user_id, notif_id)
    return True
