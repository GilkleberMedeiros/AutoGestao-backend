import uuid
from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.projects_and_clients.models import Client, Project, Task


class BaseTaskRouteTest(AuthenticatedTestCase):
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
  URL = "/api/projects/"

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

    cls.client_obj = Client.objects.create(
      user=cls.user, name="Api Test Client", cpf="12345678901"
    )
    cls.open_project = Project.objects.create(
      user=cls.user,
      client=cls.client_obj,
      name="Open Project",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      status="OPEN",
    )

  @classmethod
  def tearDownClass(cls):
    cls.open_project.delete()
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


class TaskRoute_Create(BaseTaskRouteTest):
  def test_create_task_success(self):
    token = self._get_valid_token()
    data = {"name": "New Task", "description": "Some desc"}
    res = self.client.post(
      f"{self.open_project.id}/tasks",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 201)
    self.assertEqual(res.json()["name"], "New Task")

  def test_create_task_with_done_at(self):
    token = self._get_valid_token()
    data = {"name": "Done Task", "done_at": "2026-04-08T14:00:00Z"}
    res = self.client.post(
      f"{self.open_project.id}/tasks",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 201)
    self.assertIsNotNone(res.json()["done_at"])

  def test_create_task_with_nested_finance_success(self):
    token = self._get_valid_token()
    data = {
      "name": "API Nested Task",
      "finance_entry": {
        "amount": "250.00",
        "balance": "POSITIVE",
        "reason": "From API"
      }
    }
    res = self.client.post(
      f"{self.open_project.id}/tasks",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 201)
    self.assertIsNotNone(res.json()["finance_id"])

  def test_create_task_unauthenticated(self):
    data = {"name": "New Task"}
    res = self.client.post(f"{self.open_project.id}/tasks", data=data)
    self.assertEqual(res.status_code, 401)


class TaskRoute_List(BaseTaskRouteTest):
  def test_list_tasks_success(self):
    Task.objects.create(project=self.open_project, name="T1")
    token = self._get_valid_token()
    res = self.client.get(
      f"{self.open_project.id}/tasks",
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)
    self.assertIn("items", res.json())


class TaskRoute_Get(BaseTaskRouteTest):
  def test_get_task_success(self):
    task = Task.objects.create(project=self.open_project, name="T1")
    token = self._get_valid_token()
    res = self.client.get(
      f"{self.open_project.id}/tasks/{task.id}",
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["name"], "T1")

  def test_get_task_not_found(self):
    token = self._get_valid_token()
    res = self.client.get(
      f"{self.open_project.id}/tasks/{uuid.uuid4()}",
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 404)


class TaskRoute_Update(BaseTaskRouteTest):
  def test_update_task_success(self):
    task = Task.objects.create(project=self.open_project, name="Before")
    token = self._get_valid_token()
    data = {"name": "After", "description": "Updated"}
    res = self.client.put(
      f"{self.open_project.id}/tasks/{task.id}",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["name"], "After")

  def test_update_task_manual_done_at(self):
    task = Task.objects.create(project=self.open_project, name="Before")
    token = self._get_valid_token()
    data = {"name": "After", "done_at": "2026-04-08T15:00:00Z"}
    res = self.client.put(
      f"{self.open_project.id}/tasks/{task.id}",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)
    self.assertIsNotNone(res.json()["done_at"])


class TaskRoute_PartialUpdate(BaseTaskRouteTest):
  def test_partial_update_task_success(self):
    task = Task.objects.create(project=self.open_project, name="Before")
    token = self._get_valid_token()
    data = {"name": "After"}
    res = self.client.patch(
      f"{self.open_project.id}/tasks/{task.id}",
      data=data,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["name"], "After")


class TaskRoute_Delete(BaseTaskRouteTest):
  def test_delete_task_success(self):
    task = Task.objects.create(project=self.open_project, name="Delete Me")
    token = self._get_valid_token()
    res = self.client.delete(
      f"{self.open_project.id}/tasks/{task.id}",
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)

  def test_delete_task_not_found(self):
    token = self._get_valid_token()
    res = self.client.delete(
      f"{self.open_project.id}/tasks/{uuid.uuid4()}",
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 404)
