import uuid

from django.utils import timezone

from test.api.base import APIClient
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

    cls.task_obj = Task.objects.create(
      project=cls.project_obj,
      name="Api Test Task",
      do_at=timezone.now() + timezone.timedelta(days=1),
    )

    cls.mov_group_obj = MovGroup.objects.filter(
      movgroupprojectrelation__project_id=cls.project_obj.id,
      user=cls.user,
    ).first()
    if not cls.mov_group_obj:
      cls.fail("MovGroup wasn't automatically created for created project!")

    cls.movimentation_obj = Movimentation.objects.create(
      mov_group=cls.mov_group_obj,
      amount=150.00,
      balance="+",
      reason="Api Test Task Movimentation",
    )

    cls.task_with_mov_obj = Task.objects.create(
      project=cls.project_obj,
      name="Api Test Task with Movimentation",
      do_at=timezone.now() + timezone.timedelta(days=1),
      movimentation=cls.movimentation_obj,
    )

    cls.URL = f"/api/projects/{cls.project_obj.id}/tasks"

  @classmethod
  def tearDownClass(cls):
    cls.task_with_mov_obj.delete()
    cls.movimentation_obj.delete()
    cls.mov_group_obj.delete()
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
    self.assertEqual(len(data["items"]), 2)

    # Find the default task in the response list
    task_data = next(
      (item for item in data["items"] if item["id"] == str(self.task_obj.id)), None
    )
    self.assertIsNotNone(task_data)
    self.assertIsNotNone(task_data["do_at"])
    self.assertEqual(task_data["name"], "Api Test Task")
    self.assertIsNone(task_data["movimentation"])

  def test_list_tasks_includes_movimentation_if_exists(self):
    token = self._get_valid_token()

    res = self.client.get("", headers={"Authorization": f"Bearer {token}"})
    data = res.json()

    self.assertEqual(res.status_code, 200)
    items = data["items"]

    # Find the task with movimentation in the response list
    created_task_data = next(
      (item for item in items if item["id"] == str(self.task_with_mov_obj.id)), None
    )
    self.assertIsNotNone(created_task_data)

    # Verify it has movimentation info
    self.assertIsNotNone(created_task_data["movimentation"])
    self.assertEqual(
      created_task_data["movimentation"]["id"], str(self.movimentation_obj.id)
    )
    self.assertEqual(float(created_task_data["movimentation"]["amount"]), 150.00)
    self.assertEqual(created_task_data["movimentation"]["balance"], "+")
    self.assertEqual(
      created_task_data["movimentation"]["reason"], "Api Test Task Movimentation"
    )

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
    self.assertIsNotNone(data["do_at"])
    self.assertEqual(data["name"], "Api Test Task")
    self.assertEqual(data["id"], str(self.task_obj.id))
    self.assertIsNone(data["movimentation"])

  def test_get_task_includes_movimentation_if_exists(self):
    token = self._get_valid_token()

    res = self.client.get(
      f"/{self.task_with_mov_obj.id}", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)
    data = res.json()

    # Verify it has movimentation info
    self.assertIsNotNone(data["movimentation"])
    self.assertEqual(data["movimentation"]["id"], str(self.movimentation_obj.id))
    self.assertEqual(float(data["movimentation"]["amount"]), 150.00)
    self.assertEqual(data["movimentation"]["balance"], "+")
    self.assertEqual(data["movimentation"]["reason"], "Api Test Task Movimentation")

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
    do_at = (timezone.now() + timezone.timedelta(days=2)).isoformat()
    data = {
      "name": "New Task",
      "do_at": do_at,
    }

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertIsNotNone(res_data["do_at"])
    self.assertEqual(res_data["name"], "New Task")
    self.assertIn("id", res_data)

    # Verify creation in DB
    self.assertTrue(Task.objects.filter(id=res_data["id"]).exists())

  def test_create_task_unauthenticated_returns_401(self):
    data = {
      "name": "New Task",
      "do_at": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
    }
    res = self.client.post("", data=data)
    self.assertEqual(res.status_code, 401)

  def test_create_task_user_invalid_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()

    data = {
      "name": "New Task",
      "do_at": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
    }
    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 403)

  def test_create_task_project_not_found_returns_404(self):
    token = self._get_valid_token()
    data = {
      "name": "New Task",
      "do_at": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
    }
    # Create a new client pointing to an invalid project
    client = APIClient(path_prefix=f"/api/projects/{uuid.uuid4()}/tasks")
    res = client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 404)

  def test_create_task_with_movimentation_success(self):
    token = self._get_valid_token()
    # Ensure MovGroup exists for this project (in case it was deleted by another test)
    mov_group, _ = MovGroup.objects.get_or_create(
      user=self.user,
      defaults={
        "name": f"Finance Group for {self.project_obj.id}",
      },
    )
    from apps.projects_and_clients.models import MovGroupProjectRelation
    MovGroupProjectRelation.objects.get_or_create(
      mov_group=mov_group,
      project=self.project_obj,
    )

    data = {
      "name": "Task with Movimentation",
      "do_at": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
      "movimentation": {
        "amount": 150.75,
        "balance": "+",
      },
    }

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertEqual(res_data["name"], "Task with Movimentation")

    # Verify Task and Movimentation in DB
    task = Task.objects.get(id=res_data["id"])
    self.assertIsNotNone(task.movimentation)
    self.assertEqual(float(task.movimentation.amount), 150.75)
    self.assertEqual(task.movimentation.balance, "+")

  def test_create_task_movgroup_not_found_returns_404(self):
    token = self._get_valid_token()
    # Delete the automatically created MovGroup for this project
    MovGroup.objects.filter(movgroupprojectrelation__project_id=self.project_obj.id).delete()

    data = {
      "name": "Task with Movimentation",
      "do_at": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
      "movimentation": {
        "amount": 150.75,
        "balance": "+",
      },
    }

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 404)

  def test_create_task_exclude_fields_that_arent_in_schema(self):
    token = self._get_valid_token()
    data = {
      "name": "New Task",
      "do_at": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
      "non_existent_field": "non_existent_value",
    }

    res = self.client.post("", data=data, headers={"Authorization": f"Bearer {token}"})
    res_data = res.json()

    self.assertEqual(res.status_code, 201)
    self.assertEqual(res_data["name"], "New Task")
    self.assertIn("id", res_data)
    self.assertNotIn("non_existent_field", res_data)
