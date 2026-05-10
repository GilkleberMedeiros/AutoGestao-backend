import uuid
import datetime
from django.utils import timezone

from test.api.conftest import AuthenticatedTestCase
from apps.users.models import User
from apps.projects_and_clients.models import Client, Project, Task
from apps.finances.models import MovGroup, Movimentation


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
      labor_fee=50.00,
      status="OPEN",
    )

    cls.task_obj = None

    cls.URL = f"/api/projects/{cls.project_obj.id}/tasks"

  @classmethod
  def tearDownClass(cls):
    cls.project_obj.delete()
    cls.client_obj.delete()
    super().tearDownClass()

  def setUp(self):
    super().setUp()

    # Make sure task is refreshed for each test
    if self.task_obj is None:
      self.task_obj = Task.objects.create(
        project=self.project_obj,
        name="Api Test Task",
      )

  def tearDown(self):
    # Only delete if it still exists (some tests might delete it)
    if Task.objects.filter(id=self.task_obj.id).exists():
      self.task_obj.delete()
    super().tearDown()

  def _get_valid_token(self):
    return self.credentials["access"]


class TasksRoute_Update(BaseTaskTestCase):
  def test_update_task_success_outcome_validation(self):
    token = self._get_valid_token()
    data = {
      "name": "Updated Task Name",
      "done_at": "2026-12-31T23:59:59Z",
    }

    res = self.client.put(
      f"/{self.task_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["name"], "Updated Task Name")

    # Check DB
    self.task_obj.refresh_from_db()
    self.assertEqual(self.task_obj.name, "Updated Task Name")
    self.assertIsNotNone(self.task_obj.done_at)

  def test_update_task_unauthenticated_returns_401(self):
    data = {"name": "Updated Task Name"}
    res = self.client.put(f"/{self.task_obj.id}", data=data)
    self.assertEqual(res.status_code, 401)

  def test_update_task_user_invalid_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()
    data = {"name": "Updated Task Name"}
    res = self.client.put(
      f"/{self.task_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)

  def test_update_task_invalid_id_returns_404(self):
    token = self._get_valid_token()
    data = {"name": "Updated Task Name"}
    res = self.client.put(
      f"/{uuid.uuid4()}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)

  def test_update_task_exclude_fields_that_arent_in_schema(self):
    token = self._get_valid_token()
    data = {
      "name": "Updated Task Name",
      "invalid_field": "invalid_value",
    }
    res = self.client.put(
      f"/{self.task_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["name"], "Updated Task Name")
    self.assertIsNone(res.json().get("invalid_field"))


class TasksRoute_PartialUpdate(BaseTaskTestCase):
  def test_partial_update_task_success_outcome_validation(self):
    token = self._get_valid_token()
    data = {
      "name": "Partially Updated Task",
    }

    res = self.client.patch(
      f"/{self.task_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["name"], "Partially Updated Task")

    # Check DB
    self.task_obj.refresh_from_db()
    self.assertEqual(self.task_obj.name, "Partially Updated Task")

  def test_partial_update_task_done_at_success_outcome_validation(self):
    token = self._get_valid_token()
    data = {
      "done_at": "2026-12-31T23:59:59Z",
    }
    res = self.client.patch(
      f"/{self.task_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res_data["done_at"], "2026-12-31T23:59:59Z")

    self.task_obj.refresh_from_db()
    self.assertEqual(
      self.task_obj.done_at,
      datetime.datetime(
        2026, 12, 31, 23, 59, 59, tzinfo=timezone.get_current_timezone()
      ),
    )

  def test_partial_update_task_unauthenticated_returns_401(self):
    data = {"name": "Partially Updated Task"}
    res = self.client.patch(f"/{self.task_obj.id}", data=data)
    self.assertEqual(res.status_code, 401)

  def test_partual_upadate_task_user_invalid_email_returns_403(self):
    token = self._get_valid_token()
    data = {"name": "Partially Updated Task"}
    self.user.is_email_valid = False
    self.user.save()
    res = self.client.patch(
      f"/{self.task_obj.id}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)

  def test_partial_update_task_invalid_id_returns_404(self):
    token = self._get_valid_token()
    data = {"name": "Partially Updated Task"}
    res = self.client.patch(
      f"/{uuid.uuid4()}", data=data, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)


class TasksRoute_Delete(BaseTaskTestCase):
  def test_delete_task_success_outcome_validation(self):
    token = self._get_valid_token()

    res = self.client.delete(
      f"/{self.task_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["success"], True)

    # Verify deletion from DB
    self.assertFalse(Task.objects.filter(id=self.task_obj.id).exists())

  def test_delete_task_unauthenticated_returns_401(self):
    res = self.client.delete(f"/{self.task_obj.id}")
    self.assertEqual(res.status_code, 401)

  def test_delete_task_user_invalid_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()
    res = self.client.delete(
      f"/{self.task_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)

  def test_delete_task_with_movimentation_success(self):
    token = self._get_valid_token()
    # Create a task with movimentation
    mov_group, _ = MovGroup.objects.get_or_create(
      related_to=self.project_obj.id,
      user=self.user,
      defaults={
        "name": f"Finance Group for {self.project_obj.id}",
        "relation": "PROJECT",
      },
    )
    movimentation = Movimentation.objects.create(
      mov_group=mov_group, amount=50.0, balance="-", reason="test delete"
    )
    task_with_mov = Task.objects.create(
      project=self.project_obj, name="Task to Delete", movimentation=movimentation
    )

    res = self.client.delete(
      f"/{task_with_mov.id}", headers={"Authorization": f"Bearer {token}"}
    )

    self.assertEqual(res.status_code, 200)
    # Verify both Task and Movimentation are deleted
    self.assertFalse(Task.objects.filter(id=task_with_mov.id).exists())
    self.assertFalse(Movimentation.objects.filter(id=movimentation.id).exists())

  def test_delete_task_invalid_id_returns_404(self):
    token = self._get_valid_token()
    res = self.client.delete(
      f"/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)
