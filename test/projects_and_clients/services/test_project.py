from unittest import TestCase
from unittest.mock import MagicMock, patch
from django.utils import timezone
from datetime import timedelta
import uuid

from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.services.project import (
  ProjectService,
  ProjectClosedForEditError,
  InvalidCloseStatusError,
  ProjectAlreadyOpenError,
  ProjectNeverClosedError,
  ReopenPeriodExpiredError,
)
from apps.projects_and_clients.schemas.project import (
  CreateProjectReq,
  UpdateProjectReq,
  PartialUpdateProjectReq,
  ProjectFilterSchema,
  ProjectCloseSchema,
)


class TestProjectService_Create(TestCase):
  @patch("apps.projects_and_clients.services.project.Client")
  @patch("apps.projects_and_clients.services.project.Project")
  def test_create_project_success(self, MockProject, MockClient):
    user = MagicMock()
    user.id = 1
    client = MagicMock()
    client.id = uuid.uuid4()
    MockClient.objects.filter.return_value.first.return_value = client

    project_mock = MagicMock()
    project_mock.name = "New Project"
    project_mock.user_id = user.id
    project_mock.status = "OPEN"
    MockProject.objects.create.return_value = project_mock

    data = CreateProjectReq(
      name="New Project",
      description="Desc",
      estimated_deadline="2026-12-31",
      estimated_cost="1000.00",
      colortag="#ff0000",
      client_id=str(client.id),
    )
    project = ProjectService.create(user, data)
    self.assertEqual(project.name, "New Project")
    self.assertEqual(project.user_id, user.id)
    self.assertEqual(project.status, "OPEN")
    MockClient.objects.filter.assert_called_once()
    MockProject.objects.create.assert_called_once()

  @patch("apps.projects_and_clients.services.project.Client")
  def test_create_project_client_not_found(self, MockClient):
    user = MagicMock()
    MockClient.objects.filter.return_value.first.return_value = None
    data = CreateProjectReq(
      name="New Project",
      description="Desc",
      estimated_deadline="2026-12-31",
      estimated_cost="1000.00",
      colortag="#ff0000",
      client_id=str(uuid.uuid4()),
    )
    with self.assertRaises(ResourceNotFoundError):
      ProjectService.create(user, data)

  @patch("apps.projects_and_clients.services.project.Client")
  def test_create_project_other_user_client(self, MockClient):
    _user = MagicMock()
    other_user = MagicMock()
    # Client exists but filtered by user returns None (simulating other user's client)
    MockClient.objects.filter.return_value.first.return_value = None

    data = CreateProjectReq(
      name="New Project",
      description="Desc",
      estimated_deadline="2026-12-31",
      estimated_cost="1000.00",
      colortag="#ff0000",
      client_id=str(uuid.uuid4()),
    )
    with self.assertRaises(ResourceNotFoundError):
      ProjectService.create(other_user, data)

  @patch("apps.projects_and_clients.services.project.Client")
  @patch("apps.projects_and_clients.services.project.Project")
  def test_create_project_fills_only_correct_fields(self, MockProject, MockClient):
    """
    Test if the create method will fills only the fields he should fill, even
    when other fields are specified.
    """
    user = MagicMock()
    client = MagicMock()
    MockClient.objects.filter.return_value.first.return_value = client

    project_mock = MagicMock()
    project_mock.profitability = None
    project_mock.hour_profitability = None
    MockProject.objects.create.return_value = project_mock

    data = CreateProjectReq(
      name="New Project",
      description="Desc",
      estimated_deadline="2026-12-31",
      estimated_cost="1000.00",
      colortag="#ff0000",
      profitability="1000.00",  # Create project should not fill profitability and hour_profitability
      hour_profitability="1000.00",
      client_id=str(uuid.uuid4()),
    )
    project = ProjectService.create(user, data)
    self.assertIsNone(project.profitability)
    self.assertIsNone(project.hour_profitability)


class TestProjectService_Get(TestCase):
  @patch("apps.projects_and_clients.services.project.Project")
  def test_get_project_success(self, MockProject):
    user = MagicMock()
    project_mock = MagicMock()
    project_mock.id = uuid.uuid4()
    MockProject.objects.filter.return_value.first.return_value = project_mock

    result = ProjectService.get(user, str(project_mock.id))
    self.assertEqual(result.id, project_mock.id)
    MockProject.objects.filter.assert_called_once()

  @patch("apps.projects_and_clients.services.project.Project")
  def test_get_project_not_found(self, MockProject):
    user = MagicMock()
    MockProject.objects.filter.return_value.first.return_value = None
    with self.assertRaises(ResourceNotFoundError):
      ProjectService.get(user, str(uuid.uuid4()))


class TestProjectService_List(TestCase):
  @patch("apps.projects_and_clients.services.project.Project")
  def test_list_projects(self, MockProject):
    user = MagicMock()
    mock_qs = MagicMock()
    MockProject.objects.filter.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs

    # Test no filter
    filters = ProjectFilterSchema()
    result = ProjectService.list(user, filters)
    self.assertEqual(result, mock_qs)
    MockProject.objects.filter.assert_called_with(user=user)

    # Test status filter
    filters_status = ProjectFilterSchema(status="CONCLUDED")
    ProjectService.list(user, filters_status)
    mock_qs.filter.assert_any_call(status="CONCLUDED")

    # Test colortag filter
    filters_color = ProjectFilterSchema(colortag="#000")
    ProjectService.list(user, filters_color)
    mock_qs.filter.assert_any_call(colortag="#000")


class TestProjectService_Update(TestCase):
  @patch("apps.projects_and_clients.services.project.ProjectService.get")
  def test_update_open_project(self, mock_get):
    user = MagicMock()
    project_mock = MagicMock()
    project_mock.status = "OPEN"
    mock_get.return_value = project_mock

    data = UpdateProjectReq(
      name="After Update",
      description="",
      estimated_deadline="2026-12-31",
      estimated_cost=200,
      actual_deadline=None,
      actual_cost=None,
      profitability=None,
      hour_profitability=None,
      spent_time=None,
      colortag="#111",
    )
    updated = ProjectService.update(user, "proj-id", data)
    self.assertEqual(updated.name, "After Update")
    project_mock.save.assert_called_once()

  @patch("apps.projects_and_clients.services.project.ProjectService.get")
  def test_update_closed_project_fails(self, mock_get):
    user = MagicMock()
    project_mock = MagicMock()
    project_mock.status = "CONCLUDED"
    mock_get.return_value = project_mock

    data = UpdateProjectReq(
      name="Try Edit",
      description="",
      estimated_deadline="2026-12-31",
      estimated_cost=200,
      actual_deadline=None,
      actual_cost=None,
      profitability=None,
      hour_profitability=None,
      spent_time=None,
      colortag="#111",
    )
    with self.assertRaises(ProjectClosedForEditError):
      ProjectService.update(user, "proj-id", data)


class TestProjectService_PartialUpdate(TestCase):
  @patch("apps.projects_and_clients.services.project.ProjectService.get")
  def test_partial_update_open_project(self, mock_get):
    user = MagicMock()
    project_mock = MagicMock()
    project_mock.status = "OPEN"
    mock_get.return_value = project_mock

    data = PartialUpdateProjectReq(name="After Update")
    updated = ProjectService.partial_update(user, "proj-id", data)
    self.assertEqual(updated.name, "After Update")
    project_mock.save.assert_called_once()

  @patch("apps.projects_and_clients.services.project.ProjectService.get")
  def test_partial_update_closed_project_fails(self, mock_get):
    user = MagicMock()
    project_mock = MagicMock()
    project_mock.status = "CONCLUDED"
    mock_get.return_value = project_mock

    data = PartialUpdateProjectReq(name="Try Edit")
    with self.assertRaises(ProjectClosedForEditError):
      ProjectService.partial_update(user, "proj-id", data)


class TestProjectService_Close(TestCase):
  @patch("apps.projects_and_clients.services.project.ProjectService.get")
  def test_close_project(self, mock_get):
    user = MagicMock()
    project_mock = MagicMock()
    mock_get.return_value = project_mock

    data = ProjectCloseSchema(
      actual_deadline="2026-12-31",
      actual_cost="100.00",
      spent_time=timedelta(hours=100),
      status="CONCLUDED",
    )
    closed = ProjectService.close(user, "proj-id", data)
    self.assertEqual(closed.status, "CONCLUDED")
    self.assertIsNotNone(closed.closed_at)
    # TODO: Add verifications for profitability and hour_profitability
    project_mock.save.assert_called_once()

  @patch("apps.projects_and_clients.services.project.ProjectService.get")
  def test_close_project_invalid_status(self, mock_get):
    user = MagicMock()
    project_mock = MagicMock()
    mock_get.return_value = project_mock

    data = ProjectCloseSchema(status="NOT_A_STATUS")
    with self.assertRaises(InvalidCloseStatusError):
      ProjectService.close(user, "proj-id", data)


class TestProjectService_Reopen(TestCase):
  @patch("apps.projects_and_clients.services.project.ProjectService.get")
  def test_reopen_project_success(self, mock_get):
    user = MagicMock()
    project_mock = MagicMock()
    project_mock.status = "CONCLUDED"
    project_mock.closed_at = timezone.now() - timedelta(days=2)
    mock_get.return_value = project_mock

    reopened = ProjectService.reopen(user, "proj-id")
    self.assertEqual(reopened.status, "OPEN")
    project_mock.save.assert_called_once()

  @patch("apps.projects_and_clients.services.project.ProjectService.get")
  def test_reopen_project_fails_period_expired(self, mock_get):
    user = MagicMock()
    project_mock = MagicMock()
    project_mock.status = "CONCLUDED"
    project_mock.closed_at = timezone.now() - timedelta(days=8)
    mock_get.return_value = project_mock

    with self.assertRaises(ReopenPeriodExpiredError):
      ProjectService.reopen(user, "proj-id")

  @patch("apps.projects_and_clients.services.project.ProjectService.get")
  def test_reopen_project_already_open(self, mock_get):
    user = MagicMock()
    project_mock = MagicMock()
    project_mock.status = "OPEN"
    mock_get.return_value = project_mock

    with self.assertRaises(ProjectAlreadyOpenError):
      ProjectService.reopen(user, "proj-id")

  @patch("apps.projects_and_clients.services.project.ProjectService.get")
  def test_reopen_project_never_closed(self, mock_get):
    user = MagicMock()
    project_mock = MagicMock()
    project_mock.status = "PARTIALLY_CONCLUDED"
    project_mock.closed_at = None
    mock_get.return_value = project_mock

    with self.assertRaises(ProjectNeverClosedError):
      ProjectService.reopen(user, "proj-id")


class TestProjectService_Delete(TestCase):
  @patch("apps.projects_and_clients.services.project.ProjectService.get")
  def test_delete_project_success(self, mock_get):
    user = MagicMock()
    project_mock = MagicMock()
    mock_get.return_value = project_mock

    ProjectService.delete(user, "proj-id")
    project_mock.delete.assert_called_once()
