from django.test import TestCase, override_settings

from apps.users.models import User
from apps.notifications.services.spending_limit import SpendingLimitNotificationService
from apps.notifications.schemas.spending_limit import (
  SpendingLimitNotificationCreateReq,
  UpdateSpendingLimitNotificationReq,
)
from apps.notifications.dto import NotificationTypes, NotificationPeriods


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
class TestSpendingLimitNotificationService(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="testspending",
      email="spending@example.com",
      password="password123",
      phone="5584777777777",
    )

  def test_create_multiple_spending_limits(self):
    # Rule 1: Weekly
    data1 = SpendingLimitNotificationCreateReq(
      title="Weekly Limit",
      message="You spent more than 500 this week",
      threshold=500.0,
      period=NotificationPeriods.WEEKLY,
    )
    notif1 = SpendingLimitNotificationService.create(str(self.user.id), data1)

    # Rule 2: Monthly
    data2 = SpendingLimitNotificationCreateReq(
      title="Monthly Limit",
      message="You spent more than 2000 this month",
      threshold=2000.0,
      period=NotificationPeriods.MONTHLY,
    )
    notif2 = SpendingLimitNotificationService.create(str(self.user.id), data2)

    self.assertNotEqual(notif1["id"], notif2["id"])
    self.assertEqual(notif1["period"], NotificationPeriods.WEEKLY)
    self.assertEqual(notif2["period"], NotificationPeriods.MONTHLY)
    self.assertEqual(notif1["type"], NotificationTypes.SPENDING_LIMIT)

  def test_update_spending_limit(self):
    notif = SpendingLimitNotificationService.create(
      str(self.user.id),
      SpendingLimitNotificationCreateReq(
        title="Limit",
        message="Msg",
        threshold=100.0,
        period=NotificationPeriods.MONTHLY,
      ),
    )

    updated = SpendingLimitNotificationService.update(
      str(self.user.id),
      notif["id"],
      UpdateSpendingLimitNotificationReq(threshold=150.0),
    )

    self.assertEqual(updated["threshold"], 150.0)
    
    # Reload
    stored = SpendingLimitNotificationService.get(str(self.user.id), notif["id"])
    self.assertEqual(stored["threshold"], 150.0)
