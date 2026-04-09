from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User


class DashboardRouteTest(AuthenticatedTestCase):
  user_create_data = {
    "name": "testuser",
    "email": "testapi@example.com",
    "password": "testpassword",
    "phone": "5584000000000",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testapi@example.com", "password": "testpassword"}
  URL = "/api/dashboard/"

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

  @classmethod
  def tearDownClass(cls):
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def setUp(self):
    super().setUp()
    self.client = APIClient(path_prefix=self.URL)

  def _get_valid_token(self):
    return self.credentials["access"]

  def test_get_summary_success(self):
    token = self._get_valid_token()
    res = self.client.get("summary", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200)
    self.assertIn("total_profit", res.json())

  def test_get_rankings_success(self):
    token = self._get_valid_token()
    res = self.client.get("rankings", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200)
    self.assertIn("highest_gain", res.json())

  def test_get_income_composition_success(self):
    token = self._get_valid_token()
    res = self.client.get("income-composition", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200)
    self.assertIsInstance(res.json(), list)

  def test_get_profitability_history_success(self):
    token = self._get_valid_token()
    res = self.client.get("profitability-history", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200)
    self.assertIsInstance(res.json(), list)

  def test_unauthenticated_fails(self):
    res = self.client.get("summary")
    self.assertEqual(res.status_code, 401)
