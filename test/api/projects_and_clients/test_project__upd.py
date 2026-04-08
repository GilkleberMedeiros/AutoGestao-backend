import uuid
from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
from apps.projects_and_clients.models import Client, Project

class BaseProjectTestCase(AuthenticatedTestCase):
  """Helper setup for project update tests."""

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

  @classmethod
  def tearDownClass(cls):
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


class ProjectsRoute_Update(BaseProjectTestCase):
  def test_update_project_success(self):
    project = Project.objects.create(
      user=self.user,
      client=self.client_obj,
      name="Test Update",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      status="OPEN"
    )
    token = self._get_valid_token()
    data = {
      "name": "Updated Project", 
      "estimated_deadline": "2026-12-31", 
      "estimated_cost": 200.00,
    }

    res = self.client.put(f"{project.id}", data=data, headers={"Authorization": f"Bearer {token}"})
    
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["name"], "Updated Project")
    self.assertEqual(float(res.json()["estimated_cost"]), 200.0)

  def test_update_project_closed_returns_403(self):
    project = Project.objects.create(
      user=self.user,
      client=self.client_obj,
      name="Test Update",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      status="CONCLUDED"
    )
    token = self._get_valid_token()
    data = {
      "name": "Updated Project", 
      "estimated_deadline": "2026-12-31", 
      "estimated_cost": 200.00,
    }

    res = self.client.put(f"{project.id}", data=data, headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 403)


class ProjectsRoute_PartialUpdate(BaseProjectTestCase):
  def test_partial_update_project_success(self):
    project = Project.objects.create(
      user=self.user,
      client=self.client_obj,
      name="Test Update",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      status="OPEN"
    )
    token = self._get_valid_token()
    data = {"name": "Partially Updated Project"}

    res = self.client.patch(f"{project.id}", data=data, headers={"Authorization": f"Bearer {token}"})
    
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["name"], "Partially Updated Project")


class ProjectsRoute_Close_Reopen(BaseProjectTestCase):
  from django.utils import timezone
  from datetime import timedelta

  def test_close_project_success(self):
    project = Project.objects.create(
      user=self.user,
      client=self.client_obj,
      name="Test Update",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      status="OPEN"
    )
    token = self._get_valid_token()
    data = {"status": "CONCLUDED", "actual_deadline": "2026-12-31", "actual_cost": 100.0, "spent_time": 1000}

    res = self.client.patch(f"{project.id}/close", data=data, headers={"Authorization": f"Bearer {token}"})
    
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["status"], "CONCLUDED")

  def test_close_project_invalid_status_returns_400(self):
    project = Project.objects.create(
      user=self.user,
      client=self.client_obj,
      name="Test Update",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      status="OPEN"
    )
    token = self._get_valid_token()
    data = {"status": "WRONG_STATUS"}

    res = self.client.patch(f"{project.id}/close", data=data, headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 400)

  def test_reopen_project_success(self):
    from django.utils import timezone
    from datetime import timedelta
    project = Project.objects.create(
      user=self.user,
      client=self.client_obj,
      name="Test Update",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      status="CONCLUDED",
      closed_at=timezone.now() - timedelta(days=2)
    )
    token = self._get_valid_token()

    res = self.client.post(f"{project.id}/reopen", headers={"Authorization": f"Bearer {token}"})
    
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json()["status"], "OPEN")

  def test_reopen_project_never_closed_returns_400(self):
    project = Project.objects.create(
      user=self.user,
      client=self.client_obj,
      name="Test Update",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      status="CONCLUDED"
    )
    token = self._get_valid_token()

    res = self.client.post(f"{project.id}/reopen", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 400)

  def test_reopen_project_period_expired_returns_403(self):
    from django.utils import timezone
    from datetime import timedelta
    project = Project.objects.create(
      user=self.user,
      client=self.client_obj,
      name="Test Update",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      status="CONCLUDED",
      closed_at=timezone.now() - timedelta(days=10)
    )
    token = self._get_valid_token()

    res = self.client.post(f"{project.id}/reopen", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 403)


class ProjectsRoute_Delete(BaseProjectTestCase):
  def test_delete_project_success(self):
    project = Project.objects.create(
      user=self.user,
      client=self.client_obj,
      name="Test Update",
      estimated_deadline="2026-12-31",
      estimated_cost=100.00,
      status="OPEN"
    )
    token = self._get_valid_token()

    res = self.client.delete(f"{project.id}", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200)

  def test_delete_project_not_found(self):
    token = self._get_valid_token()
    res = self.client.delete(f"{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 404)
