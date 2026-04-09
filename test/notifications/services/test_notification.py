from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from uuid import uuid4

from apps.users.models import User
from apps.notifications.services.notification import NotificationService
from apps.notifications.schemas.notification import (
  NotificationCreateReq,
  UpdateNotificationReq,
)
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
class TestNotificationService(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="testnotif",
      email="testnotif@example.com",
      password="password123",
      phone="5584888888888",
    )

  def setUp(self):
    # Clear Redis for the user before each test if necessary
    # Since we are using a dedicated DB for notifications, we should be careful.
    # But in tests, Django might mock cache or use a separate DB if configured.
    # Notifications use django-redis with 'notifications' alias.
    pass

  def test_create_notification(self):
    data = NotificationCreateReq(
      title="Test Title",
      message="Test Message",
      deliver_at=timezone.now() + timedelta(days=1),
    )
    notif = NotificationService.create(str(self.user.id), data)

    self.assertEqual(notif["title"], "Test Title")
    self.assertEqual(notif["type"], NotificationTypes.PERSONAL)
    self.assertEqual(notif["user_id"], self.user.id)

    # Verify storage
    stored = NotificationService.get(str(self.user.id), notif["id"])
    self.assertIsNotNone(stored)
    self.assertEqual(stored["title"], "Test Title")

  def test_get_non_existent_notification(self):
    notif = NotificationService.get(str(self.user.id), str(uuid4()))
    self.assertIsNone(notif)

  def test_update_notification(self):
    notif = NotificationService.create(
      str(self.user.id),
      NotificationCreateReq(
        title="Original", message="Msg", deliver_at=timezone.now()
      ),
    )

    updated = NotificationService.update(
      str(self.user.id),
      notif["id"],
      UpdateNotificationReq(title="Updated Title"),
    )

    self.assertEqual(updated["title"], "Updated Title")
    
    # Reload and verify
    stored = NotificationService.get(str(self.user.id), notif["id"])
    self.assertEqual(stored["title"], "Updated Title")

  def test_delete_notification(self):
    notif = NotificationService.create(
      str(self.user.id),
      NotificationCreateReq(
        title="To Delete", message="Msg", deliver_at=timezone.now()
      ),
    )
    
    notif_id = notif["id"]
    NotificationService.delete(str(self.user.id), notif_id)
    
    stored = NotificationService.get(str(self.user.id), notif_id)
    self.assertIsNone(stored)
