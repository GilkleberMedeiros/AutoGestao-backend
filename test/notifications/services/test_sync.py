from django.test import TestCase, override_settings
from django.utils import timezone

from apps.users.models import User
from apps.notifications.services.notification import NotificationService
from apps.notifications.services.spending_limit import SpendingLimitNotificationService
from apps.notifications.services.sync import SyncNotificationService
from apps.notifications.schemas.notification import NotificationCreateReq
from apps.notifications.schemas.spending_limit import SpendingLimitNotificationCreateReq
from apps.notifications.dto import NotificationPeriods


@override_settings(
  CACHES={
    "default": {
      "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
      "LOCATION": "default",
    },
    "notifications": {
      "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
      "LOCATION": "notifications",
      "TIMEOUT": None,
    },
  }
)
class TestSyncNotificationService(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="testsync",
      email="sync@example.com",
      password="password123",
      phone="5584555555555",
    )

  def test_sync_delta_filtering(self):
    # 1. Create 3 notifications
    n1 = NotificationService.create(
      str(self.user.id),
      NotificationCreateReq(title="N1", message="M1", deliver_at=timezone.now()),
    )
    n2 = SpendingLimitNotificationService.create(
      str(self.user.id),
      SpendingLimitNotificationCreateReq(
        title="N2", message="M2", threshold=100.0, period=NotificationPeriods.WEEKLY
      ),
    )
    n3 = NotificationService.create(
      str(self.user.id),
      NotificationCreateReq(title="N3", message="M3", deliver_at=timezone.now()),
    )

    # 2. Sync with empty list -> should return all 3
    all_notifs = SyncNotificationService.sync(str(self.user.id), [])
    self.assertEqual(len(all_notifs), 3)

    # 3. Sync with N1 already synced -> should return only N2 and N3
    delta = SyncNotificationService.sync(str(self.user.id), [n1["id"]])
    self.assertEqual(len(delta), 2)
    delta_ids = [n["id"] for n in delta]
    self.assertNotIn(n1["id"], delta_ids)
    self.assertIn(n2["id"], delta_ids)
    self.assertIn(n3["id"], delta_ids)

    # 4. Sync with all already synced -> should return empty
    empty = SyncNotificationService.sync(str(self.user.id), [n1["id"], n2["id"], n3["id"]])
    self.assertEqual(len(empty), 0)
