from typing import List
from uuid import UUID

from django.contrib.auth.models import User
from django.db.models import QuerySet

from ..models import Notification


class NotificationService:
  """
  Service class for Notification operations.
  """

  SYNC_MAX_KNOWN_IDS = 10_000

  @staticmethod
  def sync(user: User, known_ids: List[UUID] = []) -> QuerySet:
    """
    Synchronize notifications for a client by filtering out already-known IDs.

    Args:
        user: The authenticated user requesting sync
        known_ids: List of notification UUIDs already on the client (optional)

    Returns:
        QuerySet of Notification objects ordered by delivery time (newest first)
        All notifications excluding those in known_ids list

    Raises:
        ValueError: If known_ids exceeds maximum allowed size

    Implementation notes:
        - Validates list size before querying database
        - Uses exclude() for efficient filtering
        - Prefetches relations to avoid N+1 queries
        - Orders by deliver_at DESC, id ASC for deterministic results
    """
    if len(known_ids) > NotificationService.SYNC_MAX_KNOWN_IDS:
      raise ValueError(
        f"known_notification_ids size exceeds maximum ({NotificationService.SYNC_MAX_KNOWN_IDS})"
      )

    queryset = Notification.objects.filter(user=user)

    if known_ids:
      queryset = queryset.exclude(id__in=known_ids)

    queryset = queryset.prefetch_related("notificationrelation_set").order_by(
      "-deliver_at", "id"
    )

    return queryset
