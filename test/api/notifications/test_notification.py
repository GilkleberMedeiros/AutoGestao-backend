import os
from django.utils import timezone
from datetime import timedelta
from test.api.base import AuthenticatedTestCase
from apps.users.models import User
from apps.notifications.services.notification import NotificationService
from apps.notifications.schemas.notification import NotificationCreateReq


class TestNotificationAPI(AuthenticatedTestCase):
  user_create_model = User
  user_create_data = {
    "name": "apinotif",
    "email": "apinotif@example.com",
    "password": "password123",
    "phone": "5584444444444",
    "is_email_valid": True,
  }
  login_data = {"email": "apinotif@example.com", "password": "password123"}

  @classmethod
  def setUpClass(cls):
    os.environ["USE_DEBUG_ALERTS_DB"] = "True"
    super().setUpClass()

  def setUp(self):
    super().setUpUser()
    super().setUpAuth()

  def tearDown(self):
    super().tearDownAuth()
    super().tearDownUser()

  def test_create_notification(self):
    payload = {
      "title": "API Test",
      "message": "Hello",
      "deliver_at": (timezone.now() + timedelta(days=1)).isoformat(),
    }
    response = self.client.post(
      "/api/notifications/",
      data=payload,
      headers={"Authorization": f"Bearer {self.credentials['access']}"},
    )
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(data["title"], "API Test")

  def test_sync_notifications(self):
    # 1. Create a notification
    NotificationService.create(
      str(self.user.id),
      NotificationCreateReq(title="Old", message="M", deliver_at=timezone.now()),
    )

    # 2. Sync (PATCH /sync)
    response = self.client.patch(
      "/api/notifications/sync",
      data={"already_synced_ids": []},
      headers={"Authorization": f"Bearer {self.credentials['access']}"},
    )
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(len(data), 1)
    notif_id = data[0]["id"]

    # 3. Sync again with the ID -> should be empty
    response = self.client.patch(
      "/api/notifications/sync",
      data={"already_synced_ids": [notif_id]},
      headers={"Authorization": f"Bearer {self.credentials['access']}"},
    )
    self.assertEqual(response.status_code, 200)
    self.assertEqual(len(response.json()), 0)

  def test_get_notification(self):
    notif = NotificationService.create(
      str(self.user.id),
      NotificationCreateReq(title="Get Me", message="M", deliver_at=timezone.now()),
    )
    response = self.client.get(
      f"/api/notifications/{notif['id']}",
      headers={"Authorization": f"Bearer {self.credentials['access']}"},
    )
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()["title"], "Get Me")

  def test_delete_notification(self):
    notif = NotificationService.create(
      str(self.user.id),
      NotificationCreateReq(title="Delete Me", message="M", deliver_at=timezone.now()),
    )
    response = self.client.delete(
      f"/api/notifications/{notif['id']}",
      headers={"Authorization": f"Bearer {self.credentials['access']}"},
    )
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.json()["success"])
