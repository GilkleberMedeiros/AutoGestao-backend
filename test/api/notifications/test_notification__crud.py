from django.utils.timezone import now as tznow
from datetime import timedelta

from test.api.conftest import AuthenticatedTestCase
from apps.users.models import User
from apps.projects_and_clients.models import Client, Project
from apps.notifications.models import Notification, NotificationRelation


class BaseNotificationTestCase(AuthenticatedTestCase):
  """Helper setup for notification API tests."""

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

    cls.client_obj = Client.objects.create(
      user=cls.user, name="Test Client", cpf="12345678901"
    )
    cls.project = Project.objects.create(
      user=cls.user,
      client=cls.client_obj,
      name="Test Project",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      labor_fee=50.00,
      status="OPEN",
    )

  @classmethod
  def tearDownClass(cls):
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def _auth_headers(self):
    return {"Authorization": f"Bearer {self.credentials['access']}"}


class NotificationRoutes__Create(BaseNotificationTestCase):
  """Tests for notification creation route."""

  def test_create_notification_success(self):
    payload = {
      "title": "New Notification",
      "message": "This is a new notification.",
      "deliver_at": (tznow() + timedelta(hours=2)).isoformat(),
    }
    response = self.client.post(
      data=payload,
      headers=self._auth_headers(),
    )
    data = response.json()

    self.assertEqual(response.status_code, 201)
    self.assertIsNotNone(data.get("id", None))
    self.assertEqual(data.get("title"), payload["title"])
    # Type must be SIMPLE by default when no relation is provided
    self.assertEqual(data.get("type"), "SIMPLE")

  def test_create_notification_with_relation_success(self):
    payload = {
      "title": "New Notification",
      "deliver_at": (tznow() + timedelta(hours=2)).isoformat(),
      "relation": {
        "relation_type": "PROJECT",
        "project_id": str(self.project.id),
      },
    }
    response = self.client.post(
      data=payload,
      headers=self._auth_headers(),
    )
    data = response.json()

    self.assertEqual(response.status_code, 201)
    self.assertIsNotNone(data.get("id", None))
    self.assertIsNotNone(data.get("relation", None))
    self.assertEqual(data.get("title"), payload["title"])
    self.assertEqual(data.get("type"), "ASSOCIATED")
    self.assertEqual(data["relation"].get("relation_type"), "PROJECT")
    self.assertEqual(data["relation"].get("project_id"), str(self.project.id))

  def test_create_notification_invalid_relation(self):
    payload = {
      "title": "New Notification",
      "deliver_at": (tznow() + timedelta(hours=2)).isoformat(),
      "relation": {
        "relation_type": "INVALID_TYPE",
        "project_id": str(self.project.id),
      },
    }
    response = self.client.post(
      data=payload,
      headers=self._auth_headers(),
    )
    self.assertEqual(response.status_code, 400)
    data = response.json()
    self.assertFalse(data.get("success"))
    self.assertIn("Invalid relation type", data.get("details", ""))

  def test_create_notification_invalid_payload(self):
    # Missing required "title" field
    payload = {
      "deliver_at": (tznow() + timedelta(hours=2)).isoformat(),
    }
    response = self.client.post(
      data=payload,
      headers=self._auth_headers(),
    )
    # Ninja returns 422 for validation errors
    self.assertEqual(response.status_code, 422)

  def test_create_notification_unauthenticated(self):
    payload = {
      "title": "New Notification",
      "message": "This is a new notification.",
      "deliver_at": (tznow() + timedelta(hours=2)).isoformat(),
    }
    response = self.client.post(
      data=payload,
    )
    self.assertEqual(response.status_code, 401)

  def test_create_notification_user_email_invalid(self):
    self.user.is_email_valid = False
    self.user.save()

    payload = {
      "title": "New Notification",
      "deliver_at": (tznow() + timedelta(hours=2)).isoformat(),
    }
    response = self.client.post(
      data=payload,
      headers=self._auth_headers(),
    )

    # Returns User to Original State
    self.user.is_email_valid = True
    self.user.save()

    self.assertEqual(response.status_code, 403)


class BaseUpdateDeleteNotificationTestCase(BaseNotificationTestCase):
  """Base class for update and delete notification tests."""

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.other_user = User.objects.create_user(
      name="user2",
      email="user2@example.com",
      password="pass1234",
      phone="5584222222222",
      is_email_valid=True,
    )

    base_time = tznow()
    cls.notification = Notification.objects.create(
      user=cls.user,
      title="Original",
      message="Original Messaage",
      read=False,
      deliver_at=base_time + timedelta(hours=1),
      type="SIMPLE",
    )

    cls.notification_with_project = Notification.objects.create(
      user=cls.user,
      title="Project Notification",
      message="Project related",
      read=False,
      deliver_at=base_time + timedelta(hours=10),
      type="ASSOCIATED",
    )
    NotificationRelation.objects.create(
      notification=cls.notification_with_project,
      project=cls.project,
      relation_type="PROJECT",
    )

    cls.other_user_notification = Notification.objects.create(
      user=cls.other_user,
      title="Other User",
      message="Other User Message",
      read=False,
      deliver_at=base_time + timedelta(hours=1),
      type="SIMPLE",
    )


class NotificationRoutes_Update(BaseUpdateDeleteNotificationTestCase):
  """Tests for notification update route."""

  def test_update_notification_success(self):
    payload = {
      "title": "Updated Title",
      "message": "Updated Message",
    }
    response = self.client.patch(
      f"{self.notification.id}",
      data=payload,
      headers=self._auth_headers(),
    )
    data = response.json()

    self.assertEqual(response.status_code, 200)
    self.assertEqual(data.get("id"), str(self.notification.id))
    self.assertEqual(data.get("title"), payload["title"])
    self.assertEqual(data.get("message"), payload["message"])

  def test_update_notification_not_found(self):
    payload = {"title": "Updated Title"}
    response = self.client.patch(
      "00000000-0000-0000-0000-000000000000",
      data=payload,
      headers=self._auth_headers(),
    )

    self.assertEqual(response.status_code, 404)
    data = response.json()
    self.assertFalse(data.get("success"))

  def test_update_cant_update_fields(self):
    payload = {
      "title": "Updated Title",
      "read": True,
      "type": "ASSOCIATED",
      "relation": {
        "relation_type": "CLIENT",
        "project_id": str(self.client_obj.id),
      },
      "extra_fields": {"new": "field"},
    }
    response = self.client.patch(
      f"{self.notification.id}",
      data=payload,
      headers=self._auth_headers(),
    )
    data = response.json()

    self.assertEqual(response.status_code, 200)
    self.assertEqual(data.get("id"), str(self.notification.id))
    self.assertEqual(data.get("title"), payload["title"])
    self.assertFalse(data.get("read"))
    self.assertIsNone(data.get("relation"))
    self.assertEqual(data.get("type"), "SIMPLE")
    self.assertIsNone(data.get("extra_fields"))

  def test_update_cant_update_other_user_notification(self):
    payload = {"title": "Updated Title"}
    response = self.client.patch(
      f"{self.other_user_notification.id}",
      data=payload,
      headers=self._auth_headers(),
    )

    self.assertEqual(response.status_code, 404)
    data = response.json()
    self.assertFalse(data.get("success"))
    self.assertIn("Notification not found", data.get("details", ""))

  def test_update_notification_invalid_payload(self):
    payload = {"deliver_at": "not-a-datetime"}
    response = self.client.patch(
      f"{self.notification.id}",
      data=payload,
      headers=self._auth_headers(),
    )

    self.assertEqual(response.status_code, 422)

  def test_update_notification_unauthenticated(self):
    payload = {"title": "Updated Title"}
    response = self.client.patch(
      f"{self.notification.id}",
      data=payload,
    )

    self.assertEqual(response.status_code, 401)

  def test_update_notification_user_email_invalid(self):
    self.user.is_email_valid = False
    self.user.save()

    payload = {"title": "Updated Title"}
    response = self.client.patch(
      f"{self.notification.id}",
      data=payload,
      headers=self._auth_headers(),
    )

    # Returns User to valid email
    self.user.is_email_valid = True
    self.user.save()

    self.assertEqual(response.status_code, 403)


class NotificationRoutes_Delete(BaseUpdateDeleteNotificationTestCase):
  """Tests for notification delete route."""

  def test_delete_notification_success(self):
    response = self.client.delete(
      f"{self.notification.id}",
      headers=self._auth_headers(),
    )

    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.json().get("success"))
    self.assertFalse(Notification.objects.filter(id=self.notification.id).exists())

  def test_delete_notification_not_found(self):
    response = self.client.delete(
      "00000000-0000-0000-0000-000000000000",
      headers=self._auth_headers(),
    )

    self.assertEqual(response.status_code, 404)
    data = response.json()
    self.assertFalse(data.get("success"))
    self.assertIn("Notification not found", data.get("details", ""))

  def test_delete_notification_cant_delete_other_user_notification(self):
    response = self.client.delete(
      f"{self.other_user_notification.id}",
      headers=self._auth_headers(),
    )

    self.assertEqual(response.status_code, 404)
    data = response.json()
    self.assertFalse(data.get("success"))
    self.assertIn("Notification not found", data.get("details", ""))

  def test_delete_notification_unauthenticated(self):
    response = self.client.delete(f"{self.notification.id}")

    self.assertEqual(response.status_code, 401)
    self.assertFalse(response.json().get("success"))

  def test_delete_notification_user_email_invalid(self):
    self.user.is_email_valid = False
    self.user.save()

    response = self.client.delete(
      f"{self.notification.id}",
      headers=self._auth_headers(),
    )

    self.user.is_email_valid = True
    self.user.save()

    self.assertEqual(response.status_code, 403)
    self.assertFalse(response.json().get("success"))
