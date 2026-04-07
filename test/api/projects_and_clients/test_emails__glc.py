import uuid
from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.projects_and_clients.models import Client, ClientEmail


class BaseEmailTestCase(AuthenticatedTestCase):
  """Helper setup for email API tests."""

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

    # Create a client belonging to the authenticated user
    cls.client_obj = Client.objects.create(
      user=cls.user, name="Api Test Client", cpf="12345678901"
    )

    # Create some initial emails for listing tests
    cls.email1 = ClientEmail.objects.create(
      client=cls.client_obj, email="test1@example.com"
    )
    cls.email2 = ClientEmail.objects.create(
      client=cls.client_obj, email="test2@example.com"
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


class EmailsRoute_List(BaseEmailTestCase):
  def test_list_emails_success_outcome_validation(self):
    """Test if list endpoint returns correctly structured PaginatedAPIResponse[ClientEmailSchema] instances."""
    token = self._get_valid_token()

    res = self.client.get(
      f"{self.client_obj.id}/emails", headers={"Authorization": f"Bearer {token}"}
    )
    data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertIsInstance(data, dict)
    self.assertIn("items", data)
    self.assertIsInstance(data["items"], list)
    self.assertEqual(len(data["items"]), 2)
    self.assertEqual(data["total_count"], 2)

    # Verify outcome data structure matches ClientEmailSchema
    emails = {e["email"]: e for e in data["items"]}
    self.assertIn("test1@example.com", emails)
    self.assertIn("test2@example.com", emails)
    self.assertEqual(emails["test1@example.com"]["id"], str(self.email1.id))

  def test_list_emails_unauthenticated_returns_401(self):
    """Test authentication gating."""
    res = self.client.get(f"{self.client_obj.id}/emails")
    self.assertEqual(res.status_code, 401)
    data = res.json()
    self.assertEqual(data.get("success"), False)

  def test_list_emails_invalid_client_returns_404(self):
    """Test if route returns 404 for a non-existent client."""
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.get(
      f"{random_id}/emails", headers={"Authorization": f"Bearer {token}"}
    )
    data = res.json()

    self.assertEqual(res.status_code, 404)
    self.assertEqual(data.get("success"), False)
    self.assertIn("Client", data.get("details", ""))


class EmailsRoute_Create(BaseEmailTestCase):
  def test_create_email_success_outcome_validation(self):
    """Test if route can add a new email successfully."""
    token = self._get_valid_token()
    data = {"email": "new-api-test@example.com"}

    res = self.client.post(
      f"{self.client_obj.id}/emails",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertEqual(res_data["email"], "new-api-test@example.com")
    self.assertIn("id", res_data)

    # Verify it's actually in the database for THIS client
    self.assertTrue(
      ClientEmail.objects.filter(id=res_data["id"], client=self.client_obj).exists()
    )

  def test_create_email_unauthenticated_returns_401(self):
    """Test authentication gating."""
    data = {"email": "new-api-test@example.com"}
    res = self.client.post(f"{self.client_obj.id}/emails", data=data)
    self.assertEqual(res.status_code, 401)

  def test_create_email_invalid_client_returns_404(self):
    """Test if route returns 404 for a non-existent client."""
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())
    data = {"email": "new-api-test@example.com"}

    res = self.client.post(
      f"{random_id}/emails", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)

  def test_create_email_invalid_data_returns_422(self):
    """Test validation error for malformed email."""
    token = self._get_valid_token()
    data = {"email": "not-an-email"}

    res = self.client.post(
      f"{self.client_obj.id}/emails",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 422)
