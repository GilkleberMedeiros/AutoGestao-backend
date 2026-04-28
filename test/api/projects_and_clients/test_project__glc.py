import uuid
from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.projects_and_clients.models import Client, Project


class BaseProjectTestCase(AuthenticatedTestCase):
  """Helper setup for project API tests."""

  user_create_data = {
    "name": "testuser",
    "email": "testapi@example.com",
    "password": "testpassword",
    "phone": "5584000000000",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testapi@example.com", "password": "testpassword"}
  URL = "/api/projects/"

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

    cls.client_obj = Client.objects.create(
      user=cls.user, name="Api Test Client", cpf="12345678901"
    )

    cls.project_obj = Project.objects.create(
      user=cls.user,
      client=cls.client_obj,
      name="Api Test Project",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      status="OPEN",
    )

  @classmethod
  def tearDownClass(cls):
    cls.project_obj.delete()
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


class ProjectsRoute_List(BaseProjectTestCase):
  def test_list_projects_success_outcome_validation(self):
    token = self._get_valid_token()

    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertIsInstance(data, dict)
    self.assertIn("items", data)
    self.assertIsInstance(data["items"], list)
    self.assertEqual(len(data["items"]), 1)

    project_data = data["items"][0]
    self.assertEqual(project_data["name"], "Api Test Project")
    self.assertEqual(project_data["id"], str(self.project_obj.id))

  def test_list_projects_unauthenticated_returns_401(self):
    res = self.client.get("")
    self.assertEqual(res.status_code, 401)


class ProjectsRoute_Get(BaseProjectTestCase):
  def test_get_project_success_outcome_validation(self):
    token = self._get_valid_token()
    res = self.client.get(
      f"{self.project_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 200)
    data = res.json()
    self.assertEqual(data["name"], "Api Test Project")
    self.assertEqual(data["id"], str(self.project_obj.id))

  def test_get_project_unauthenticated_returns_401(self):
    res = self.client.get(f"{self.project_obj.id}")
    self.assertEqual(res.status_code, 401)

  def test_get_project_invalid_id_returns_404(self):
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.get(f"{random_id}", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 404)


class ProjectsRoute_Create(BaseProjectTestCase):
  def test_create_project_success_outcome_validation(self):
    token = self._get_valid_token()
    data = {
      "name": "New Project",
      "description": "test",
      "estimated_deadline": "2026-12-31",
      "estimated_cost": 200.00,
      "colortag": "#000000",
      "client_id": str(self.client_obj.id),
    }

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertEqual(res_data["name"], "New Project")
    self.assertIn("id", res_data)

  def test_create_project_unauthenticated_returns_401(self):
    data = {
      "name": "New Project",
      "client_id": str(self.client_obj.id),
      "estimated_deadline": "2026-12-31",
      "estimated_cost": 200.00,
    }
    res = self.client.post("", data=data)
    self.assertEqual(res.status_code, 401)

  def test_create_project_client_not_found_returns_404(self):
    token = self._get_valid_token()
    data = {
      "name": "New Project",
      "client_id": str(uuid.uuid4()),
      "estimated_deadline": "2026-12-31",
      "estimated_cost": 200.00,
    }
    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 404)
