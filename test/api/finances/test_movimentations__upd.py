import uuid
from decimal import Decimal
from django.utils import timezone

from test.api.base import APIClient
from test.api.conftest import AuthenticatedTestCase
from apps.users.models import User
from apps.finances.models import MovGroup, Movimentation


class BaseMovimentationTestCase(AuthenticatedTestCase):
  """Helper setup for movimentation API tests."""

  user_create_data = {
    "name": "testuser_mov_upd",
    "email": "testapi_mov_upd@example.com",
    "password": "testpassword",
    "phone": "5584000000002",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testapi_mov_upd@example.com", "password": "testpassword"}
  URL_TEMPLATE = "/api/finances/groups/{movgroup_id}/movimentations/"

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

    self.mov_group_obj = MovGroup.objects.create(
      user=self.user,
      name="Movement Update Test Group",
      description="Desc test",
    )

    self.movimentation_obj = Movimentation.objects.create(
      mov_group=self.mov_group_obj,
      amount=Decimal("100.50"),
      balance="+",
      reason="Initial Movement",
      movemented_at=timezone.now(),
    )

    self.path_prefix = self.URL_TEMPLATE.format(movgroup_id=self.mov_group_obj.id)
    self.client = APIClient(path_prefix=self.path_prefix)

  def tearDown(self):
    super().tearDown()

  def _get_valid_token(self):
    return self.credentials["access"]


class MovimentationRoute_Update(BaseMovimentationTestCase):
  def test_update_movimentation_success_outcome_validation(self):
    token = self._get_valid_token()
    data = {
      "amount": 200.0,
      "balance": "-",
      "reason": "Updated Movement",
      "movemented_at": timezone.now().isoformat(),
    }

    res = self.client.put(
      f"{self.movimentation_obj.id}",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200, res.content.decode()[:500])
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["reason"], "Updated Movement")
    self.assertEqual(float(res_data["amount"]), 200.0)

  def test_update_movimentation_unauthenticated_returns_401(self):
    data = {
      "amount": 1.0,
      "balance": "+",
      "reason": "test",
      "movemented_at": timezone.now().isoformat(),
    }
    res = self.client.put(f"{self.movimentation_obj.id}", data=data)
    self.assertEqual(res.status_code, 401)

  def test_update_movimentation_invalid_id_returns_404(self):
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())
    data = {
      "amount": 1.0,
      "balance": "+",
      "reason": "test",
      "movemented_at": timezone.now().isoformat(),
    }

    res = self.client.put(
      f"{random_id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404, res.content.decode()[:500])

  def test_update_movimentation_invalid_user_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()
    data = {
      "amount": 1.0,
      "balance": "+",
      "reason": "test",
      "movemented_at": timezone.now().isoformat(),
    }

    res = self.client.put(
      f"{self.movimentation_obj.id}",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 403)
    self.user.is_email_valid = True
    self.user.save()


class MovimentationRoute_PartialUpdate(BaseMovimentationTestCase):
  def test_partial_update_movimentation_success_outcome_validation(self):
    token = self._get_valid_token()
    data = {"reason": "Partially Updated"}

    res = self.client.patch(
      f"{self.movimentation_obj.id}",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200, res.content.decode()[:500])
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["reason"], "Partially Updated")
    self.assertEqual(float(res_data["amount"]), 100.50)  # Unchanged

  def test_partial_update_movimentation_unauthenticated_returns_401(self):
    res = self.client.patch(f"{self.movimentation_obj.id}", data={"reason": "test"})
    self.assertEqual(res.status_code, 401)

  def test_partial_update_movimentation_invalid_id_returns_404(self):
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.patch(
      f"{random_id}",
      data={"reason": "test"},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 404)

  def test_partial_update_movimentation_invalid_user_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()

    res = self.client.patch(
      f"{self.movimentation_obj.id}",
      data={"reason": "test"},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 403)
    self.user.is_email_valid = True
    self.user.save()


class MovimentationRoute_Delete(BaseMovimentationTestCase):
  def test_delete_movimentation_success_outcome_validation(self):
    token = self._get_valid_token()
    res = self.client.delete(
      f"{self.movimentation_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 200, res.content.decode()[:500])
    self.assertTrue(res.json()["success"])

    # Verify it's really gone
    self.assertFalse(
      Movimentation.objects.filter(id=self.movimentation_obj.id).exists()
    )

  def test_delete_movimentation_unauthenticated_returns_401(self):
    res = self.client.delete(f"{self.movimentation_obj.id}")
    self.assertEqual(res.status_code, 401)

  def test_delete_movimentation_invalid_id_returns_404(self):
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.delete(
      f"{random_id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)

  def test_delete_movimentation_invalid_user_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()

    res = self.client.delete(
      f"{self.movimentation_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)
    self.user.is_email_valid = True
    self.user.save()
