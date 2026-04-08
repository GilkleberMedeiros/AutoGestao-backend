from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import uuid

from apps.users.models import User
from apps.projects_and_clients.models import Client, Project
from apps.projects_and_clients.services.project import (
  ProjectService,
  ResourceNotFoundError,
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


class BaseTestReadCreate(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="Test User", email="test@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Other User", email="other@example.com", password="password123"
    )
    cls.project_client = Client.objects.create(
      user=cls.user, name="Client A", cpf="12345678901"
    )

    cls.project_a = Project.objects.create(
      user=cls.user,
      client=cls.project_client,
      name="Project A",
      description="Desc A",
      estimated_deadline="2026-12-31",
      estimated_cost="1000.00",
      colortag="#ff0000",
    )

  @classmethod
  def tearDownClass(cls):
    cls.project_client.delete()
    cls.other_user.delete()
    cls.user.delete()
    super().tearDownClass()


class BaseTestUpdateDelete(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="Test User Update", email="testupdate@example.com", password="password123"
    )
    cls.project_client = Client.objects.create(
      user=cls.user, name="Client U", cpf="12345678902"
    )

  @classmethod
  def tearDownClass(cls):
    cls.project_client.delete()
    cls.user.delete()
    super().tearDownClass()


class TestCreateProject(BaseTestReadCreate):
  def test_create_project_success(self):
    data = CreateProjectReq(
      name="New Project",
      description="Desc",
      estimated_deadline="2026-12-31",
      estimated_cost="1000.00",
      colortag="#ff0000",
      client_id=str(self.project_client.id),
    )
    project = ProjectService.create(self.user, data)
    self.assertEqual(project.name, "New Project")
    self.assertEqual(project.user_id, self.user.id)
    self.assertEqual(project.status, "OPEN")

  def test_create_project_client_not_found(self):
    data = CreateProjectReq(
      name="New Project",
      description="Desc",
      estimated_deadline="2026-12-31",
      estimated_cost="1000.00",
      colortag="#ff0000",
      client_id=str(uuid.uuid4()),
    )
    with self.assertRaises(ResourceNotFoundError):
      ProjectService.create(self.user, data)

  def test_create_project_other_user_client(self):
    data = CreateProjectReq(
      name="New Project",
      description="Desc",
      estimated_deadline="2026-12-31",
      estimated_cost="1000.00",
      colortag="#ff0000",
      client_id=str(self.project_client.id),
    )
    with self.assertRaises(ResourceNotFoundError):
      ProjectService.create(self.other_user, data)

  def test_create_project_fills_only_correct_fields(self):
    """
    Test if the create method will fills only the fields he should fill, even
    when other fields are specified.
    """
    data = CreateProjectReq(
      name="New Project",
      description="Desc",
      estimated_deadline="2026-12-31",
      estimated_cost="1000.00",
      colortag="#ff0000",
      profitability="1000.00",
      hour_profitability="1000.00",
      client_id=str(self.project_client.id),
    )
    project = ProjectService.create(self.user, data)
    self.assertIsNone(project.profitability)
    self.assertIsNone(project.hour_profitability)
    self.assertIsNone(project.spent_time)
    self.assertIsNone(project.actual_cost)
    self.assertIsNone(project.actual_deadline)


class TestGetProject(BaseTestReadCreate):
  def test_get_project_success(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="Test Get",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
    )
    result = ProjectService.get(self.user, str(project.id))
    self.assertEqual(result.id, project.id)

  def test_get_project_other_user(self):
    with self.assertRaises(ResourceNotFoundError):
      ProjectService.get(self.other_user, str(self.project_a.id))

  def test_get_project_not_found(self):
    with self.assertRaises(ResourceNotFoundError):
      ProjectService.get(self.user, str(uuid.uuid4()))


class TestListProjects(BaseTestReadCreate):
  def test_list_projects(self):
    Project.objects.all().delete()
    Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="P1",
      estimated_cost=10,
      estimated_deadline="2026-01-01",
      status="OPEN",
      colortag="#000",
    )
    Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="P2",
      estimated_cost=20,
      estimated_deadline="2026-01-01",
      status="CONCLUDED",
      colortag="#fff",
    )

    # Test no filter
    filters = ProjectFilterSchema()
    self.assertEqual(ProjectService.list(self.user, filters).count(), 2)

    # Test status filter
    filters_status = ProjectFilterSchema(status="CONCLUDED")
    self.assertEqual(ProjectService.list(self.user, filters_status).count(), 1)

    # Test colortag filter
    filters_color = ProjectFilterSchema(colortag="#000")
    self.assertEqual(ProjectService.list(self.user, filters_color).count(), 1)

  def test_list_projects_other_user(self):
    filters = ProjectFilterSchema()
    self.assertEqual(ProjectService.list(self.other_user, filters).count(), 0)


class TestUpdateProject(BaseTestUpdateDelete):
  def test_update_open_project(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="Before Update",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
      status="OPEN",
    )
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
    updated = ProjectService.update(self.user, str(project.id), data)
    self.assertEqual(updated.name, "After Update")

  def test_update_closed_project_fails(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="Closed Proj",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
      status="CONCLUDED",
    )
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
      ProjectService.update(self.user, str(project.id), data)


class TestPartialUpdateProject(BaseTestUpdateDelete):
  def test_partial_update_open_project(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="Before Update",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
      status="OPEN",
    )
    data = PartialUpdateProjectReq(
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
    updated = ProjectService.partial_update(self.user, str(project.id), data)
    self.assertEqual(updated.name, "After Update")

  def test_partial_update_closed_project_fails(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="Closed Proj",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
      status="CONCLUDED",
    )
    data = PartialUpdateProjectReq(name="Try Edit")

    with self.assertRaises(ProjectClosedForEditError):
      ProjectService.partial_update(self.user, str(project.id), data)


class TestCloseProject(BaseTestUpdateDelete):
  def test_close_project(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="To Close",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
      status="OPEN",
    )
    data = ProjectCloseSchema(
      actual_deadline="2026-12-31",
      actual_cost="100.00",
      spent_time=timedelta(hours=100),
      status="CONCLUDED",
    )
    closed = ProjectService.close(self.user, str(project.id), data)
    self.assertEqual(closed.status, "CONCLUDED")
    self.assertIsNotNone(closed.closed_at)
    # TODO: Add verifications for profitability and hour_profitability

  def test_close_project_invalid_status(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="To Close",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
      status="OPEN",
    )
    data = ProjectCloseSchema(status="NOT_A_STATUS")
    with self.assertRaises(InvalidCloseStatusError):
      ProjectService.close(self.user, str(project.id), data)


class TestReopenProject(BaseTestUpdateDelete):
  def test_reopen_project_success(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="To Reopen",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
      status="CONCLUDED",
      closed_at=timezone.now() - timedelta(days=2),
    )
    reopened = ProjectService.reopen(self.user, str(project.id))
    self.assertEqual(reopened.status, "OPEN")
    self.assertIsNotNone(reopened.closed_at)  # Should retain the last closed_at

  def test_reopen_project_fails(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="Old Closed",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
      status="CONCLUDED",
      closed_at=timezone.now() - timedelta(days=8),
    )
    with self.assertRaises(ReopenPeriodExpiredError):
      ProjectService.reopen(self.user, str(project.id))

  def test_reopen_project_already_open(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="Open Proj",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
      status="OPEN",
    )
    with self.assertRaises(ProjectAlreadyOpenError):
      ProjectService.reopen(self.user, str(project.id))

  def test_reopen_project_never_closed(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="Never Closed",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
      status="PARTIALLY_CONCLUDED",
    )
    with self.assertRaises(ProjectNeverClosedError):
      ProjectService.reopen(self.user, str(project.id))


class TestDeleteProject(BaseTestUpdateDelete):
  def test_delete_project_success(self):
    project = Project.objects.create(
      user=self.user,
      client=self.project_client,
      name="To Delete",
      estimated_deadline="2026-12-31",
      estimated_cost=100,
      status="OPEN",
    )
    ProjectService.delete(self.user, str(project.id))
    with self.assertRaises(ResourceNotFoundError):
      ProjectService.get(self.user, str(project.id))
