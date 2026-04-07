import uuid
from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.projects_and_clients.models import Client, ClientEmail


class BaseEmailTestCase(AuthenticatedTestCase):
  """Helper setup for email API tests (modifying operations)."""

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

    # Recreate a client for each test to ensure a clean state
    self.client_obj = Client.objects.create(
      user=self.user, name="Api Test Client", cpf="12345678901"
    )

    # Create an initial email for update/delete tests
    self.email_obj = ClientEmail.objects.create(
      client=self.client_obj, email="test@example.com"
    )

  def tearDown(self):
    self.client_obj.delete()
    super().tearDown()

  def _get_valid_token(self):
    return self.credentials["access"]


class EmailsRoute_Update(BaseEmailTestCase):
  def test_update_email_success_outcome_validation(self):
    """Test if route can update an existing email."""
    token = self._get_valid_token()
    data = {"email": "updated-api-test@example.com"}

    res = self.client.put(
      f"emails/{self.email_obj.id}",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["email"], "updated-api-test@example.com")
    self.assertEqual(res_data["id"], str(self.email_obj.id))

  def test_update_email_unauthenticated_returns_401(self):
    """Test authentication gating."""
    data = {"email": "updated-api-test@example.com"}
    res = self.client.put(f"emails/{self.email_obj.id}", data=data)
    self.assertEqual(res.status_code, 401)

  def test_update_email_invalid_id_returns_404(self):
    """Test if route returns 404 for a non-existent email."""
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())
    data = {"email": "updated-api-test@example.com"}

    res = self.client.put(
      f"emails/{random_id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)


class EmailsRoute_Delete(BaseEmailTestCase):
  def test_delete_email_success_outcome_validation(self):
    """Test if route can delete an existing email."""
    token = self._get_valid_token()

    res = self.client.delete(
      f"emails/{self.email_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data.get("success"), True)

    # Verify it's actually gone from the database
    self.assertFalse(ClientEmail.objects.filter(id=self.email_obj.id).exists())

  def test_delete_email_unauthenticated_returns_401(self):
    """Test authentication gating."""
    res = self.client.delete(f"emails/{self.email_obj.id}")
    self.assertEqual(res.status_code, 401)

  def test_delete_email_invalid_id_returns_404(self):
    """Test if route returns 404 for a non-existent email."""
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.delete(
      f"emails/{random_id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)
