from unittest import TestCase
from unittest.mock import MagicMock, patch
from django.utils import timezone
import uuid

from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.services.task import (
  TaskService,
  ProjectNotFoundError,
  MovGroupNotFoundError,
)
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
    do_at = timezone.now()
    task_mock.do_at = do_at
    MockTask.objects.create.return_value = task_mock

    data = CreateTaskReq(name="New Task", do_at=do_at)
    result = TaskService.create(user, project_id, data)

    self.assertEqual(result.do_at, do_at)
    self.assertEqual(result.name, "New Task")
    MockProject.objects.filter.assert_called_once_with(id=project_id, user=user)
    MockTask.objects.create.assert_called_once()
    task_mock.save.assert_called_once()

  @patch("apps.projects_and_clients.services.task.Project")
  def test_create_task_project_not_found(self, MockProject):
    user = MagicMock()
    project_id = str(uuid.uuid4())
    MockProject.objects.filter.return_value.first.return_value = None

    data = CreateTaskReq(name="Task", do_at=timezone.now())
    with self.assertRaises(ProjectNotFoundError):
      TaskService.create(user, project_id, data)

  @patch("apps.projects_and_clients.services.task.Task")
  @patch("apps.projects_and_clients.services.task.MovimentationService")
  @patch("apps.projects_and_clients.services.task.MovGroup")
  @patch("apps.projects_and_clients.services.task.Project")
  def test_create_task_with_movimentation(
    self, MockProject, MockMovGroup, MockMovService, MockTask
  ):
    user = MagicMock()
    project_id = str(uuid.uuid4())
    project_mock = MagicMock()
    MockProject.objects.filter.return_value.first.return_value = project_mock

    movgroup_mock = MagicMock()
    MockMovGroup.objects.filter.return_value.first.return_value = movgroup_mock

    movimentation_mock = MagicMock()
    MockMovService.create.return_value = movimentation_mock

    task_mock = MagicMock()
    MockTask.objects.create.return_value = task_mock

    mov_data = {"amount": 100.0, "balance": "+"}
    data = CreateTaskReq(
      name="Task with Mov", do_at=timezone.now(), movimentation=mov_data
    )

    result = TaskService.create(user, project_id, data)

    MockMovGroup.objects.filter.assert_called_once_with(
      related_to=project_id, user=user
    )
    MockMovService.create.assert_called_once()
    MockTask.objects.create.assert_called_once()
    # Check if the movimentation object was passed to Task.create
    _, kwargs = MockTask.objects.create.call_args
    self.assertEqual(kwargs["movimentation"], movimentation_mock)
    self.assertEqual(result, task_mock)

  @patch("apps.projects_and_clients.services.task.Task")
  @patch("apps.projects_and_clients.services.task.MovimentationService")
  @patch("apps.projects_and_clients.services.task.MovGroup")
  @patch("apps.projects_and_clients.services.task.Project")
  def test_create_task_doesnot_create_movimentation_if_no_movimentation_data_provided(
    self, MockProject, MockMovGroup, MockMovService, MockTask
  ):
    user = MagicMock()
    project_id = str(uuid.uuid4())
    MockProject.objects.filter.return_value.first.return_value = MagicMock()
    MockMovGroup.objects.filter.return_value.first.return_value = MagicMock()
    MockTask.objects.create.return_value = MagicMock()

    data = CreateTaskReq(name="Task No Mov", do_at=timezone.now(), movimentation=None)
    TaskService.create(user, project_id, data)

    MockMovGroup.objects.filter.assert_not_called()
    MockMovService.create.assert_not_called()

  @patch("apps.projects_and_clients.services.task.MovGroup")
  @patch("apps.projects_and_clients.services.task.Project")
  def test_create_task_movgroup_not_found(self, MockProject, MockMovGroup):
    user = MagicMock()
    project_id = str(uuid.uuid4())
    MockProject.objects.filter.return_value.first.return_value = MagicMock()
    MockMovGroup.objects.filter.return_value.first.return_value = None

    mov_data = {"amount": 100.0, "balance": "+"}
    data = CreateTaskReq(name="Task", do_at=timezone.now(), movimentation=mov_data)

    with self.assertRaises(MovGroupNotFoundError):
      TaskService.create(user, project_id, data)

  @patch("apps.projects_and_clients.services.task.Task")
  @patch("apps.projects_and_clients.services.task.Project")
  def test_create_task_project_belongs_to_user(self, MockProject, MockTask):
    """Filter must include both project_id and user to prevent cross-user access."""
    user = MagicMock()
    project_id = str(uuid.uuid4())
    project_mock = MagicMock()
    MockProject.objects.filter.return_value.first.return_value = project_mock
    MockTask.objects.create.return_value = MagicMock()

    data = CreateTaskReq(name="Task", do_at=timezone.now())
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
    task_mock.do_at = timezone.now()
    mock_get.return_value = task_mock
    new_doat = timezone.now() + timezone.timedelta(days=1)

    data = UpdateTaskReq(name="Updated Name", do_at=new_doat)
    result = TaskService.update(user, "task-id", "project-id", data)

    self.assertEqual(task_mock.do_at, new_doat)
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
    data = UpdateTaskReq(name="Name", do_at=timezone.now())
    TaskService.update(user, task_id, project_id, data)

    mock_get.assert_called_once_with(user, task_id, project_id)

  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_update_task_not_found(self, mock_get):
    user = MagicMock()
    mock_get.side_effect = ResourceNotFoundError("Task not found.")

    data = UpdateTaskReq(name="Name", do_at=timezone.now())
    with self.assertRaises(ResourceNotFoundError):
      TaskService.update(user, "bad-id", "project-id", data)


class TestTaskService_PartialUpdate(TestCase):
  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_partial_update_task_success(self, mock_get):
    user = MagicMock()
    task_mock = MagicMock()
    task_mock.name = "Old Name"
    task_mock.do_at = timezone.now()
    mock_get.return_value = task_mock
    new_doat = timezone.now() + timezone.timedelta(days=1)

    data = PartialUpdateTaskReq(name="Partial Name", do_at=new_doat)
    result = TaskService.partial_update(user, "task-id", "project-id", data)

    self.assertEqual(task_mock.do_at, new_doat)
    self.assertEqual(task_mock.name, "Partial Name")
    task_mock.save.assert_called_once()
    self.assertEqual(result, task_mock)

  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_partial_update_task_not_found(self, mock_get):
    user = MagicMock()
    mock_get.side_effect = ResourceNotFoundError("Task not found.")

    data = PartialUpdateTaskReq(name="Name", do_at=timezone.now())
    with self.assertRaises(ResourceNotFoundError):
      TaskService.partial_update(user, "bad-id", "project-id", data)


class TestTaskService_Delete(TestCase):
  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_delete_task_success(self, mock_get):
    user = MagicMock()
    task_mock = MagicMock()
    task_mock.movimentation = None
    mock_get.return_value = task_mock

    result = TaskService.delete(user, "task-id", "project-id")

    task_mock.delete.assert_called_once()
    self.assertEqual(result, {"success": True})

  @patch("apps.projects_and_clients.services.task.TaskService.get")
  def test_delete_task_with_movimentation_success(self, mock_get):
    user = MagicMock()
    task_mock = MagicMock()
    mov_mock = MagicMock()
    task_mock.movimentation = mov_mock
    mock_get.return_value = task_mock

    TaskService.delete(user, "task-id", "project-id")

    mov_mock.delete.assert_called_once()
    task_mock.delete.assert_called_once()

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
