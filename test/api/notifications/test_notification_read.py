from django.utils.timezone import now as tznow
from datetime import timedelta
import uuid

from test.api.conftest import AuthenticatedTestCase
from apps.users.models import User
from apps.notifications.models import Notification


class NotificationRoutes_Read(AuthenticatedTestCase):
  """Tests for notification read route."""

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

    base_time = tznow()
    cls.notification = Notification.objects.create(
      user=cls.user,
      title="Original",
      message="Original Message",
      read=False,
      deliver_at=base_time + timedelta(hours=1),
      type="SIMPLE",
    )

    cls.other_user = User.objects.create_user(
      name="user2",
      email="user2@example.com",
      password="pass1234",
      phone="5584222222222",
      is_email_valid=True,
    )
    cls.other_user_notification = Notification.objects.create(
      user=cls.other_user,
      title="Other User",
      message="Other User Message",
      read=False,
      deliver_at=base_time + timedelta(hours=1),
      type="SIMPLE",
    )

  @classmethod
  def tearDownClass(cls):
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def setUp(self):
    super().setUp()
    self.notification.read = False
    self.notification.save()

  def _auth_headers(self):
    return {"Authorization": f"Bearer {self.credentials['access']}"}

  def test_read_notification_success(self):
    response = self.client.post(
      f"read/{self.notification.id}",
      headers=self._auth_headers(),
    )
    data = response.json()

    self.assertEqual(response.status_code, 200)
    self.assertEqual(data.get("id"), str(self.notification.id))
    self.assertTrue(data.get("read"))

  def test_read_notification_not_found(self):
    response = self.client.post(
      f"read/{str(uuid.uuid4())}",
      headers=self._auth_headers(),
    )

    self.assertEqual(response.status_code, 404)
    data = response.json()
    self.assertFalse(data.get("success"))
    self.assertIn("Notification not found", data.get("details", ""))

  def test_read_notification_cant_read_from_other_user(self):
    response = self.client.post(
      f"read/{self.other_user_notification.id}",
      headers=self._auth_headers(),
    )

    self.assertEqual(response.status_code, 404)
    data = response.json()
    self.assertFalse(data.get("success"))
    self.assertIn("Notification not found", data.get("details", ""))

  def test_read_notification_unauthenticated(self):
    response = self.client.post(f"read/{self.notification.id}")

    self.assertEqual(response.status_code, 401)
    self.assertFalse(response.json().get("success"))

  def test_read_notification_user_email_invalid(self):
    self.user.is_email_valid = False
    self.user.save()

    response = self.client.post(
      f"read/{self.notification.id}",
      headers=self._auth_headers(),
    )

    self.user.is_email_valid = True
    self.user.save()

    self.assertEqual(response.status_code, 403)
    self.assertFalse(response.json().get("success"))
