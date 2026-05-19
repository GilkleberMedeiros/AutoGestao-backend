from datetime import timedelta
from django.utils import timezone

from test.api.finances.dashboard.test_fast_views import BaseDashboardTestCase
from apps.projects_and_clients.models import Client, Project, Task
from apps.finances.models import MovGroup, Movimentation


class DashboardRoute_Get(BaseDashboardTestCase):
  def setUp(self):
    super().setUp()

    self.client_model = Client.objects.create(user=self.user, name="Test Client")
    self.project_mov_group = MovGroup.objects.create(
      user=self.user, name="Project Group", relation="PROJECT"
    )
    self.personal_mov_group = MovGroup.objects.create(
      user=self.user, name="Personal Group", relation="NORELATION"
    )

    self.today = timezone.now().date()

    # Create Concluded Project (Gain: 5000, Cost: 1000 -> Profit: 4000)
    self.project_concluded = Project.objects.create(
      user=self.user,
      client=self.client_model,
      name="Concluded Project",
      estimated_deadline=self.today + timedelta(days=10),
      estimated_cost=100.0,
      labor_fee=0.0,
      status=Project.CONCLUDED_STATUS,
    )
    task1 = Task.objects.create(
      project=self.project_concluded, name="Task 1", do_at=timezone.now()
    )
    mov1 = Movimentation.objects.create(
      mov_group=self.project_mov_group,
      amount=5000.0,
      balance="+",
      reason="Gain",
      movemented_at=timezone.now(),
    )
    task1.movimentation = mov1
    task1.save()

    task2 = Task.objects.create(
      project=self.project_concluded, name="Task 2", do_at=timezone.now()
    )
    mov2 = Movimentation.objects.create(
      mov_group=self.project_mov_group,
      amount=1000.0,
      balance="-",
      reason="Cost",
      movemented_at=timezone.now(),
    )
    task2.movimentation = mov2
    task2.save()

    # Create personal finance movimentation
    Movimentation.objects.create(
      mov_group=self.personal_mov_group,
      amount=500.0,
      balance="+",
      reason="Personal Gain",
      movemented_at=timezone.now(),
    )

  def test_dashboard_all_metrics_by_default(self):
    token = self._get_valid_token()

    start_date = self.today - timedelta(days=2)
    end_date = self.today

    query_params = {
      "start_date": start_date.isoformat(),
      "end_date": end_date.isoformat(),
      "includes_open_projects": "true",
      "includes_personal_finances": "true",
    }

    res = self.client.get(
      "/api/finances/dashboard/",
      data=query_params,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertIsNotNone(data["projects_fast_views"])
    self.assertIsNotNone(data["projects_rankings"])
    self.assertIsNotNone(data["income_projects_composition"])
    self.assertIsNotNone(data["income_history"])

    # Verify calculation logic details
    fast_views = data["projects_fast_views"]
    self.assertEqual(fast_views["total_gains"], 5000.0)
    self.assertEqual(fast_views["total_costs"], -1000.0)
    self.assertEqual(fast_views["profitability"], 4000.0)

    history = data["income_history"]
    self.assertEqual(len(history), 3)
    # The last day (today) should include 4000 from concluded project + 500 personal
    self.assertEqual(history[2]["profit"], 4500.0)

  def test_dashboard_filters_metrics(self):
    token = self._get_valid_token()

    start_date = self.today - timedelta(days=2)
    end_date = self.today

    query_params = {
      "start_date": start_date.isoformat(),
      "end_date": end_date.isoformat(),
      "includes_open_projects": "true",
      "includes_personal_finances": "true",
      "include_metric": ["projects_fast_views", "income_history"],
    }

    res = self.client.get(
      "/api/finances/dashboard/",
      data=query_params,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertIsNotNone(data["projects_fast_views"])
    self.assertIsNone(data["projects_rankings"])
    self.assertIsNone(data["income_projects_composition"])
    self.assertIsNotNone(data["income_history"])

  def test_dashboard_unauthenticated_returns_401(self):
    query_params = {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "includes_open_projects": "true",
      "includes_personal_finances": "true",
    }
    res = self.client.get("/api/finances/dashboard/", data=query_params)
    self.assertEqual(res.status_code, 401)

  def test_dashboard_invalid_user_email_returns_403(self):
    token = self._get_valid_token()

    self.user.is_email_valid = False
    self.user.save()

    query_params = {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "includes_open_projects": "true",
      "includes_personal_finances": "true",
    }

    res = self.client.get(
      "/api/finances/dashboard/",
      data=query_params,
      headers={"Authorization": f"Bearer {token}"},
    )
    self.assertEqual(res.status_code, 403)

  def test_dashboard_invalid_rankings_count_returns_422(self):
    token = self._get_valid_token()
    query_params = {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "includes_open_projects": "true",
      "includes_personal_finances": "true",
      "rankings_count": "0",
    }
    res = self.client.get(
      "/api/finances/dashboard/",
      data=query_params,
      headers={"Authorization": f"Bearer {token}"},
    )

    self.assertEqual(res.status_code, 422)
