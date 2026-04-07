import uuid
from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.projects_and_clients.models import Client, ClientPhone


class BasePhoneTestCase(AuthenticatedTestCase):
  """Helper setup for phone API tests."""

  user_create_data = {
    "name": "testuser",
    "email": "testapi_p@example.com",
    "password": "testpassword",
    "phone": "5584000000000",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testapi_p@example.com", "password": "testpassword"}
  URL = "/api/clients/"

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

    # Create a client belonging to the authenticated user
    cls.client_obj = Client.objects.create(
      user=cls.user, name="Api Test Client", cpf="12345678902"
    )

    # Create some initial phones for listing tests
    cls.phone1 = ClientPhone.objects.create(
      client=cls.client_obj, phone="5511911111111"
    )
    cls.phone2 = ClientPhone.objects.create(
      client=cls.client_obj, phone="5511922222222"
    )

  @classmethod
  def tearDownClass(cls):
    cls.client_obj.delete()
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def setUp(self):
    super().setUp()
    self.client = APIClient(path_prefix=self.URL)

  def _get_valid_token(self):
    return self.credentials["access"]


class PhonesRoute_List(BasePhoneTestCase):
  def test_list_phones_success_outcome_validation(self):
    """Test if list endpoint returns correctly structured PaginatedAPIResponse[ClientPhoneSchema] instances."""
    token = self._get_valid_token()

    res = self.client.get(
      f"{self.client_obj.id}/phones", headers={"Authorization": f"Bearer {token}"}
    )
    data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertIsInstance(data, dict)
    self.assertIn("items", data)
    self.assertIsInstance(data["items"], list)
    self.assertEqual(len(data["items"]), 2)
    self.assertEqual(data["total_count"], 2)

    # Verify outcome data structure matches ClientPhoneSchema
    phones = {p["phone"]: p for p in data["items"]}
    self.assertIn("+55 (11) 9 1111-1111", phones)
    self.assertIn("+55 (11) 9 2222-2222", phones)
    self.assertEqual(phones["+55 (11) 9 1111-1111"]["id"], str(self.phone1.id))

  def test_list_phones_unauthenticated_returns_401(self):
    """Test authentication gating."""
    res = self.client.get(f"{self.client_obj.id}/phones")
    self.assertEqual(res.status_code, 401)
    data = res.json()
    self.assertEqual(data.get("success"), False)

  def test_list_phones_invalid_client_returns_404(self):
    """Test if route returns 404 for a non-existent client."""
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.get(
      f"{random_id}/phones", headers={"Authorization": f"Bearer {token}"}
    )
    data = res.json()

    self.assertEqual(res.status_code, 404)
    self.assertEqual(data.get("success"), False)
    self.assertIn("Client", data.get("details", ""))


class PhonesRoute_Create(BasePhoneTestCase):
  def test_create_phone_success_outcome_validation(self):
    """Test if route can add a new phone successfully."""
    token = self._get_valid_token()
    data = {"phone": "11933333333"}

    res = self.client.post(
      f"{self.client_obj.id}/phones",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    # The normalization happens in the schema or service, so it should be FULLPLAIN
    self.assertEqual(res_data["phone"], "+55 (11) 9 3333-3333")
    self.assertIn("id", res_data)

    # Verify it's actually in the database for THIS client
    self.assertTrue(
      ClientPhone.objects.filter(id=res_data["id"], client=self.client_obj).exists()
    )

  def test_create_phone_unauthenticated_returns_401(self):
    """Test authentication gating."""
    data = {"phone": "11933333333"}
    res = self.client.post(f"{self.client_obj.id}/phones", data=data)
    self.assertEqual(res.status_code, 401)

  def test_create_phone_invalid_client_returns_404(self):
    """Test if route returns 404 for a non-existent client."""
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())
    data = {"phone": "11933333333"}

    res = self.client.post(
      f"{random_id}/phones", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)

  def test_create_phone_invalid_data_returns_422(self):
    """Test validation error for malformed phone."""
    token = self._get_valid_token()
    data = {"phone": "not-a-phone"}

    res = self.client.post(
      f"{self.client_obj.id}/phones",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)
