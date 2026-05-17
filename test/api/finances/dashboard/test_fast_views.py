from datetime import date, timedelta
from django.utils import timezone

from test.api.base import APIClient
from test.api.conftest import AuthenticatedTestCase
from apps.users.models import User
from apps.projects_and_clients.models import Client, Project, Task
from apps.finances.models import MovGroup, Movimentation


class BaseDashboardTestCase(AuthenticatedTestCase):
  """Helper setup for dashboard API tests."""

  user_create_data = {
    "name": "testuser",
    "email": "testapi@example.com",
    "password": "testpassword",
    "phone": "5584000000000",
    "is_email_valid": True,
  }
  user_create_model = User
  login_data = {"email": "testapi@example.com", "password": "testpassword"}
  URL = "/api/finances/dashboard/"

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

  @classmethod
  def tearDownClass(cls):
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def setUp(self):
    super().setUp()
    self.client = APIClient(path_prefix=self.URL)

  def _get_valid_token(self):
    return self.credentials["access"]


class DashboardFastViewsRoute_Get(BaseDashboardTestCase):
  def setUp(self):
    super().setUp()

    self.client_model = Client.objects.create(user=self.user, name="Test Client")
    self.mov_group = MovGroup.objects.create(user=self.user, name="Test Group")

    today = timezone.now().date()

    # 1. OPEN Project
    self.project_open = Project.objects.create(
      user=self.user,
      client=self.client_model,
      name="Open Project",
      estimated_deadline=today + timedelta(days=10),
      estimated_cost=100.0,
      labor_fee=1000.0,
      status=Project.OPEN_STATUS,
    )
    task1 = Task.objects.create(
      project=self.project_open, name="Task 1", do_at=timezone.now()
    )
    mov1 = Movimentation.objects.create(
      mov_group=self.mov_group,
      amount=2000.0,
      balance="+",
      reason="Gain",
      movemented_at=timezone.now(),
    )
    task1.movimentation = mov1
    task1.save()

    task2 = Task.objects.create(
      project=self.project_open, name="Task 2", do_at=timezone.now()
    )
    mov2 = Movimentation.objects.create(
      mov_group=self.mov_group,
      amount=500.0,
      balance="-",
      reason="Cost",
      movemented_at=timezone.now(),
    )
    task2.movimentation = mov2
    task2.save()

    # 2. CONCLUDED Project
    self.project_concluded = Project.objects.create(
      user=self.user,
      client=self.client_model,
      name="Concluded Project",
      estimated_deadline=today + timedelta(days=10),
      estimated_cost=100.0,
      labor_fee=2000.0,
      status=Project.CONCLUDED_STATUS,
    )
    task3 = Task.objects.create(
      project=self.project_concluded, name="Task 3", do_at=timezone.now()
    )
    mov3 = Movimentation.objects.create(
      mov_group=self.mov_group,
      amount=5000.0,
      balance="+",
      reason="Gain",
      movemented_at=timezone.now(),
    )
    task3.movimentation = mov3
    task3.save()

    task4 = Task.objects.create(
      project=self.project_concluded, name="Task 4", do_at=timezone.now()
    )
    mov4 = Movimentation.objects.create(
      mov_group=self.mov_group,
      amount=1000.0,
      balance="-",
      reason="Cost",
      movemented_at=timezone.now(),
    )
    task4.movimentation = mov4
    task4.save()

    # 3. CANCELLED Project
    self.project_cancelled = Project.objects.create(
      user=self.user,
      client=self.client_model,
      name="Cancelled Project",
      estimated_deadline=today + timedelta(days=10),
      estimated_cost=100.0,
      labor_fee=500.0,
      status=Project.CANCELLED_STATUS,
    )
    task5 = Task.objects.create(
      project=self.project_cancelled, name="Task 5", do_at=timezone.now()
    )
    mov5 = Movimentation.objects.create(
      mov_group=self.mov_group,
      amount=1000.0,
      balance="+",
      reason="Gain",
      movemented_at=timezone.now(),
    )
    task5.movimentation = mov5
    task5.save()

  def test_fast_views_calculation_logic(self):
    """
    Test the basic calculation logic.
    OPEN project: gains = 3000, costs = -500, profit = 2500
    CONCLUDED project: gains = 7000, costs = -1000, profit = 6000
    Total (with includes_open_projects=True) = gains 10000, costs -1500, profit 8500
    (CANCELLED project should naturally be ignored)
    """
    token = self._get_valid_token()

    today = date.today()
    start_date = today - timedelta(days=7)
    end_date = today

    query_params = {
      "start_date": start_date.isoformat(),
      "end_date": end_date.isoformat(),
      "includes_open_projects": "true",
    }

    res = self.client.get(
      "fast-views", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertEqual(data["total_gains"], 10000.0)
    self.assertEqual(data["total_costs"], -1500.0)
    self.assertEqual(data["profitability"], 8500.0)

  def test_fast_views_excludes_open_projects(self):
    """
    Test if projects with OPEN status are excluded when includes_open_projects=False.
    Total should only equal CONCLUDED project: gains 7000, costs -1000, profit 6000.
    """
    token = self._get_valid_token()

    today = date.today()
    start_date = today - timedelta(days=7)
    end_date = today

    query_params = {
      "start_date": start_date.isoformat(),
      "end_date": end_date.isoformat(),
      "includes_open_projects": "false",
    }

    res = self.client.get(
      "fast-views", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertEqual(data["total_gains"], 7000.0)
    self.assertEqual(data["total_costs"], -1000.0)
    self.assertEqual(data["profitability"], 6000.0)

  def test_fast_views_excludes_cancelled_projects(self):
    """
    Test if projects with CANCELLED status are completely ignored.
    If we delete OPEN and CONCLUDED, the result should be exactly 0.0 for everything,
    even if the CANCELLED project has a gain of 1500.
    """
    # Delete the OPEN and CONCLUDED projects to isolate the CANCELLED project
    self.project_open.delete()
    self.project_concluded.delete()

    token = self._get_valid_token()

    today = date.today()
    start_date = today - timedelta(days=7)
    end_date = today

    query_params = {
      "start_date": start_date.isoformat(),
      "end_date": end_date.isoformat(),
      "includes_open_projects": "true",
    }

    res = self.client.get(
      "fast-views", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertEqual(data["total_gains"], 0.0)
    self.assertEqual(data["total_costs"], 0.0)
    self.assertEqual(data["profitability"], 0.0)

  def test_fast_views_unauthenticated_returns_401(self):
    query_params = {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "includes_open_projects": "true",
    }
    res = self.client.get("fast-views", data=query_params)
    self.assertEqual(res.status_code, 401)

  def test_fast_views_invalid_user_email_returns_403(self):
    token = self._get_valid_token()

    self.user.is_email_valid = False
    self.user.save()

    query_params = {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "includes_open_projects": "true",
    }

    res = self.client.get(
      "fast-views", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)

    data = res.json()
    self.assertEqual(data.get("success"), False)

  def test_fast_views_missing_query_params_returns_422(self):
    token = self._get_valid_token()
    res = self.client.get("fast-views", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 422)

  def test_fast_views_empty_query_params_returns_422(self):
    token = self._get_valid_token()
    query_params = {}
    res = self.client.get(
      "fast-views", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 422)

  def test_fast_views_invalid_date_range_returns_422(self):
    token = self._get_valid_token()
    query_params = {
      "start_date": "2023-12-31",
      "end_date": "2023-01-01",
      "includes_open_projects": "true",
    }
    res = self.client.get(
      "fast-views", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 422)
