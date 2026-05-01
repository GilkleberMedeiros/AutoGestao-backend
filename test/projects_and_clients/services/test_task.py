from unittest import TestCase
from unittest.mock import MagicMock, patch
from django.utils import timezone
import uuid

from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.services.task import TaskService
from apps.projects_and_clients.schemas.task import (
  CreateTaskReq,
  UpdateTaskReq,
  PartialUpdateTaskReq,
)


class TestTaskService_Create(TestCase):
  @patch("apps.projects_and_clients.services.task.Task")
  @patch("apps.projects_and_clients.services.task.Project")
  def test_create_task_success(self, MockProject, MockTask):
    user = MagicMock()
    project_id = str(uuid.uuid4())

    project_mock = MagicMock()
    project_mock.id = project_id
    MockProject.objects.filter.return_value.first.return_value = project_mock

    task_mock = MagicMock()
    task_mock.name = "New Task"
    MockTask.objects.create.return_value = task_mock

    data = CreateTaskReq(name="New Task", done_at=None)
    result = TaskService.create(user, project_id, data)

    self.assertEqual(result.name, "New Task")
    MockProject.objects.filter.assert_called_once_with(id=project_id, user=user)
    MockTask.objects.create.assert_called_once()
    task_mock.save.assert_called_once()

  @patch("apps.projects_and_clients.services.task.Project")
  def test_create_task_project_not_found(self, MockProject):
    user = MagicMock()
    project_id = str(uuid.uuid4())
    MockProject.objects.filter.return_value.first.return_value = None

    data = CreateTaskReq(name="Task", done_at=None)
    with self.assertRaises(ResourceNotFoundError):
      TaskService.create(user, project_id, data)

  @patch("apps.projects_and_clients.services.task.Task")
  @patch("apps.projects_and_clients.services.task.Project")
  def test_create_task_sets_done_at_when_not_provided(self, MockProject, MockTask):
    """When done_at is not set (None), the service should default it to timezone.now()."""
    user = MagicMock()
    project_id = str(uuid.uuid4())
    project_mock = MagicMock()
    MockProject.objects.filter.return_value.first.return_value = project_mock

    task_mock = MagicMock()
    MockTask.objects.create.return_value = task_mock

    data = CreateTaskReq(name="Task", done_at=None)
    TaskService.create(user, project_id, data)

    # done_at must have been injected into the create call
    _, kwargs = MockTask.objects.create.call_args
    self.assertIn("done_at", kwargs)
    self.assertIsNotNone(kwargs["done_at"])

  @patch("apps.projects_and_clients.services.task.Task")
  @patch("apps.projects_and_clients.services.task.Project")
  def test_create_task_doesnot_set_done_at_when_provided(self, MockProject, MockTask):
    """When done_at is provided, the service should not override it."""
    user = MagicMock()
    project_id = str(uuid.uuid4())
    project_mock = MagicMock()
    MockProject.objects.filter.return_value.first.return_value = project_mock

    task_mock = MagicMock()
    MockTask.objects.create.return_value = task_mock

    done_at = timezone.now()
    data = CreateTaskReq(name="Task", done_at=done_at)
    TaskService.create(user, project_id, data)

    # done_at must have been injected into the create call
    _, kwargs = MockTask.objects.create.call_args
    self.assertIn("done_at", kwargs)
    self.assertEqual(kwargs["done_at"], done_at)

  def test_create_task_with_movimentation(
    self,
  ):
    # TODO: create a task with movimentation and check if it was created
    pass

  def test_create_task_doesnot_create_movimentation_if_no_movimentation_data_provided(
    self,
  ):
    # TODO: create a task without movimentation data when not provided, and check if it was not created
    pass

  @patch("apps.projects_and_clients.services.task.Task")
  @patch("apps.projects_and_clients.services.task.Project")
  def test_create_task_project_belongs_to_user(self, MockProject, MockTask):
    """Filter must include both project_id and user to prevent cross-user access."""
    user = MagicMock()
    project_id = str(uuid.uuid4())
    project_mock = MagicMock()
    MockProject.objects.filter.return_value.first.return_value = project_mock
    MockTask.objects.create.return_value = MagicMock()

    data = CreateTaskReq(name="Task", done_at=None)
    TaskService.create(user, project_id, data)

    MockProject.objects.filter.assert_called_once_with(id=project_id, user=user)


class TestTaskService_List(TestCase):
  @patch("apps.projects_and_clients.services.task.Task")
  def test_list_tasks_success(self, MockTask):
    user = MagicMock()
    project_id = str(uuid.uuid4())
    mock_qs = MagicMock()
    MockTask.objects.filter.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs

    result = TaskService.list(user, project_id=project_id)

    MockTask.objects.filter.assert_called_once_with(
      project=project_id, project__user=user
    )
    self.assertEqual(result, mock_qs)


class TestTaskService_Get(TestCase):
  @patch("apps.projects_and_clients.services.task.Task")
  def test_get_task_success(self, MockTask):
    user = MagicMock()
    project_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    task_mock = MagicMock()
    task_mock.project.id = project_id
    MockTask.objects.filter.return_value.first.return_value = task_mock

    result = TaskService.get(user, task_id, project_id)

    self.assertEqual(result, task_mock)
    MockTask.objects.filter.assert_called_once_with(id=task_id, project__user=user)

  @patch("apps.projects_and_clients.services.task.Task")
  def test_get_task_not_found(self, MockTask):
    user = MagicMock()
    MockTask.objects.filter.return_value.first.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      TaskService.get(user, str(uuid.uuid4()), str(uuid.uuid4()))

  @patch("apps.projects_and_clients.services.task.Task")
  def test_get_task_wrong_project(self, MockTask):
    """Raise ResourceNotFoundError when the task belongs to a different project."""
    user = MagicMock()
    task_id = str(uuid.uuid4())
    requested_project_id = uuid.uuid4()
    other_project_id = uuid.uuid4()

    task_mock = MagicMock()
    task_mock.project.id = other_project_id
    MockTask.objects.filter.return_value.first.return_value = task_mock

    with self.assertRaises(ResourceNotFoundError):
      TaskService.get(user, task_id, requested_project_id)


class TestTaskService_Update(TestCase):
  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_update_task_success(self, mock_get):
    user = MagicMock()
    task_mock = MagicMock()
    task_mock.name = "Old Name"
    mock_get.return_value = task_mock

    data = UpdateTaskReq(name="Updated Name", done_at=None)
    result = TaskService.update(user, "task-id", "project-id", data)

    self.assertEqual(task_mock.name, "Updated Name")
    task_mock.save.assert_called_once()
    self.assertEqual(result, task_mock)

  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_update_task_calls_get_with_correct_args(self, mock_get):
    user = MagicMock()
    task_mock = MagicMock()
    mock_get.return_value = task_mock

    task_id = "task-id"
    project_id = "proj-id"
    data = UpdateTaskReq(name="Name", done_at=None)
    TaskService.update(user, task_id, project_id, data)

    mock_get.assert_called_once_with(user, task_id, project_id)

  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_update_task_not_found(self, mock_get):
    user = MagicMock()
    mock_get.side_effect = ResourceNotFoundError("Task not found.")

    data = UpdateTaskReq(name="Name", done_at=None)
    with self.assertRaises(ResourceNotFoundError):
      TaskService.update(user, "bad-id", "project-id", data)


class TestTaskService_PartialUpdate(TestCase):
  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_partial_update_task_success(self, mock_get):
    user = MagicMock()
    task_mock = MagicMock()
    task_mock.name = "Old Name"
    mock_get.return_value = task_mock

    data = PartialUpdateTaskReq(name="Partial Name")
    result = TaskService.partial_update(user, "task-id", "project-id", data)

    self.assertEqual(task_mock.name, "Partial Name")
    task_mock.save.assert_called_once()
    self.assertEqual(result, task_mock)

  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_partial_update_only_sets_provided_fields(self, mock_get):
    """Only fields included in the request should be mutated via setattr."""
    user = MagicMock()

    class DummyTask:
      def __init__(self):
        self.name = "Old Name"
        self.done_at = "Old Date"
        self.save = MagicMock()

    task_mock = DummyTask()
    mock_get.return_value = task_mock

    data = PartialUpdateTaskReq(name="Only Name")
    TaskService.partial_update(user, "task-id", "project-id", data)

    # name was provided so it should be updated
    self.assertEqual(task_mock.name, "Only Name")
    # done_at was not provided so it should remain unchanged
    self.assertEqual(task_mock.done_at, "Old Date")

  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_partial_update_task_not_found(self, mock_get):
    user = MagicMock()
    mock_get.side_effect = ResourceNotFoundError("Task not found.")

    data = PartialUpdateTaskReq(name="Name")
    with self.assertRaises(ResourceNotFoundError):
      TaskService.partial_update(user, "bad-id", "project-id", data)


class TestTaskService_Delete(TestCase):
  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_delete_task_success(self, mock_get):
    user = MagicMock()
    task_mock = MagicMock()
    mock_get.return_value = task_mock

    result = TaskService.delete(user, "task-id", "project-id")

    task_mock.delete.assert_called_once()
    self.assertEqual(result, {"success": True})

  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_delete_task_calls_get_with_correct_args(self, mock_get):
    user = MagicMock()
    task_mock = MagicMock()
    mock_get.return_value = task_mock

    task_id = "task-id"
    project_id = "proj-id"
    TaskService.delete(user, task_id, project_id)

    mock_get.assert_called_once_with(user, task_id, project_id)

  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_delete_task_not_found(self, mock_get):
    user = MagicMock()
    mock_get.side_effect = ResourceNotFoundError("Task not found.")

    with self.assertRaises(ResourceNotFoundError):
      TaskService.delete(user, "bad-id", "project-id")
