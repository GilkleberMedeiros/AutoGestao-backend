import uuid
from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.finances.models import FinGroup


class BaseFinGroupRouteTest(AuthenticatedTestCase):
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


class FinGroupRoute_Create(BaseFinGroupRouteTest):
  def test_create_fingroup_success(self):
    token = self._get_valid_token()
    data = {"name": "New Group", "relation": "PERSONAL"}
    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 201)
    self.assertEqual(res.json()["name"], "New Group")

  def test_create_fingroup_unauthenticated(self):
    res = self.client.post("", data={"name": "New Group"})
    self.assertEqual(res.status_code, 401)


class FinGroupRoute_List(BaseFinGroupRouteTest):
  def test_list_fingroups_success(self):
    token = self._get_valid_token()
    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200)
    self.assertIn("items", res.json())


class FinGroupRoute_Get(BaseFinGroupRouteTest):
  def test_get_fingroup_success(self):
    token = self._get_valid_token()
    res = self.client.get(
      f"{self.fingroup_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["name"], "Test Group")

  def test_get_fingroup_not_found(self):
    token = self._get_valid_token()
    res = self.client.get(
      f"{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)


class FinGroupRoute_Update(BaseFinGroupRouteTest):
  def test_update_fingroup_success(self):
    fg = FinGroup.objects.create(user=self.user, name="Before")
    token = self._get_valid_token()
    data = {"name": "After", "relation": "PERSONAL"}
    res = self.client.put(
      f"{fg.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["name"], "After")


class FinGroupRoute_Delete(BaseFinGroupRouteTest):
  def test_delete_fingroup_success(self):
    fg = FinGroup.objects.create(user=self.user, name="Bye")
    token = self._get_valid_token()
    res = self.client.delete(
      f"{fg.id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

  def test_delete_fingroup_not_found(self):
    token = self._get_valid_token()
    res = self.client.delete(
      f"{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)
