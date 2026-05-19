from datetime import date, timedelta
from django.utils import timezone

from test.api.finances.dashboard.test_fast_views import BaseDashboardTestCase
from apps.projects_and_clients.models import Client, Project, Task
from apps.finances.models import MovGroup, Movimentation


class DashboardIncomeProjectsCompositionRoute_Get(BaseDashboardTestCase):
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

  def test_income_projects_composition_calculation_logic(self):
    """
    Test the basic calculation and composition logic.
    Concluded Project: Profit 6000
    Open Project: Profit 2500
    Total Profitability = 8500
    Open Project % = (2500 / 8500) * 100 = 29.41
    Concluded Project % = (6000 / 8500) * 100 = 70.59
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
      "income-projects-composition", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertIn("composition", data)
    self.assertIn("total_profitability", data)

    self.assertEqual(data["total_profitability"], 8500.0)
    composition = data["composition"]
    self.assertEqual(len(composition), 2)

    # Validate percentages and values
    for item in composition:
      if item["project"]["name"] == "Open Project":
        self.assertEqual(item["profit"], 2500.0)
        self.assertEqual(item["percentage"], 29.41)
      elif item["project"]["name"] == "Concluded Project":
        self.assertEqual(item["profit"], 6000.0)
        self.assertEqual(item["percentage"], 70.59)
      else:
        self.fail("Unexpected project in composition")

  def test_income_projects_composition_excludes_open_projects(self):
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
    }

    res = self.client.get(
      "income-projects-composition", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertEqual(data["total_profitability"], 6000.0)
    self.assertEqual(len(data["composition"]), 1)
    self.assertEqual(data["composition"][0]["project"]["name"], "Concluded Project")
    self.assertEqual(data["composition"][0]["percentage"], 100.0)

  def test_income_projects_composition_excludes_cancelled_projects(self):
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
    }

    res = self.client.get(
      "income-projects-composition", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertEqual(data["total_profitability"], 0.0)
    self.assertEqual(len(data["composition"]), 0)

  def test_income_projects_composition_excludes_zero_or_negative_profit_projects(self):
    """
    Test if projects with zero or negative profit are excluded from the composition.
    """
    today = timezone.now().date()
    
    # Project with Zero Profit (Gains: 1000, Costs: -1000)
    project_zero = Project.objects.create(
      user=self.user,
      client=self.client_model,
      name="Zero Profit Project",
      estimated_deadline=today + timedelta(days=10),
      estimated_cost=100.0,
      labor_fee=0.0,
      status=Project.CONCLUDED_STATUS,
    )
    task_z1 = Task.objects.create(project=project_zero, name="Task Z1", do_at=timezone.now())
    mov_z1 = Movimentation.objects.create(
      mov_group=self.mov_group, amount=1000.0, balance="+", reason="Gain", movemented_at=timezone.now()
    )
    task_z1.movimentation = mov_z1
    task_z1.save()
    
    task_z2 = Task.objects.create(project=project_zero, name="Task Z2", do_at=timezone.now())
    mov_z2 = Movimentation.objects.create(
      mov_group=self.mov_group, amount=1000.0, balance="-", reason="Cost", movemented_at=timezone.now()
    )
    task_z2.movimentation = mov_z2
    task_z2.save()

    # Project with Negative Profit (Gains: 500, Costs: -1000)
    project_negative = Project.objects.create(
      user=self.user,
      client=self.client_model,
      name="Negative Profit Project",
      estimated_deadline=today + timedelta(days=10),
      estimated_cost=100.0,
      labor_fee=0.0,
      status=Project.CONCLUDED_STATUS,
    )
    task_n1 = Task.objects.create(project=project_negative, name="Task N1", do_at=timezone.now())
    mov_n1 = Movimentation.objects.create(
      mov_group=self.mov_group, amount=500.0, balance="+", reason="Gain", movemented_at=timezone.now()
    )
    task_n1.movimentation = mov_n1
    task_n1.save()
    
    task_n2 = Task.objects.create(project=project_negative, name="Task N2", do_at=timezone.now())
    mov_n2 = Movimentation.objects.create(
      mov_group=self.mov_group, amount=1000.0, balance="-", reason="Cost", movemented_at=timezone.now()
    )
    task_n2.movimentation = mov_n2
    task_n2.save()

    token = self._get_valid_token()
    start_date = today - timedelta(days=7)
    end_date = today
    query_params = {
      "start_date": start_date.isoformat(),
      "end_date": end_date.isoformat(),
      "includes_open_projects": "true",
    }

    res = self.client.get(
      "income-projects-composition", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    # Initial setup has Open Project (Profit: 2500) and Concluded Project (Profit: 6000)
    # The zero and negative projects should be ignored. Total profitability remains 8500.
    self.assertEqual(data["total_profitability"], 8500.0)
    composition = data["composition"]
    self.assertEqual(len(composition), 2)
    
    project_names = [item["project"]["name"] for item in composition]
    self.assertNotIn("Zero Profit Project", project_names)
    self.assertNotIn("Negative Profit Project", project_names)

  def test_income_projects_composition_unauthenticated_returns_401(self):
    query_params = {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "includes_open_projects": "true",
    }
    res = self.client.get("income-projects-composition", data=query_params)
    self.assertEqual(res.status_code, 401)

  def test_income_projects_composition_invalid_user_email_returns_403(self):
    token = self._get_valid_token()

    self.user.is_email_valid = False
    self.user.save()

    query_params = {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "includes_open_projects": "true",
    }

    res = self.client.get(
      "income-projects-composition", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)

    data = res.json()
    self.assertEqual(data.get("success"), False)

  def test_income_projects_composition_missing_query_params_returns_422(self):
    token = self._get_valid_token()
    res = self.client.get("income-projects-composition", headers={"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 422)

  def test_income_projects_composition_empty_query_params_returns_422(self):
    token = self._get_valid_token()
    query_params = {}
    res = self.client.get(
      "income-projects-composition", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 422)

  def test_income_projects_composition_invalid_date_range_returns_422(self):
    token = self._get_valid_token()
    query_params = {
      "start_date": "2023-12-31",
      "end_date": "2023-01-01",
      "includes_open_projects": "true",
    }
    res = self.client.get(
      "income-projects-composition", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 422)
