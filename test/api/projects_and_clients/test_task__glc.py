import uuid
from test.api.base import APIClient
from test.api.conftest import AuthenticatedTestCase
from apps.users.models import User
from apps.projects_and_clients.models import Client, Project, Task


class BaseTaskTestCase(AuthenticatedTestCase):
  """Helper setup for task API tests."""

  user_create_data = {
    "name": "testuser",
    "email": "testapi@example.com",
    "password": "testpassword",
    "phone": "5584000000000",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testapi@example.com", "password": "testpassword"}

  @classmethod
  def setUpClass(cls):
    super().setUpClass()

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

    cls.task_obj = Task.objects.create(
      project=cls.project_obj,
      name="Api Test Task",
    )

    cls.URL = f"/api/projects/{cls.project_obj.id}/tasks"

  @classmethod
  def tearDownClass(cls):
    cls.task_obj.delete()
    cls.project_obj.delete()
    cls.client_obj.delete()
    super().tearDownClass()

  def setUp(self):
    super().setUp()

  def tearDown(self):
    super().tearDown()

  def _get_valid_token(self):
    return self.credentials["access"]


class TasksRoute_List(BaseTaskTestCase):
  def test_list_tasks_success_outcome_validation(self):
    token = self._get_valid_token()

    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertIsInstance(data, dict)
    self.assertIn("items", data)
    self.assertIsInstance(data["items"], list)
    self.assertEqual(len(data["items"]), 1)

    task_data = data["items"][0]
    self.assertEqual(task_data["name"], "Api Test Task")
    self.assertEqual(task_data["id"], str(self.task_obj.id))

  def test_list_tasks_unauthenticated_returns_401(self):
    res = self.client.get("")
    self.assertEqual(res.status_code, 401)

  def test_list_tasks_user_invalid_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()

    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 403)


class TasksRoute_Get(BaseTaskTestCase):
  def test_get_task_success_outcome_validation(self):
    token = self._get_valid_token()
    res = self.client.get(
      f"/{self.task_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 200)
    data = res.json()
    self.assertEqual(data["name"], "Api Test Task")
    self.assertEqual(data["id"], str(self.task_obj.id))

  def test_get_task_unauthenticated_returns_401(self):
    res = self.client.get(f"/{self.task_obj.id}")
    self.assertEqual(res.status_code, 401)

  def test_get_task_user_invalid_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()

    res = self.client.get(
      f"/{self.task_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)

  def test_get_task_invalid_id_returns_404(self):
    token = self._get_valid_token()
    random_id = str(uuid.uuid4())

    res = self.client.get(f"/{random_id}", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 404)


class TasksRoute_Create(BaseTaskTestCase):
  def test_create_task_success_outcome_validation(self):
    token = self._get_valid_token()
    data = {
      "name": "New Task",
    }

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertEqual(res_data["name"], "New Task")
    self.assertIn("id", res_data)

    # Verify creation in DB
    self.assertTrue(Task.objects.filter(id=res_data["id"]).exists())

  def test_create_task_unauthenticated_returns_401(self):
    data = {
      "name": "New Task",
    }
    res = self.client.post("", data=data)
    self.assertEqual(res.status_code, 401)

  def test_create_task_user_invalid_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()

    data = {
      "name": "New Task",
    }
    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 403)

  def test_create_task_project_not_found_returns_404(self):
    token = self._get_valid_token()
    data = {
      "name": "New Task",
    }
    # Create a new client pointing to an invalid project
    client = APIClient(path_prefix=f"/api/projects/{uuid.uuid4()}/tasks")
    res = client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 404)

  def test_create_task_exclude_fields_that_arent_in_schema(self):
    token = self._get_valid_token()
    data = {
      "name": "New Task",
      "non_existent_field": "non_existent_value",
    }

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertEqual(res_data["name"], "New Task")
    self.assertIn("id", res_data)
    self.assertNotIn("non_existent_field", res_data)
