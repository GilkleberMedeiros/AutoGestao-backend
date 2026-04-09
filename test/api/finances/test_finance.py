import uuid
from decimal import Decimal
from django.utils import timezone
from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.finances.models import FinGroup, Finance


class BaseFinanceRouteTest(AuthenticatedTestCase):
  user_create_data = {
    "name": "testuser",
    "email": "testapi@example.com",
    "password": "testpassword",
    "phone": "5584000000000",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testapi@example.com", "password": "testpassword"}
  URL = "/api/fingroups/"

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

    cls.fingroup_obj = FinGroup.objects.create(
      user=cls.user, name="Test Group", relation="PERSONAL"
    )

  @classmethod
  def tearDownClass(cls):
    cls.fingroup_obj.delete()
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def setUp(self):
    super().setUp()
    self.client = APIClient(path_prefix=self.URL)

  def _get_valid_token(self):
    return self.credentials["access"]


class FinanceRoute_Create(BaseFinanceRouteTest):
  def test_create_finance_success(self):
    token = self._get_valid_token()
    data = {
      "amount": "100.50",
      "balance": "POSITIVE",
      "reason": "Test",
      "movemented_at": timezone.now().isoformat(),
    }
    res = self.client.post(
      f"{self.fingroup_obj.id}/finances",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 201)
    self.assertEqual(res.json()["reason"], "Test")


class FinanceRoute_List(BaseFinanceRouteTest):
  def test_list_finances_success(self):
    Finance.objects.create(
      fingroup=self.fingroup_obj,
      amount=Decimal("10.00"),
      balance="POSITIVE",
      reason="R1",
      movemented_at=timezone.now(),
    )
    token = self._get_valid_token()
    res = self.client.get(
      f"{self.fingroup_obj.id}/finances",
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)
    self.assertIn("items", res.json())


class FinanceRoute_Get(BaseFinanceRouteTest):
  def test_get_finance_success(self):
    fin = Finance.objects.create(
      fingroup=self.fingroup_obj,
      amount=Decimal("10.00"),
      balance="POSITIVE",
      reason="R1",
      movemented_at=timezone.now(),
    )
    token = self._get_valid_token()
    res = self.client.get(
      f"{self.fingroup_obj.id}/finances/{fin.id}",
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["reason"], "R1")

  def test_get_not_found(self):
    token = self._get_valid_token()
    res = self.client.get(
      f"{self.fingroup_obj.id}/finances/{uuid.uuid4()}",
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 404)


class FinanceRoute_Update(BaseFinanceRouteTest):
  def test_update_finance_success(self):
    fin = Finance.objects.create(
      fingroup=self.fingroup_obj,
      amount=Decimal("10.00"),
      balance="POSITIVE",
      reason="Before",
      movemented_at=timezone.now(),
    )
    token = self._get_valid_token()
    data = {
      "amount": "20.00",
      "balance": "POSITIVE",
      "reason": "After",
      "movemented_at": timezone.now().isoformat(),
    }
    res = self.client.put(
      f"{self.fingroup_obj.id}/finances/{fin.id}",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["reason"], "After")


class FinanceRoute_Delete(BaseFinanceRouteTest):
  def test_delete_finance_success(self):
    fin = Finance.objects.create(
      fingroup=self.fingroup_obj,
      amount=Decimal("10.00"),
      balance="POSITIVE",
      reason="Bye",
      movemented_at=timezone.now(),
    )
    token = self._get_valid_token()
    res = self.client.delete(
      f"{self.fingroup_obj.id}/finances/{fin.id}",
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)
