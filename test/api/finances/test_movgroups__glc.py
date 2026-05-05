import uuid
from test.api.base import APIClient
from test.api.conftest import AuthenticatedTestCase
from apps.users.models import User
from apps.finances.models import MovGroup


class BaseMovGroupTestCase(AuthenticatedTestCase):
  """Helper setup for mov_group API tests."""

  user_create_data = {
    "name": "testuser",
    "email": "testapi@example.com",
    "password": "testpassword",
    "phone": "5584000000000",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testapi@example.com", "password": "testpassword"}
  URL = "/api/finances/groups/"

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

    cls.mov_group_obj = MovGroup.objects.create(
      user=cls.user,
      name="Api Test Group",
      description="Desc test",
    )

  @classmethod
  def tearDownClass(cls):
    cls.mov_group_obj.delete()
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def setUp(self):
    super().setUp()
    self.client = APIClient(path_prefix=self.URL)

  def tearDown(self):
    super().tearDown()

  def _get_valid_token(self):
    return self.credentials["access"]


class MovGroupRoute_List(BaseMovGroupTestCase):
  def test_list_mov_groups_success_outcome_validation(self):
    token = self._get_valid_token()

    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertIsInstance(data, dict)
    self.assertIn("items", data)
    self.assertIsInstance(data["items"], list)
    self.assertEqual(len(data["items"]), 1)

    group_data = data["items"][0]
    self.assertEqual(group_data["name"], "Api Test Group")
    self.assertEqual(group_data["id"], str(self.mov_group_obj.id))

  def test_list_mov_groups_unauthenticated_returns_401(self):
    res = self.client.get("")
    self.assertEqual(res.status_code, 401)

  def test_list_mov_groups_invalid_user_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()
    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    data = res.json()
    self.assertEqual(res.status_code, 403)
    self.assertEqual(data.get("success"), False)


class MovGroupRoute_Get(BaseMovGroupTestCase):
  def test_get_mov_group_success_outcome_validation(self):
    token = self._get_valid_token()
    res = self.client.get(
      f"{self.mov_group_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 200)
    data = res.json()
    self.assertEqual(data["name"], "Api Test Group")
    self.assertEqual(data["id"], str(self.mov_group_obj.id))

  def test_get_mov_group_unauthenticated_returns_401(self):
    res = self.client.get(f"{self.mov_group_obj.id}")
    self.assertEqual(res.status_code, 401)

  def test_get_mov_group_invalid_user_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()
    res = self.client.get(
      f"{self.mov_group_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )
    data = res.json()
    self.assertEqual(res.status_code, 403)
    self.assertEqual(data.get("success"), False)

  def test_get_mov_group_invalid_id_returns_404(self):
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.get(f"{random_id}", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 404)


class MovGroupRoute_Create(BaseMovGroupTestCase):
  def test_create_mov_group_success_outcome_validation(self):
    token = self._get_valid_token()
    data = {
      "name": "New Group",
      "description": "test desc",
    }

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertEqual(res_data["name"], "New Group")
    self.assertIn("id", res_data)

  def test_create_mov_group_unauthenticated_returns_401(self):
    data = {
      "name": "New Group 2",
      "description": "test",
    }
    res = self.client.post("", data=data)
    self.assertEqual(res.status_code, 401)

  def test_create_mov_group_invalid_user_email_returns_403(self):
    token = self._get_valid_token()
    data = {
      "name": "New Group 3",
      "description": "test",
    }
    self.user.is_email_valid = False
    self.user.save()
    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()
    self.assertEqual(res.status_code, 403)
    self.assertEqual(res_data.get("success"), False)

  def test_create_mov_group_already_exists_returns_400(self):
    token = self._get_valid_token()
    data = {
      "name": "Api Test Group",  # Same name as self.mov_group_obj
      "description": "test desc",
    }

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 400)
    res_data = res.json()
    self.assertEqual(res_data.get("success"), False)
