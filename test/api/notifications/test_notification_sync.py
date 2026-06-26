from django.utils.timezone import now as tznow

from datetime import timedelta
from uuid import uuid4

from apps.notifications.models import Notification, NotificationRelation
from apps.projects_and_clients.models import Client, Project
from apps.users.models import User
from test.api.base import APIClient
from test.api.conftest import AuthenticatedTestCase


class BaseNotificationSyncTestCase(AuthenticatedTestCase):
  """Helper setup for notification sync API tests."""

  user_create_data = {
    "name": "user1",
    "email": "user1@example.com",
    "password": "pass1234",
    "phone": "5584111111111",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "user1@example.com", "password": "pass1234"}
  URL = "/api/notifications/"

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

    cls.other_user = User.objects.create_user(
      name="user2",
      email="user2@example.com",
      password="pass1234",
      phone="5584222222222",
      is_email_valid=True,
    )

    base_time = tznow()
    cls.user_notifications = []
    for i in range(5):
      notif = Notification.objects.create(
        user=cls.user,
        title=f"Notification {i}",
        message=f"Message {i}",
        read=False,
        deliver_at=base_time + timedelta(hours=i),
        type="SIMPLE",
      )
      cls.user_notifications.append(notif)

    client = Client.objects.create(user=cls.user, name="Test Client", cpf="12345678901")
    cls.project = Project.objects.create(
      user=cls.user,
      client=client,
      name="Test Project",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      labor_fee=50.00,
      status="OPEN",
    )
    notif_with_project = Notification.objects.create(
      user=cls.user,
      title="Project Notification",
      message="Project related",
      read=False,
      deliver_at=base_time + timedelta(hours=10),
      type="ASSOCIATED",
    )
    NotificationRelation.objects.create(
      notification=notif_with_project,
      project=cls.project,
      relation_type="PROJECT",
    )

    cls.other_user_notifications = []
    for i in range(3):
      notif = Notification.objects.create(
        user=cls.other_user,
        title=f"User2 Notification {i}",
        message=f"User2 Message {i}",
        read=False,
        deliver_at=base_time + timedelta(hours=i),
        type="SIMPLE",
      )
      cls.other_user_notifications.append(notif)

  @classmethod
  def tearDownClass(cls):
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def setUp(self):
    super().setUp()
    self.client = APIClient(path_prefix=self.URL)

  def _auth_headers(self):
    return {"Authorization": f"Bearer {self.credentials['access']}"}

  def _post_sync(self, payload, headers=None):
    if headers is None:
      headers = self._auth_headers()
    return self.client.post("sync", payload, headers=headers)


class NotificationSyncRoute__sync(BaseNotificationSyncTestCase):
  def test_with_known_ids_returns_only_new_notifications(self):
    known_ids = [
      str(self.user_notifications[1].id),
      str(self.user_notifications[3].id),
    ]

    response = self._post_sync({"known_notification_ids": known_ids})

    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertIn("notifications", data)
    self.assertEqual(len(data["notifications"]), 4)

  def test_response_matches_contract_schema(self):
    response = self._post_sync({"known_notification_ids": []})

    self.assertEqual(response.status_code, 200)
    data = response.json()

    for notif in data["notifications"]:
      self.assertIn("id", notif)
      self.assertIn("title", notif)
      self.assertIn("message", notif)
      self.assertIn("read", notif)
      self.assertIn("deliver_at", notif)
      self.assertIn("type", notif)
      self.assertIn("extra_fields", notif)
      self.assertIn("relation", notif)

  def test_with_relation_populates_relation_object(self):
    response = self._post_sync({"known_notification_ids": []})

    self.assertEqual(response.status_code, 200)
    data = response.json()

    project_notif = next((n for n in data["notifications"] if n.get("relation")), None)
    self.assertIsNotNone(project_notif)
    self.assertEqual(project_notif["relation"]["relation_type"], "PROJECT")
    self.assertEqual(project_notif["relation"]["project_id"], str(self.project.id))

  def test_without_auth_returns_401(self):
    response = self._post_sync({"known_notification_ids": []}, headers={})

    self.assertEqual(response.status_code, 401)

  def test_invalid_uuid_returns_422(self):
    response = self._post_sync({"known_notification_ids": ["not-a-uuid"]})

    self.assertEqual(response.status_code, 422)

  def test_oversized_list_returns_400(self):
    payload = {"known_notification_ids": [str(uuid4()) for _ in range(10001)]}

    response = self._post_sync(payload)

    self.assertEqual(response.status_code, 400)
    data = response.json()
    self.assertFalse(data["success"])
    self.assertIn("maximum", data["details"])

  def test_user_isolation(self):
    response = self._post_sync({"known_notification_ids": []})

    data = response.json()
    returned_ids = {n["id"] for n in data["notifications"]}
    other_user_ids = {str(n.id) for n in self.other_user_notifications}

    self.assertEqual(len(returned_ids & other_user_ids), 0)

  def test_empty_known_ids_returns_all_user_notifications(self):
    response = self._post_sync({"known_notification_ids": []})

    self.assertEqual(response.status_code, 200)
    self.assertEqual(len(response.json()["notifications"]), 6)

  def test_omitted_known_ids_returns_all_user_notifications(self):
    response = self._post_sync({})

    self.assertEqual(response.status_code, 200)
    self.assertEqual(len(response.json()["notifications"]), 6)

  def test_deterministic_order(self):
    response1 = self._post_sync({"known_notification_ids": []})
    response2 = self._post_sync({"known_notification_ids": []})

    ids1 = [n["id"] for n in response1.json()["notifications"]]
    ids2 = [n["id"] for n in response2.json()["notifications"]]

    self.assertEqual(ids1, ids2)

  def test_deleted_notification_absent_from_next_sync(self):
    notif_to_delete = Notification.objects.create(
      user=self.user,
      title="To Delete",
      message="Temporary notification",
      read=False,
      deliver_at=tznow(),
      type="SIMPLE",
    )

    count_before = len(
      self._post_sync({"known_notification_ids": []}).json()["notifications"]
    )

    notif_to_delete.delete()

    count_after = len(
      self._post_sync({"known_notification_ids": []}).json()["notifications"]
    )

    self.assertEqual(count_after, count_before - 1)
