from datetime import date, timedelta
from django.utils import timezone

from test.api.finances.dashboard.test_fast_views import BaseDashboardTestCase
from apps.projects_and_clients.models import Client, Project, Task
from apps.finances.models import MovGroup, Movimentation


class DashboardProjectsRankingsRoute_Get(BaseDashboardTestCase):
  def setUp(self):
    super().setUp()

    self.client_model = Client.objects.create(user=self.user, name="Test Client")
    self.mov_group = MovGroup.objects.create(user=self.user, name="Test Group")

    today = timezone.now().date()

    # 1. OPEN Project (Gains: 3000, Costs: -500, Profit: 2500)
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

    # 2. CONCLUDED Project (Gains: 7000, Costs: -1000, Profit: 6000)
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

    # 3. CANCELLED Project (Gains: 1500, Costs: 0, Profit: 1500)
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

  def test_projects_rankings_calculation_logic(self):
    """
    Test the basic calculation and ranking logic.
    Concluded Project: Gain 7000, Cost -1000, Profit 6000
    Open Project: Gain 3000, Cost -500, Profit 2500
    Rankings should sort descending for gains/profit, ascending for costs (meaning more negative is top).
    """
    token = self._get_valid_token()

    today = date.today()
    start_date = today - timedelta(days=7)
    end_date = today

    query_params = {
      "start_date": start_date.isoformat(),
      "end_date": end_date.isoformat(),
      "includes_open_projects": "true",
      "rankings_count": 5,
    }

    res = self.client.get(
      "projects-rankings", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertIn("total_gain", data)
    self.assertIn("total_cost", data)
    self.assertIn("profitability", data)

    # Validate Gain Ranking (Concluded 7000 > Open 3000)
    gains = data["total_gain"]
    self.assertEqual(len(gains), 2)
    self.assertEqual(gains[0]["project"]["name"], "Concluded Project")
    self.assertEqual(gains[0]["value"], 7000.0)
    self.assertEqual(gains[1]["project"]["name"], "Open Project")
    self.assertEqual(gains[1]["value"], 3000.0)

    # Validate Cost Ranking (Concluded -1000 < Open -500)
    costs = data["total_cost"]
    self.assertEqual(len(costs), 2)
    self.assertEqual(costs[0]["project"]["name"], "Concluded Project")
    self.assertEqual(costs[0]["value"], -1000.0)
    self.assertEqual(costs[1]["project"]["name"], "Open Project")
    self.assertEqual(costs[1]["value"], -500.0)

  def test_projects_rankings_excludes_open_projects(self):
    """
    Test if projects with OPEN status are excluded when includes_open_projects=False.
    """
    token = self._get_valid_token()

    today = date.today()
    start_date = today - timedelta(days=7)
    end_date = today

    query_params = {
      "start_date": start_date.isoformat(),
      "end_date": end_date.isoformat(),
      "includes_open_projects": "false",
      "rankings_count": 5,
    }

    res = self.client.get(
      "projects-rankings", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertEqual(len(data["total_gain"]), 1)
    self.assertEqual(data["total_gain"][0]["project"]["name"], "Concluded Project")

  def test_projects_rankings_excludes_cancelled_projects(self):
    """
    Test if projects with CANCELLED status are completely ignored.
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
      "rankings_count": 5,
    }

    res = self.client.get(
      "projects-rankings", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertEqual(len(data["total_gain"]), 0)
    self.assertEqual(len(data["total_cost"]), 0)
    self.assertEqual(len(data["profitability"]), 0)

  def test_projects_rankings_unauthenticated_returns_401(self):
    query_params = {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "includes_open_projects": "true",
      "rankings_count": 5,
    }
    res = self.client.get("projects-rankings", data=query_params)
    self.assertEqual(res.status_code, 401)

  def test_projects_rankings_invalid_user_email_returns_403(self):
    token = self._get_valid_token()

    self.user.is_email_valid = False
    self.user.save()

    query_params = {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "includes_open_projects": "true",
      "rankings_count": 5,
    }

    res = self.client.get(
      "projects-rankings", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)

    data = res.json()
    self.assertEqual(data.get("success"), False)

  def test_projects_rankings_missing_query_params_returns_422(self):
    token = self._get_valid_token()
    res = self.client.get("projects-rankings", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 422)

  def test_projects_rankings_empty_query_params_returns_422(self):
    token = self._get_valid_token()
    query_params = {}
    res = self.client.get(
      "projects-rankings", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 422)

  def test_projects_rankings_invalid_rankings_count_returns_422(self):
    token = self._get_valid_token()
    query_params = {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "includes_open_projects": "true",
      "rankings_count": 0,
    }
    res = self.client.get(
      "projects-rankings", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 422)

    query_params["rankings_count"] = -1
    res = self.client.get(
      "projects-rankings", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 422)

  def test_projects_rankings_invalid_date_range_returns_422(self):
    token = self._get_valid_token()
    query_params = {
      "start_date": "2023-12-31",
      "end_date": "2023-01-01",
      "includes_open_projects": "true",
      "rankings_count": 5,
    }
    res = self.client.get(
      "projects-rankings", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 422)
