import uuid
from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.projects_and_clients.models import Client, ClientPhone


class BasePhoneTestCase(AuthenticatedTestCase):
  """Helper setup for phone API tests (modifying operations)."""

  user_create_data = {
    "name": "testuser",
    "email": "testapi_up@example.com",
    "password": "testpassword",
    "phone": "5584000000000",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testapi_up@example.com", "password": "testpassword"}
  URL = "/api/clients/"

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

    # Recreate a client for each test to ensure a clean state
    self.client_obj = Client.objects.create(
      user=self.user, name="Api Test Client", cpf="12345678903"
    )

    # Create an initial phone for update/delete tests
    self.phone_obj = ClientPhone.objects.create(
      client=self.client_obj, phone="5511999999999"
    )

  def tearDown(self):
    self.client_obj.delete()
    super().tearDown()

  def _get_valid_token(self):
    return self.credentials["access"]


class PhonesRoute_Update(BasePhoneTestCase):
  def test_update_phone_success_outcome_validation(self):
    """Test if route can update an existing phone."""
    token = self._get_valid_token()
    data = {"phone": "11988888888"}

    res = self.client.put(
      f"phones/{self.phone_obj.id}",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["phone"], "+55 (11) 9 8888-8888")
    self.assertEqual(res_data["id"], str(self.phone_obj.id))

  def test_update_phone_unauthenticated_returns_401(self):
    """Test authentication gating."""
    data = {"phone": "11988888888"}
    res = self.client.put(f"phones/{self.phone_obj.id}", data=data)
    self.assertEqual(res.status_code, 401)

  def test_update_phone_invalid_id_returns_404(self):
    """Test if route returns 404 for a non-existent phone."""
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())
    data = {"phone": "11988888888"}

    res = self.client.put(
      f"phones/{random_id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)

  def test_update_phone_invalid_data_returns_422(self):
    """Test validation error for malformed phone."""
    token = self._get_valid_token()
    data = {"phone": "not-a-phone"}

    res = self.client.put(
      f"phones/{self.phone_obj.id}",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)


class PhonesRoute_Delete(BasePhoneTestCase):
  def test_delete_phone_success_outcome_validation(self):
    """Test if route can delete an existing phone."""
    token = self._get_valid_token()

    res = self.client.delete(
      f"phones/{self.phone_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data.get("success"), True)

    # Verify it's actually gone from the database
    self.assertFalse(ClientPhone.objects.filter(id=self.phone_obj.id).exists())

  def test_delete_phone_unauthenticated_returns_401(self):
    """Test authentication gating."""
    res = self.client.delete(f"phones/{self.phone_obj.id}")
    self.assertEqual(res.status_code, 401)

  def test_delete_phone_invalid_id_returns_404(self):
    """Test if route returns 404 for a non-existent phone."""
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.delete(
      f"phones/{random_id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)
