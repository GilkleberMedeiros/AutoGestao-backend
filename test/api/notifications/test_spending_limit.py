import os
from test.api.base import AuthenticatedTestCase
from apps.users.models import User
from apps.notifications.services.spending_limit import SpendingLimitNotificationService
from apps.notifications.schemas.spending_limit import SpendingLimitNotificationCreateReq
from apps.notifications.dto import NotificationPeriods


class TestSpendingLimitAPI(AuthenticatedTestCase):
  user_create_model = User
  user_create_data = {
    "name": "apispending",
    "email": "apispending@example.com",
    "password": "password123",
    "phone": "5584333333333",
    "is_email_valid": True,
  }
  login_data = {"email": "apispending@example.com", "password": "password123"}

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

  def test_create_spending_limit(self):
    payload = {
      "title": "Monthly Cap",
      "message": "Limit hit",
      "threshold": 1000.0,
      "period": NotificationPeriods.MONTHLY,
    }
    response = self.client.post(
      "/api/notifications/spending-limits/",
      data=payload,
      headers={"Authorization": f"Bearer {self.credentials['access']}"},
    )
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(data["threshold"], 1000.0)
    self.assertEqual(data["period"], NotificationPeriods.MONTHLY)

  def test_patch_spending_limit(self):
    notif = SpendingLimitNotificationService.create(
      str(self.user.id),
      SpendingLimitNotificationCreateReq(
        title="Original", message="M", threshold=100.0, period=NotificationPeriods.WEEKLY
      ),
    )
    payload = {"threshold": 200.0}
    response = self.client.patch(
      f"/api/notifications/spending-limits/{notif['id']}",
      data=payload,
      headers={"Authorization": f"Bearer {self.credentials['access']}"},
    )
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()["threshold"], 200.0)

  def test_delete_spending_limit(self):
    notif = SpendingLimitNotificationService.create(
      str(self.user.id),
      SpendingLimitNotificationCreateReq(
        title="To Delete", message="M", threshold=100.0, period=NotificationPeriods.WEEKLY
      ),
    )
    response = self.client.delete(
      f"/api/notifications/spending-limits/{notif['id']}",
      headers={"Authorization": f"Bearer {self.credentials['access']}"},
    )
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.json()["success"])
