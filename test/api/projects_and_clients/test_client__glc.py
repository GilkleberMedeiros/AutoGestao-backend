import uuid
from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.projects_and_clients.models import Client


class BaseClientTestCase(AuthenticatedTestCase):
  """Helper setup for client API tests."""

  user_create_data = {
    "name": "testuser",
    "email": "testapi@example.com",
    "password": "testpassword",
    "phone": "5584000000000",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testapi@example.com", "password": "testpassword"}
  URL = "/api/clients/"

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

    # We create a client belonging to the authenticated user for the tests
    cls.client_obj = Client.objects.create(
      user=cls.user, name="Api Test Client", cpf="12345678901"
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

  def tearDown(self):
    super().tearDown()

  def _get_valid_token(self):
    return self.credentials["access"]


class ClientsRoute_List(BaseClientTestCase):
  def test_list_clients_success_outcome_validation(self):
    """Test if list endpoint returns correctly structured ClientSchema instances."""
    token = self._get_valid_token()

    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertIsInstance(data, dict)
    self.assertIn("items", data)
    self.assertIsInstance(data["items"], list)
    self.assertEqual(len(data["items"]), 1)

    # Verify outcome data structure matches ClientSchema
    client_data = data["items"][0]
    self.assertEqual(client_data["name"], "Api Test Client")
    self.assertEqual(client_data["cpf"], "12345678901")
    self.assertEqual(client_data["id"], str(self.client_obj.id))
    self.assertIn("emails", client_data)
    self.assertIn("phones", client_data)
    self.assertIn("address", client_data)
    self.assertIn("rating", client_data)

  def test_list_clients_unauthenticated_returns_401(self):
    """Test authentication gating."""
    res = self.client.get("")
    self.assertEqual(res.status_code, 401)
    data = res.json()

    self.assertEqual(data.get("success"), False)

  def test_list_clients_invalid_email_returns_403(self):
    """Test valid email permission is active."""
    self.user.is_email_valid = False  # Set False to ensure invalid email.
    self.user.save()
    self.user.refresh_from_db()
    token = self._get_valid_token()

    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    data = res.json()

    self.assertEqual(res.status_code, 403)
    self.assertEqual(data.get("success"), False)


class ClientsRoute_Get(BaseClientTestCase):
  def test_get_client_success_outcome_validation(self):
    """Test if get endpoint returns correctly structured ClientSchema instance."""
    token = self._get_valid_token()
    res = self.client.get(
      f"{self.client_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 200)
    data = res.json()

    # Verify outcome data structure matches ClientSchema
    self.assertEqual(data["name"], "Api Test Client")
    self.assertEqual(data["cpf"], "12345678901")
    self.assertEqual(data["id"], str(self.client_obj.id))
    self.assertIn("emails", data)
    self.assertIn("phones", data)
    self.assertIn("address", data)
    self.assertIn("rating", data)

  def test_get_client_unauthenticated_returns_401(self):
    """Test authentication gating."""

    res = self.client.get(f"{self.client_obj.id}")
    self.assertEqual(res.status_code, 401)
    data = res.json()

    self.assertEqual(data.get("success"), False)

  def test_list_clients_invalid_email_returns_403(self):
    """Test valid email permission is active."""
    self.user.is_email_valid = False  # Set False to ensure invalid email.
    self.user.save()
    self.user.refresh_from_db()
    token = self._get_valid_token()

    res = self.client.get(
      f"{self.client_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )
    data = res.json()

    self.assertEqual(res.status_code, 403)
    self.assertEqual(data.get("success"), False)

  def test_get_client_invalid_id_returns_404(self):
    """Test income validation/existence check."""
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.get(f"{random_id}", headers={"Authorization": f"Bearer {token}"})
    data = res.json()

    self.assertEqual(res.status_code, 404)
    self.assertEqual(data.get("success"), False)


class ClientsRoute_Create(BaseClientTestCase):
  def test_create_client_success_outcome_validation(self):
    """Test if route can create the resource successfully and returns the correct status with the apropriated resource data."""
    token = self._get_valid_token()
    data = {"name": "New Client", "cpf": "11122233344"}

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertEqual(res_data["name"], "New Client")
    self.assertEqual(res_data["cpf"], "11122233344")
    self.assertIn("id", res_data)

  def test_create_client_unauthenticated_returns_401(self):
    """Test if route fails with unauthenticated request."""
    data = {"name": "New Client"}
    res = self.client.post("", data=data)
    res_data = res.json()

    self.assertEqual(res.status_code, 401)
    self.assertIn("success", res_data)
    self.assertEqual(res_data["success"], False)

  def test_create_client_invalid_email_returns_403(self):
    """Test if route fails with a request from a user with an invalid email."""
    self.user.is_email_valid = False
    self.user.save()
    self.user.refresh_from_db()
    token = self._get_valid_token()

    data = {"name": "New Client"}
    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()

    self.assertEqual(res.status_code, 403)
    self.assertEqual(res_data.get("success"), False)

  def test_create_client_with_full_data_returns_success(self):
    """Test if the route can handle a creation with full data, even that data that isn't required by the schema validation."""
    token = self._get_valid_token()
    data = {
      "name": "Full Client",
      "cpf": "99988877766",
      "emails": ["test@test.com", "other@test.com"],
      "phones": ["5584999999999"],
      "address": {
        "state": "RN",
        "city": "Natal",
        "neighborhood": "Centro",
        "street": "Rua Principal",
        "house_number": "100",
        "complement": "Apto 1",
      },
      "rating": {"score": 5, "comment": "Great client"},
    }

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertEqual(res_data["name"], "Full Client")
    self.assertEqual(res_data["emails"], ["test@test.com", "other@test.com"])
    self.assertEqual(res_data["phones"], ["5584999999999"])
    self.assertEqual(res_data["address"]["city"], "Natal")
    self.assertEqual(res_data["rating"]["score"], 5)

  def test_create_client_with_minimum_data_returns_success(self):
    """Test if the route can handle a creation with the minimum data, only the required."""
    token = self._get_valid_token()
    data = {"name": "Minimum Client"}

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertEqual(res_data["name"], "Minimum Client")
    self.assertIn(res_data.get("emails"), [None, []])
    self.assertIn(res_data.get("phones"), [None, []])
    self.assertIn(res_data.get("address"), [None, {}])
    self.assertIn(res_data.get("rating"), [None, {}])

  def test_create_client_missing_name_returns_422(self):
    """Test if route fails when the name isn't specified (this is the only data required)."""
    token = self._get_valid_token()
    data = {"cpf": "11122233344"}

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})

    self.assertEqual(res.status_code, 422)

  def test_create_client_emails_as_string_returns_422(self):
    """emails must be a list; a bare string should be rejected."""
    token = self._get_valid_token()
    res = self.client.post(
      "",
      data={"name": "Client", "emails": "bad@test.com"},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)

  def test_create_client_phones_as_int_returns_422(self):
    """phones must be a list of strings; a bare integer should be rejected."""
    token = self._get_valid_token()
    res = self.client.post(
      "",
      data={"name": "Client", "phones": 5584999999999},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)

  def test_create_client_address_as_string_returns_422(self):
    """address must be an object, not a plain string."""
    token = self._get_valid_token()
    res = self.client.post(
      "",
      data={"name": "Client", "address": "123 Main St"},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)

  def test_create_client_cpf_as_int_returns_422(self):
    """cpf must be a string, not an integer."""
    token = self._get_valid_token()
    res = self.client.post(
      "",
      data={"name": "Client", "cpf": 12345678901},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)
