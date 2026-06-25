from datetime import datetime, timedelta
from uuid import uuid4

from django.test import TestCase

from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from apps.users.models import User


class TestNotificationService__sync(TestCase):
  """Unit tests for NotificationService.sync()."""

  @classmethod
  def setUpTestData(cls):
    cls.user = User.objects.create_user(
      name="testuser",
      email="testuser@example.com",
      password="testpass123",
      phone="5584999999999",
    )
    cls.other_user = User.objects.create_user(
      name="otheruser",
      email="otheruser@example.com",
      password="testpass123",
      phone="5584888888888",
    )

    base_time = datetime.now()
    cls.notifications = []
    for i in range(5):
      notif = Notification.objects.create(
        user=cls.user,
        title=f"Notification {i}",
        message=f"Message {i}",
        read=False,
        deliver_at=base_time + timedelta(hours=i),
        type="SIMPLE",
      )
      cls.notifications.append(notif)

  def test_filters_known_ids(self):
    known_ids = [self.notifications[0].id, self.notifications[2].id]
    result = list(NotificationService.sync(self.user, known_ids))

    self.assertEqual(len(result), 3)
    result_ids = {n.id for n in result}
    self.assertNotIn(known_ids[0], result_ids)
    self.assertNotIn(known_ids[1], result_ids)

  def test_returns_ordered_by_deliver_at_desc(self):
    result = list(NotificationService.sync(self.user, []))

    for i in range(len(result) - 1):
      self.assertGreater(result[i].deliver_at, result[i + 1].deliver_at)

  def test_empty_known_ids_returns_all_notifications(self):
    result = list(NotificationService.sync(self.user, []))

    self.assertEqual(len(result), 5)

  def test_unknown_valid_uuids_are_safely_ignored(self):
    known_ids = [self.notifications[0].id, uuid4()]
    result = list(NotificationService.sync(self.user, known_ids))

    self.assertEqual(len(result), 4)
    result_ids = {n.id for n in result}
    self.assertNotIn(known_ids[0], result_ids)

  def test_max_size_validation_raises_value_error(self):
    oversized_list = [uuid4() for _ in range(10001)]

    with self.assertRaises(ValueError):
      NotificationService.sync(self.user, oversized_list)

  def test_user_isolation(self):
    Notification.objects.create(
      user=self.other_user,
      title="Other User Notification",
      message="Should not appear",
      read=False,
      deliver_at=datetime.now(),
      type="SIMPLE",
    )

    result = list(NotificationService.sync(self.user, []))

    self.assertEqual(len(result), 5)
    for notif in result:
      self.assertEqual(notif.user, self.user)

  def test_deterministic_ordering(self):
    result1 = list(NotificationService.sync(self.user, []))
    result2 = list(NotificationService.sync(self.user, []))

    self.assertEqual([n.id for n in result1], [n.id for n in result2])
