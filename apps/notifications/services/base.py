from django.core.cache import caches
from datetime import datetime, timedelta
from typing import Union
from django.utils import timezone
from django.utils.dateparse import parse_datetime


class BaseNotificationService:
  @staticmethod
  def _get_cache():
    return caches["notifications"]

  @staticmethod
  def _get_notification_ttl(deliver_at: Union[datetime, str]) -> int:
    if isinstance(deliver_at, str):
      deliver_at = parse_datetime(deliver_at)
    
    if not deliver_at:
      return 0
        
    expiration_date = deliver_at + timedelta(days=7)
    now = timezone.now()
    ttl = int((expiration_date - now).total_seconds())
    return max(ttl, 0)

  @staticmethod
  def _format_notification_key(user_id: str, notif_id: str) -> str:
    return f"notifications:{user_id}:{notif_id}"

  @staticmethod
  def _add_to_notification_index(user_id: str, notif_id: str):
    cache = BaseNotificationService._get_cache()
    ids_key = f"user_notifications:{user_id}"
    ids = cache.get(ids_key) or []
    if notif_id not in ids:
      ids.append(notif_id)
      cache.set(ids_key, ids)

  @staticmethod
  def _remove_from_notification_index(user_id: str, notif_id: str):
    cache = BaseNotificationService._get_cache()
    ids_key = f"user_notifications:{user_id}"
    ids = cache.get(ids_key) or []
    if notif_id in ids:
      ids.remove(notif_id)
      cache.set(ids_key, ids)
