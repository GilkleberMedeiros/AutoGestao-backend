from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta

from apps.users.models import User
from apps.notifications.services.deadline import DeadlineNotificationService
from apps.notifications.schemas.deadline import DeadlineNotificationCreateReq
from apps.notifications.dto import NotificationTypes


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
class TestDeadlineNotificationService(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="testdeadline",
      email="deadline@example.com",
      password="password123",
      phone="5584666666666",
    )

  def test_create_deadline_notification(self):
    data = DeadlineNotificationCreateReq(
      title="Project X Deadline",
      message="7 days remaining",
      deliver_at=timezone.now() + timedelta(days=7),
    )
    notif = DeadlineNotificationService.create(str(self.user.id), data)

    self.assertEqual(notif["type"], NotificationTypes.DEADLINE)
    self.assertIn("Project X", notif["title"])
    
    # Verify persistence
    stored = DeadlineNotificationService.get(str(self.user.id), notif["id"])
    self.assertIsNotNone(stored)
    self.assertEqual(stored["type"], NotificationTypes.DEADLINE)
