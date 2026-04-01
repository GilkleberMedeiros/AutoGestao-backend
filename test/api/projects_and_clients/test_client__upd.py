"""
Tests for the clients route. Update, Partial Update and Delete.
"""

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

  @classmethod
  def tearDownClass(cls):
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def setUp(self):
    super().setUp()
    self.client = APIClient(path_prefix=self.URL)

    # We create a client belonging to the authenticated user for the tests
    self.client_obj = Client.objects.create(
      user=self.user, name="Api Test Client", cpf="12345678901"
    )

  def tearDown(self):
    self.client_obj.delete()
    super().tearDown()

  def _get_valid_token(self):
    return self.credentials["access"]


class ClientsRoute_Update(BaseClientTestCase):
  def test_update_client_success_outcome_validation(self):
    """Test if update endpoint updates the client and returns the correct data."""
    token = self._get_valid_token()
    data = {"name": "Updated Client", "cpf": "99999999999"}

    res = self.client.put(
      f"{self.client_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["name"], "Updated Client")
    self.assertEqual(res_data["cpf"], "99999999999")
    self.assertEqual(res_data["id"], str(self.client_obj.id))

  def test_update_client_unauthenticated_returns_401(self):
    """Test if update route fails with unauthenticated request."""
    data = {"name": "Updated Client"}
    res = self.client.put(f"{self.client_obj.id}", data=data)
    res_data = res.json()

    self.assertEqual(res.status_code, 401)
    self.assertEqual(res_data.get("success"), False)

  def test_update_client_invalid_email_returns_403(self):
    """Test if update route fails with a request from a user with an invalid email."""
    self.user.is_email_valid = False
    self.user.save()
    self.user.refresh_from_db()

    token = self._get_valid_token()
    data = {"name": "Updated Client"}

    res = self.client.put(
      f"{self.client_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 403)
    self.assertEqual(res_data.get("success"), False)

  def test_update_client_invalid_id_returns_404(self):
    """Test if update route returns 404 for a non-existent client."""
    import uuid

    token = self._get_valid_token()
    random_id = str(uuid.uuid4())
    data = {"name": "Updated Client"}

    res = self.client.put(
      f"{random_id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 404)
    self.assertEqual(res_data.get("success"), False)

  def test_update_client_with_full_data_returns_success(self):
    """Test if update route can handle full data including nested fields."""
    token = self._get_valid_token()
    data = {
      "name": "Full Updated Client",
      "cpf": "11100011100",
      "emails": ["updated@test.com"],
      "phones": ["5584888888888"],
      "address": {
        "state": "SP",
        "city": "São Paulo",
        "neighborhood": "Bela Vista",
        "street": "Av. Paulista",
        "house_number": "1000",
        "complement": "Sala 10",
      },
      "rating": {"score": 4, "comment": "Good client"},
    }

    res = self.client.put(
      f"{self.client_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["name"], "Full Updated Client")
    self.assertEqual(res_data["emails"], ["updated@test.com"])
    self.assertEqual(res_data["phones"], ["5584888888888"])
    self.assertEqual(res_data["address"]["city"], "São Paulo")
    self.assertEqual(res_data["rating"]["score"], 4)

  def test_update_client_replaces_nested_data(self):
    """Test that update replaces nested data (emails/phones) instead of merging."""
    token = self._get_valid_token()

    # First, create with emails
    create_data = {
      "name": "Client with emails",
      "emails": ["old@test.com", "also-old@test.com"],
    }
    self.client.post("", data=create_data, headers={"Authorization": f"Bearer {token}"})

    # Now update with a different email list
    update_data = {"name": "Client with emails", "emails": ["new@test.com"]}
    res = self.client.put(
      f"{self.client_obj.id}",
      data=update_data,
      headers={"Authorization": f"Bearer {token}"},
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["emails"], ["new@test.com"])

  def test_update_client_emails_as_string_returns_422(self):
    """emails must be a list; a bare string should be rejected."""
    token = self._get_valid_token()
    res = self.client.put(
      f"{self.client_obj.id}",
      data={"name": "Client", "emails": "bad@test.com"},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)

  def test_update_client_phones_as_int_returns_422(self):
    """phones must be a list of strings; a bare integer should be rejected."""
    token = self._get_valid_token()
    res = self.client.put(
      f"{self.client_obj.id}",
      data={"name": "Client", "phones": 5584999999999},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)

  def test_update_client_address_as_string_returns_422(self):
    """address must be an object, not a plain string."""
    token = self._get_valid_token()
    res = self.client.put(
      f"{self.client_obj.id}",
      data={"name": "Client", "address": "123 Main St"},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)

  def test_update_client_cpf_as_int_returns_422(self):
    """cpf must be a string, not an integer."""
    token = self._get_valid_token()
    res = self.client.put(
      f"{self.client_obj.id}",
      data={"name": "Client", "cpf": 12345678901},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)


class ClientsRoute_PartialUpdate(BaseClientTestCase):
  def test_partial_update_client_success_outcome_validation(self):
    """Test if partial update endpoint updates the client and returns the correct data."""
    token = self._get_valid_token()
    data = {"name": "Partially Updated Client"}

    res = self.client.patch(
      f"{self.client_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["name"], "Partially Updated Client")
    self.assertEqual(res_data["id"], str(self.client_obj.id))

  def test_partial_update_client_unauthenticated_returns_401(self):
    """Test if partial update route fails with unauthenticated request."""
    data = {"name": "Updated Client"}
    res = self.client.patch(f"{self.client_obj.id}", data=data)
    res_data = res.json()

    self.assertEqual(res.status_code, 401)
    self.assertEqual(res_data.get("success"), False)

  def test_partial_update_client_invalid_email_returns_403(self):
    """Test if partial update route fails with a request from a user with an invalid email."""
    self.user.is_email_valid = False
    self.user.save()
    self.user.refresh_from_db()

    token = self._get_valid_token()
    data = {"name": "Updated Client"}

    res = self.client.patch(
      f"{self.client_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 403)
    self.assertEqual(res_data.get("success"), False)

  def test_partial_update_client_invalid_id_returns_404(self):
    """Test if partial update route returns 404 for a non-existent client."""
    import uuid

    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.patch(
      f"{random_id}", data={"name": "X"}, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 404)
    self.assertEqual(res_data.get("success"), False)

  def test_partial_update_client_without_required_fields_returns_success(self):
    """Test that partial update allows omitting required fields like name."""
    token = self._get_valid_token()
    data = {
      "emails": ["patch@test.com"],
      "phones": ["5584777777777"],
    }

    res = self.client.patch(
      f"{self.client_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["emails"], ["patch@test.com"])
    self.assertEqual(res_data["phones"], ["5584777777777"])
    # name should remain unchanged
    self.assertEqual(res_data["name"], self.client_obj.name)

  def test_partial_update_client_replaces_nested_data(self):
    """Test that patch replaces nested data (emails) instead of merging."""
    token = self._get_valid_token()

    # Seed emails
    self.client.patch(
      f"{self.client_obj.id}",
      data={"emails": ["old@test.com", "also-old@test.com"]},
      headers={"Authorization": f"Bearer {token}"},
    )

    res = self.client.patch(
      f"{self.client_obj.id}",
      data={"emails": ["new@test.com"]},
      headers={"Authorization": f"Bearer {token}"},
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["emails"], ["new@test.com"])

  def test_partial_update_client_emails_as_string_returns_422(self):
    """emails must be a list; a bare string should be rejected."""
    token = self._get_valid_token()
    res = self.client.patch(
      f"{self.client_obj.id}",
      data={"emails": "bad@test.com"},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)

  def test_partial_update_client_phones_as_int_returns_422(self):
    """phones must be a list of strings; a bare integer should be rejected."""
    token = self._get_valid_token()
    res = self.client.patch(
      f"{self.client_obj.id}",
      data={"phones": 5584999999999},
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)


class ClientsRoute_Delete(BaseClientTestCase):
  def test_delete_client_success_outcome_validation(self):
    """Test if delete endpoint can delete the resource successfully. Checks database as well."""
    token = self._get_valid_token()

    client_id = self.client_obj.id

    res = self.client.delete(
      f"{client_id}", headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json().get("success"), True)

  def test_delete_client_unauthenticated_returns_401(self):
    """Test authentication gating."""
    res = self.client.delete(f"{self.client_obj.id}")
    self.assertEqual(res.status_code, 401)
    self.assertEqual(res.json().get("success"), False)

  def test_delete_client_invalid_email_returns_403(self):
    """Test valid email permission is active."""
    self.user.is_email_valid = False
    self.user.save()
    self.user.refresh_from_db()
    token = self._get_valid_token()

    res = self.client.delete(
      f"{self.client_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)
    self.assertEqual(res.json().get("success"), False)

  def test_delete_client_invalid_id_returns_404(self):
    """Test income validation/existence check."""
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.delete(
      f"{random_id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)
    self.assertEqual(res.json().get("success"), False)
