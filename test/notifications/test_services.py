from datetime import datetime, timedelta
from uuid import uuid4

from django.test import TestCase

from apps.core.exceptions import BusinessRuleError, ResourceNotFoundError
from apps.notifications.models import Notification, NotificationRelation
from apps.notifications.schemas import (
  CreateNotificationReq,
  PartialUpdateNotificationReq,
  RelationInputSchema,
)
from apps.notifications.services import NotificationService
from apps.projects_and_clients.models import Client, Project
from apps.users.models import User


class BaseNotificationServiceTestCase(TestCase):
  """Shared fixtures for NotificationService CRUD tests."""

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
    cls.client = Client.objects.create(
      user=cls.user, name="Test Client", cpf="12345678901"
    )
    cls.project = Project.objects.create(
      user=cls.user,
      client=cls.client,
      name="Test Project",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      labor_fee=50.00,
      status="OPEN",
    )
    cls.base_time = datetime.now()


class TestNotificationService__sync(BaseNotificationServiceTestCase):
  """Unit tests for NotificationService.sync()."""

  @classmethod
  def setUpTestData(cls):
    super().setUpTestData()
    cls.notifications = []
    for i in range(5):
      notif = Notification.objects.create(
        user=cls.user,
        title=f"Notification {i}",
        message=f"Message {i}",
        read=False,
        deliver_at=cls.base_time + timedelta(hours=i),
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


class TestNotificationService__create(BaseNotificationServiceTestCase):
  def test_create_success_with_required_fields(self):
    data = CreateNotificationReq(
      title="New Alert",
      deliver_at=self.base_time,
      type="SIMPLE",
      message="Hello",
    )

    notification = NotificationService.create(self.user, data)

    self.assertEqual(notification.title, "New Alert")
    self.assertEqual(notification.message, "Hello")
    self.assertEqual(notification.type, "SIMPLE")
    self.assertFalse(notification.read)
    self.assertEqual(notification.user, self.user)

  def test_create_with_project_relation(self):
    data = CreateNotificationReq(
      title="Project Alert",
      deliver_at=self.base_time,
      type="ASSOCIATED",
      relation=RelationInputSchema(
        relation_type="PROJECT",
        project_id=self.project.id,
      ),
    )

    notification = NotificationService.create(self.user, data)

    self.assertEqual(notification.notificationrelation_set.count(), 1)
    relation = notification.notificationrelation_set.first()
    self.assertEqual(relation.relation_type, "PROJECT")
    self.assertEqual(relation.project_id, self.project.id)

  def test_create_rejects_invalid_type(self):
    data = CreateNotificationReq(
      title="Bad Type",
      deliver_at=self.base_time,
      type="INVALID",
    )

    with self.assertRaises(BusinessRuleError):
      NotificationService.create(self.user, data)

  def test_create_associated_without_relation_raises(self):
    data = CreateNotificationReq(
      title="Missing Relation",
      deliver_at=self.base_time,
      type="ASSOCIATED",
    )

    with self.assertRaises(BusinessRuleError):
      NotificationService.create(self.user, data)


class TestNotificationService__get(BaseNotificationServiceTestCase):
  def setUp(self):
    self.notification = Notification.objects.create(
      user=self.user,
      title="Get Me",
      message="Body",
      read=False,
      deliver_at=self.base_time,
      type="SIMPLE",
    )

  def test_get_success_returns_notification(self):
    result = NotificationService.get(self.user, str(self.notification.id))

    self.assertEqual(result.id, self.notification.id)
    self.assertEqual(result.title, "Get Me")

  def test_get_not_found_raises(self):
    with self.assertRaises(ResourceNotFoundError):
      NotificationService.get(self.user, str(uuid4()))

  def test_get_other_user_raises(self):
    with self.assertRaises(ResourceNotFoundError):
      NotificationService.get(self.other_user, str(self.notification.id))


class TestNotificationService__list(BaseNotificationServiceTestCase):
  def test_list_returns_user_notifications_ordered(self):
    for i in range(3):
      Notification.objects.create(
        user=self.user,
        title=f"N{i}",
        deliver_at=self.base_time + timedelta(hours=i),
        type="SIMPLE",
      )

    result = list(NotificationService.list(self.user))

    self.assertEqual(len(result), 3)
    for i in range(len(result) - 1):
      self.assertGreaterEqual(result[i].deliver_at, result[i + 1].deliver_at)

  def test_list_empty_for_user_without_notifications(self):
    self.assertEqual(NotificationService.list(self.other_user).count(), 0)

  def test_list_user_isolation(self):
    Notification.objects.create(
      user=self.other_user,
      title="Other",
      deliver_at=self.base_time,
      type="SIMPLE",
    )
    Notification.objects.create(
      user=self.user,
      title="Mine",
      deliver_at=self.base_time,
      type="SIMPLE",
    )

    result = list(NotificationService.list(self.user))

    self.assertEqual(len(result), 1)
    self.assertEqual(result[0].user, self.user)


class TestNotificationService__partial_update(BaseNotificationServiceTestCase):
  def setUp(self):
    self.notification = Notification.objects.create(
      user=self.user,
      title="Original",
      message="Original message",
      read=False,
      deliver_at=self.base_time,
      type="SIMPLE",
    )

  def test_partial_update_mark_read_only(self):
    data = PartialUpdateNotificationReq(read=True)

    updated = NotificationService.partial_update(
      self.user, str(self.notification.id), data
    )

    self.assertTrue(updated.read)
    self.assertEqual(updated.title, "Original")
    self.assertEqual(updated.message, "Original message")

  def test_partial_update_relation(self):
    NotificationRelation.objects.create(
      notification=self.notification,
      project=self.project,
      relation_type="PROJECT",
    )
    other_client = Client.objects.create(
      user=self.user, name="Other Client", cpf="98765432100"
    )
    data = PartialUpdateNotificationReq(
      relation=RelationInputSchema(
        relation_type="CLIENT",
        client_id=other_client.id,
      )
    )

    updated = NotificationService.partial_update(
      self.user, str(self.notification.id), data
    )

    relation = updated.notificationrelation_set.first()
    self.assertEqual(relation.relation_type, "CLIENT")
    self.assertEqual(relation.client_id, other_client.id)

  def test_partial_update_empty_payload_is_no_op(self):
    data = PartialUpdateNotificationReq()

    updated = NotificationService.partial_update(
      self.user, str(self.notification.id), data
    )

    self.assertEqual(updated.title, "Original")
    self.assertFalse(updated.read)

  def test_partial_update_not_found_raises(self):
    with self.assertRaises(ResourceNotFoundError):
      NotificationService.partial_update(
        self.user, str(uuid4()), PartialUpdateNotificationReq(read=True)
      )

  def test_partial_update_invalid_type_raises(self):
    with self.assertRaises(BusinessRuleError):
      NotificationService.partial_update(
        self.user,
        str(self.notification.id),
        PartialUpdateNotificationReq(type="INVALID"),
      )


class TestNotificationService__delete(BaseNotificationServiceTestCase):
  def test_delete_success(self):
    notification = Notification.objects.create(
      user=self.user,
      title="Delete Me",
      deliver_at=self.base_time,
      type="SIMPLE",
    )

    result = NotificationService.delete(self.user, str(notification.id))

    self.assertEqual(result, {"success": True})
    self.assertFalse(Notification.objects.filter(id=notification.id).exists())

  def test_delete_cascades_relation(self):
    notification = Notification.objects.create(
      user=self.user,
      title="With Relation",
      deliver_at=self.base_time,
      type="ASSOCIATED",
    )
    relation = NotificationRelation.objects.create(
      notification=notification,
      project=self.project,
      relation_type="PROJECT",
    )

    NotificationService.delete(self.user, str(notification.id))

    self.assertFalse(NotificationRelation.objects.filter(id=relation.id).exists())

  def test_delete_not_found_raises(self):
    with self.assertRaises(ResourceNotFoundError):
      NotificationService.delete(self.user, str(uuid4()))

  def test_delete_other_user_raises(self):
    notification = Notification.objects.create(
      user=self.user,
      title="Protected",
      deliver_at=self.base_time,
      type="SIMPLE",
    )

    with self.assertRaises(ResourceNotFoundError):
      NotificationService.delete(self.other_user, str(notification.id))

    self.assertTrue(Notification.objects.filter(id=notification.id).exists())
