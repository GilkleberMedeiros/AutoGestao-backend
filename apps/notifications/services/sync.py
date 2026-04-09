from typing import List
from apps.notifications.services.notification import NotificationService
from apps.notifications.schemas.notification import NotificationSchema


class SyncNotificationService:
  @staticmethod
  def sync(
    user_id: str, already_synced_ids: List[str] = []
  ) -> List[NotificationSchema]:
    cache = NotificationService._get_cache()
    ids_key = f"user_notifications:{user_id}"
    ids = cache.get(ids_key) or []

    # Convert list to set for O(1) lookups, ensuring we compare strings
    already_synced_ids_set = {str(i) for i in already_synced_ids}

    notifications = []

    for notif_id in ids:
      if notif_id in already_synced_ids_set:
        continue

      # Using NotificationService.get should works for all notification types
      # because all other services inherit from NotificationService
      # without reimplementing get method

      notif = NotificationService.get(user_id, notif_id)
      if notif:
        notifications.append(notif)

    return notifications
