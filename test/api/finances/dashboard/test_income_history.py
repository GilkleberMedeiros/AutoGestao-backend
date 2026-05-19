from datetime import timedelta
from django.utils import timezone

from test.api.finances.dashboard.test_fast_views import BaseDashboardTestCase
from apps.projects_and_clients.models import Client, Project, Task
from apps.finances.models import MovGroup, Movimentation


class DashboardIncomeHistoryRoute_Get(BaseDashboardTestCase):
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

    # Create project 1 with a task movimentation yesterday
    self.project_1 = Project.objects.create(
      user=self.user,
      client=self.client_model,
      name="Project 1",
      estimated_deadline=self.today + timedelta(days=10),
      estimated_cost=100.0,
      labor_fee=0.0,
      status=Project.OPEN_STATUS,
    )
    task1 = Task.objects.create(
      project=self.project_1, name="Task 1", do_at=timezone.now()
    )
    mov1 = Movimentation.objects.create(
      mov_group=self.project_mov_group,
      amount=1000.0,
      balance="+",
      reason="Gain",
      movemented_at=timezone.now() - timedelta(days=1),
    )
    task1.movimentation = mov1
    task1.save()

    # Create personal finance movimentation today
    Movimentation.objects.create(
      mov_group=self.personal_mov_group,
      amount=500.0,
      balance="+",
      reason="Personal Gain",
      movemented_at=timezone.now(),
    )

  def test_income_history_calculation_logic(self):
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
      "income-history", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertTrue(isinstance(data, list))
    self.assertEqual(len(data), 3)

    date_str_1 = (self.today - timedelta(days=2)).isoformat()
    date_str_2 = (self.today - timedelta(days=1)).isoformat()
    date_str_3 = self.today.isoformat()

    self.assertEqual(data[0]["date"], date_str_1)
    self.assertEqual(data[0]["profit"], 0.0)

    self.assertEqual(data[1]["date"], date_str_2)
    self.assertEqual(data[1]["profit"], 1000.0)

    self.assertEqual(data[2]["date"], date_str_3)
    self.assertEqual(data[2]["profit"], 500.0)

  def test_income_history_excludes_personal_finances(self):
    token = self._get_valid_token()

    start_date = self.today - timedelta(days=2)
    end_date = self.today

    query_params = {
      "start_date": start_date.isoformat(),
      "end_date": end_date.isoformat(),
      "includes_open_projects": "true",
      "includes_personal_finances": "false",
    }

    res = self.client.get(
      "income-history", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 200)

    data = res.json()
    self.assertTrue(isinstance(data, list))
    self.assertEqual(len(data), 3)

    date_str_1 = (self.today - timedelta(days=2)).isoformat()
    date_str_2 = (self.today - timedelta(days=1)).isoformat()
    date_str_3 = self.today.isoformat()

    self.assertEqual(data[0]["date"], date_str_1)
    self.assertEqual(data[0]["profit"], 0.0)

    self.assertEqual(data[1]["date"], date_str_2)
    self.assertEqual(data[1]["profit"], 1000.0)

    self.assertEqual(data[2]["date"], date_str_3)
    self.assertEqual(data[2]["profit"], 0.0)

  def test_income_history_unauthenticated_returns_401(self):

    query_params = {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "includes_open_projects": "true",
      "includes_personal_finances": "true",
    }
    res = self.client.get("income-history", data=query_params)
    self.assertEqual(res.status_code, 401)

  def test_income_history_invalid_user_email_returns_403(self):
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
      "income-history", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)

  def test_income_history_missing_query_params_returns_422(self):
    token = self._get_valid_token()
    res = self.client.get(
      "income-history", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 422)

  def test_income_history_empty_query_params_returns_422(self):
    token = self._get_valid_token()
    query_params = {}
    res = self.client.get(
      "income-history", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 422)

  def test_income_history_invalid_date_range_returns_422(self):
    token = self._get_valid_token()
    query_params = {
      "start_date": "2023-12-31",
      "end_date": "2023-01-01",
      "includes_open_projects": "true",
      "includes_personal_finances": "true",
    }
    res = self.client.get(
      "income-history", data=query_params, headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 422)
