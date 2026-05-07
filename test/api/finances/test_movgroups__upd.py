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

  @classmethod
  def tearDownClass(cls):
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


class MovGroupRoute_Update(BaseMovGroupTestCase):
  def test_update_mov_group_success(self):
    group = MovGroup.objects.create(
      user=self.user,
      name="Test Update",
      description="desc",
    )
    token = self._get_valid_token()
    data = {
      "name": "Updated Group",
      "description": "updated desc",
    }

    res = self.client.put(
      f"{group.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["name"], "Updated Group")
    self.assertEqual(res.json()["description"], "updated desc")

  def test_update_mov_group_already_exists_returns_400(self):
    MovGroup.objects.create(
      user=self.user,
      name="Existing Group",
      description="desc",
    )
    group = MovGroup.objects.create(
      user=self.user,
      name="Test Update",
      description="desc",
    )
    token = self._get_valid_token()
    data = {
      "name": "Existing Group",
      "description": "updated desc",
    }

    res = self.client.put(
      f"{group.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 400)
    self.assertEqual(res.json().get("success"), False)

  def test_update_mov_group_unauthenticated_returns_401(self):
    group = MovGroup.objects.create(
      user=self.user,
      name="Test Update",
      description="desc",
    )
    data = {
      "name": "Updated Group",
      "description": "updated desc",
    }
    res = self.client.put(f"{group.id}", data=data)
    self.assertEqual(res.status_code, 401)

  def test_update_mov_group_invalid_user_email_returns_403(self):
    group = MovGroup.objects.create(
      user=self.user,
      name="Test Update",
      description="desc",
    )
    token = self._get_valid_token()
    data = {
      "name": "Updated Group",
      "description": "updated desc",
    }
    self.user.is_email_valid = False
    self.user.save()
    res = self.client.put(
      f"{group.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()
    self.assertEqual(res.status_code, 403)
    self.assertEqual(res_data.get("success"), False)


class MovGroupRoute_PartialUpdate(BaseMovGroupTestCase):
  def test_partial_update_mov_group_success(self):
    group = MovGroup.objects.create(
      user=self.user,
      name="Test Update",
      description="desc",
    )
    token = self._get_valid_token()
    data = {"name": "Partially Updated Group"}

    res = self.client.patch(
      f"{group.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["name"], "Partially Updated Group")
    self.assertEqual(res.json()["description"], "desc")

  def test_partial_update_mov_group_already_exists_returns_400(self):
    MovGroup.objects.create(
      user=self.user,
      name="Existing Group",
      description="desc",
    )
    group = MovGroup.objects.create(
      user=self.user,
      name="Test Update",
      description="desc",
    )
    token = self._get_valid_token()
    data = {"name": "Existing Group"}

    res = self.client.patch(
      f"{group.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 400)
    self.assertEqual(res.json().get("success"), False)

  def test_partial_update_mov_group_unauthenticated_returns_401(self):
    group = MovGroup.objects.create(
      user=self.user,
      name="Test Update",
    )
    data = {"name": "Partially Updated Group"}
    res = self.client.patch(f"{group.id}", data=data)
    self.assertEqual(res.status_code, 401)

  def test_partial_update_mov_group_invalid_user_email_returns_403(self):
    group = MovGroup.objects.create(
      user=self.user,
      name="Test Update",
    )
    token = self._get_valid_token()
    data = {"name": "Partially Updated Group"}
    self.user.is_email_valid = False
    self.user.save()
    res = self.client.patch(
      f"{group.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()
    self.assertEqual(res.status_code, 403)
    self.assertEqual(res_data.get("success"), False)


class MovGroupRoute_Delete(BaseMovGroupTestCase):
  def test_delete_mov_group_success(self):
    group = MovGroup.objects.create(
      user=self.user,
      name="Test Delete",
    )
    token = self._get_valid_token()

    res = self.client.delete(
      f"{group.id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

  def test_delete_mov_group_not_found(self):
    token = self._get_valid_token()
    res = self.client.delete(
      f"{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)

  def test_delete_mov_group_unauthenticated_returns_401(self):
    group = MovGroup.objects.create(
      user=self.user,
      name="Test Delete",
    )
    res = self.client.delete(f"{group.id}")
    self.assertEqual(res.status_code, 401)

  def test_delete_mov_group_invalid_user_email_returns_403(self):
    group = MovGroup.objects.create(
      user=self.user,
      name="Test Delete",
    )
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()
    res = self.client.delete(
      f"{group.id}", headers={"Authorization": f"Bearer {token}"}
    )
    data = res.json()
    self.assertEqual(res.status_code, 403)
    self.assertEqual(data.get("success"), False)
