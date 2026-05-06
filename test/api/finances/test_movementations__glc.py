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
    "name": "testuser_mov",
    "email": "testapi_mov@example.com",
    "password": "testpassword",
    "phone": "5584000000001",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testapi_mov@example.com", "password": "testpassword"}
  URL_TEMPLATE = "/api/finances/groups/{movgroup_id}/movementations/"

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

    cls.mov_group_obj = MovGroup.objects.create(
      user=cls.user,
      name="Movement Test Group",
      description="Desc test",
    )

    cls.movimentation_obj = Movimentation.objects.create(
      mov_group=cls.mov_group_obj,
      amount=Decimal("100.50"),
      balance="+",
      reason="Initial Movement",
      movemented_at=timezone.now(),
    )

  @classmethod
  def tearDownClass(cls):
    cls.movimentation_obj.delete()
    cls.mov_group_obj.delete()
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def setUp(self):
    super().setUp()
    self.path_prefix = self.URL_TEMPLATE.format(movgroup_id=self.mov_group_obj.id)
    self.client = APIClient(path_prefix=self.path_prefix)

  def tearDown(self):
    super().tearDown()

  def _get_valid_token(self):
    return self.credentials["access"]


class MovimentationRoute_List(BaseMovimentationTestCase):
  def test_list_movimentations_success_outcome_validation(self):
    token = self._get_valid_token()

    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200, res.content.decode()[:500])
    data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertIsInstance(data, dict)
    self.assertIn("items", data)
    self.assertEqual(len(data["items"]), 1)

    mov_data = data["items"][0]
    self.assertEqual(mov_data["reason"], "Initial Movement")
    self.assertEqual(float(mov_data["amount"]), 100.50)
    self.assertEqual(mov_data["id"], str(self.movimentation_obj.id))

  def test_list_movimentations_with_group_filter_success(self):
    token = self._get_valid_token()

    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200, res.content.decode()[:500])
    data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(len(data["items"]), 1)

  def test_list_movimentations_unauthenticated_returns_401(self):
    res = self.client.get("")
    self.assertEqual(res.status_code, 401)

  def test_list_movimentations_invalid_user_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()

    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 403)
    self.user.is_email_valid = True
    self.user.save()


class MovimentationRoute_Get(BaseMovimentationTestCase):
  def test_get_movimentation_success_outcome_validation(self):
    token = self._get_valid_token()
    res = self.client.get(
      f"{self.movimentation_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 200, res.content.decode()[:500])
    data = res.json()
    self.assertEqual(data["reason"], "Initial Movement")
    self.assertEqual(data["id"], str(self.movimentation_obj.id))

  def test_get_movimentation_unauthenticated_returns_401(self):
    res = self.client.get(f"{self.movimentation_obj.id}")
    self.assertEqual(res.status_code, 401)

  def test_get_movimentation_invalid_id_returns_404(self):
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.get(f"{random_id}", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 404, res.content.decode()[:500])

  def test_get_movimentation_invalid_user_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()

    res = self.client.get(
      f"{self.movimentation_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)
    self.user.is_email_valid = True
    self.user.save()


class MovimentationRoute_Create(BaseMovimentationTestCase):
  def test_create_movimentation_success_outcome_validation(self):
    token = self._get_valid_token()
    data = {
      "amount": 50.0,
      "balance": "-",
      "reason": "New Movement",
      "movemented_at": timezone.now().isoformat(),
    }

    res = self.client.post(
      "", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 201, res.content.decode()[:500])
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertEqual(res_data["reason"], "New Movement")
    self.assertEqual(float(res_data["amount"]), 50.0)
    self.assertIn("id", res_data)

  def test_create_movimentation_unauthenticated_returns_401(self):
    data = {
      "amount": 10.0,
      "balance": "+",
      "reason": "Unauth Test",
      "movemented_at": timezone.now().isoformat(),
    }
    res = self.client.post("", data=data)
    self.assertEqual(res.status_code, 401)

  def test_create_movimentation_invalid_group_id_returns_404(self):
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())
    data = {
      "amount": 10.0,
      "balance": "+",
      "reason": "Invalid Group Test",
      "movemented_at": timezone.now().isoformat(),
    }

    prefix = self.URL_TEMPLATE.format(movgroup_id=random_id)
    res = self.client.post(
      prefix, data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)

  def test_create_movimentation_invalid_user_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()
    data = {
      "amount": 10.0,
      "balance": "+",
      "reason": "Email Test",
      "movemented_at": timezone.now().isoformat(),
    }

    res = self.client.post(
      "", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)
    self.user.is_email_valid = True
    self.user.save()
