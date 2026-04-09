from django.test import TestCase
from django.utils import timezone
import uuid

from apps.users.models import User
from apps.projects_and_clients.models import Client, Project, Task
from apps.projects_and_clients.services.task import TaskService
from apps.projects_and_clients.services.project import ProjectClosedForEditError
from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.schemas.task import (
  CreateTaskReq,
  UpdateTaskReq,
  PartialUpdateTaskReq,
)


class BaseTaskTest(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="taskuser",
      email="taskuser@test.com",
      password="testpass",
      phone="5584000000000",
    )
    cls.other_user = User.objects.create_user(
      name="otheruser",
      email="otheruser@test.com",
      password="testpass",
      phone="5584000000001",
    )
    cls.project_client = Client.objects.create(
      user=cls.user, name="Client A", cpf="12345678901"
    )
    cls.open_project = Project.objects.create(
      user=cls.user,
      client=cls.project_client,
      name="Open Project",
      estimated_deadline="2026-12-31",
      estimated_cost="1000.00",
      status="OPEN",
    )
    cls.closed_project = Project.objects.create(
      user=cls.user,
      client=cls.project_client,
      name="Closed Project",
      estimated_deadline="2026-12-31",
      estimated_cost="1000.00",
      status="CONCLUDED",
      closed_at=timezone.now(),
    )

  @classmethod
  def tearDownClass(cls):
    cls.closed_project.delete()
    cls.open_project.delete()
    cls.project_client.delete()
    cls.other_user.delete()
    cls.user.delete()
    super().tearDownClass()


class TestCreateTask(BaseTaskTest):
  def test_create_task_success(self):
    data = CreateTaskReq(name="Task A", description="Do something")
    task = TaskService.create(self.user, str(self.open_project.id), data)
    self.assertEqual(task.name, "Task A")
    self.assertEqual(task.description, "Do something")
    self.assertEqual(task.project_id, self.open_project.id)
    self.assertIsNone(task.done_at)

  def test_create_task_without_description(self):
    data = CreateTaskReq(name="Task B")
    task = TaskService.create(self.user, str(self.open_project.id), data)
    self.assertEqual(task.name, "Task B")
    self.assertIsNone(task.description)

  def test_create_task_with_done_at(self):
    now = timezone.now()
    data = CreateTaskReq(name="Done Task", done_at=now)
    task = TaskService.create(self.user, str(self.open_project.id), data)
    self.assertEqual(task.name, "Done Task")
    self.assertEqual(task.done_at, now)

  def test_create_task_with_nested_finance(self):
    from apps.projects_and_clients.schemas.task import TaskFinanceInputSchema
    from decimal import Decimal
    
    finance_data = TaskFinanceInputSchema(
      amount=Decimal("150.00"),
      balance="POSITIVE",
      reason="Test Nested"
    )
    data = CreateTaskReq(name="Nested Task", finance_entry=finance_data)
    task = TaskService.create(self.user, str(self.open_project.id), data)
    
    self.assertEqual(task.name, "Nested Task")
    self.assertIsNotNone(task.finance)
    self.assertEqual(task.finance.amount, Decimal("150.00"))
    self.assertEqual(task.finance.reason, "Test Nested")

  def test_create_task_closed_project_fails(self):
    data = CreateTaskReq(name="Task C")
    with self.assertRaises(ProjectClosedForEditError):
      TaskService.create(self.user, str(self.closed_project.id), data)

  def test_create_task_other_user_project_fails(self):
    data = CreateTaskReq(name="Task D")
    with self.assertRaises(ResourceNotFoundError):
      TaskService.create(self.other_user, str(self.open_project.id), data)


class TestGetTask(BaseTaskTest):
  def test_get_task_success(self):
    task = Task.objects.create(
      project=self.open_project, name="Get Me"
    )
    result = TaskService.get(self.user, str(self.open_project.id), str(task.id))
    self.assertEqual(result.id, task.id)

  def test_get_task_not_found(self):
    with self.assertRaises(ResourceNotFoundError):
      TaskService.get(self.user, str(self.open_project.id), str(uuid.uuid4()))

  def test_get_task_wrong_project(self):
    task = Task.objects.create(
      project=self.open_project, name="Wrong Proj"
    )
    with self.assertRaises(ResourceNotFoundError):
      TaskService.get(self.user, str(self.closed_project.id), str(task.id))


class TestListTasks(BaseTaskTest):
  def test_list_tasks(self):
    Task.objects.create(project=self.open_project, name="T1")
    Task.objects.create(project=self.open_project, name="T2")
    tasks = TaskService.list(self.user, str(self.open_project.id))
    self.assertGreaterEqual(tasks.count(), 2)

  def test_list_tasks_other_user(self):
    with self.assertRaises(ResourceNotFoundError):
      TaskService.list(self.other_user, str(self.open_project.id))


class TestUpdateTask(BaseTaskTest):
  def test_update_task_success(self):
    task = Task.objects.create(
      project=self.open_project, name="Before", description="Old"
    )
    data = UpdateTaskReq(name="After", description="New")
    updated = TaskService.update(self.user, str(self.open_project.id), str(task.id), data)
    self.assertEqual(updated.name, "After")
    self.assertEqual(updated.description, "New")

  def test_update_task_manual_done_at(self):
    task = Task.objects.create(
      project=self.open_project, name="Before"
    )
    now = timezone.now()
    data = UpdateTaskReq(name="After", done_at=now)
    updated = TaskService.update(self.user, str(self.open_project.id), str(task.id), data)
    self.assertEqual(updated.done_at, now)

  def test_update_task_closed_project_fails(self):
    task = Task.objects.create(
      project=self.closed_project, name="Locked"
    )
    data = UpdateTaskReq(name="Try Edit")
    with self.assertRaises(ProjectClosedForEditError):
      TaskService.update(self.user, str(self.closed_project.id), str(task.id), data)


class TestPartialUpdateTask(BaseTaskTest):
  def test_partial_update_task_success(self):
    task = Task.objects.create(
      project=self.open_project, name="Before", description="Keep"
    )
    data = PartialUpdateTaskReq(name="After")
    updated = TaskService.partial_update(
      self.user, str(self.open_project.id), str(task.id), data
    )
    self.assertEqual(updated.name, "After")
    self.assertEqual(updated.description, "Keep")

class TestDeleteTask(BaseTaskTest):
  def test_delete_task_success(self):
    task = Task.objects.create(
      project=self.open_project, name="Bye"
    )
    TaskService.delete(self.user, str(self.open_project.id), str(task.id))
    with self.assertRaises(ResourceNotFoundError):
      TaskService.get(self.user, str(self.open_project.id), str(task.id))

  def test_delete_task_closed_project_fails(self):
    task = Task.objects.create(
      project=self.closed_project, name="Locked"
    )
    with self.assertRaises(ProjectClosedForEditError):
      TaskService.delete(self.user, str(self.closed_project.id), str(task.id))
