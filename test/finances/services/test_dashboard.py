from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import date

from apps.finances.services.dashboard import DashboardService
from apps.finances.schemas.dashboard import DashboardPeriodFilter


class TestDashboardService_FastViews(TestCase):
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_fast_views_calls_projects_qs_when_none_provided(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    mock_projects_qs.return_value = []

    DashboardService.fast_views(user, period)

    mock_projects_qs.assert_called_once_with(user, period)

  def test_fast_views_uses_provided_projects_qs(self):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_qs = MagicMock()

    # If we provide projects_qs, _projects_qs should NOT be called.
    with patch(
      "apps.finances.services.dashboard.DashboardService._projects_qs"
    ) as mock_projects_qs:
      DashboardService.fast_views(user, period, projects_qs=mock_qs)
      mock_projects_qs.assert_not_called()

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_fast_views_calculation_logic(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    # Mock project 1
    project1 = MagicMock()
    project1.calc_project_total_gain.return_value = 100.0
    project1.calc_project_total_cost.return_value = -40.0
    project1.calc_project_profitability.return_value = 60.0
    tasks1 = ["task1", "task2"]
    project1.task_set.all.return_value = tasks1

    # Mock project 2
    project2 = MagicMock()
    project2.calc_project_total_gain.return_value = 250.0
    project2.calc_project_total_cost.return_value = -100.0
    project2.calc_project_profitability.return_value = 150.0
    tasks2 = ["task3"]
    project2.task_set.all.return_value = tasks2

    mock_projects_qs.return_value = [project1, project2]

    result = DashboardService.fast_views(user, period)

    # Verify totals
    self.assertEqual(result["projects_total_gains"], 350.0)
    self.assertEqual(result["projects_total_costs"], -140.0)
    self.assertEqual(result["project_profitability"], 210.0)

    # Verify that model methods were called with the correct task sets
    project1.calc_project_total_gain.assert_called_once_with(tasks1)
    project1.calc_project_total_cost.assert_called_once_with(tasks1)
    project1.calc_project_profitability.assert_called_once_with(tasks1)

    project2.calc_project_total_gain.assert_called_once_with(tasks2)
    project2.calc_project_total_cost.assert_called_once_with(tasks2)
    project2.calc_project_profitability.assert_called_once_with(tasks2)

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_fast_views_empty_projects(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_projects_qs.return_value = []

    result = DashboardService.fast_views(user, period)

    self.assertEqual(result["projects_total_gains"], 0.0)
    self.assertEqual(result["projects_total_costs"], 0.0)
    self.assertEqual(result["project_profitability"], 0.0)

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_fast_views_negative_profitability(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    project = MagicMock()
    project.calc_project_total_gain.return_value = 50.0
    project.calc_project_total_cost.return_value = -100.0
    project.calc_project_profitability.return_value = -50.0
    project.task_set.all.return_value = []

    mock_projects_qs.return_value = [project]

    result = DashboardService.fast_views(user, period)

    self.assertEqual(result["project_profitability"], -50.0)
    self.assertEqual(result["projects_total_gains"], 50.0)
    self.assertEqual(result["projects_total_costs"], -100.0)

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_fast_views_zero_gains_and_costs(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    project = MagicMock()
    project.calc_project_total_gain.return_value = 0.0
    project.calc_project_total_cost.return_value = 0.0
    project.calc_project_profitability.return_value = 0.0
    project.task_set.all.return_value = []

    mock_projects_qs.return_value = [project]

    result = DashboardService.fast_views(user, period)

    self.assertEqual(result["projects_total_gains"], 0.0)
    self.assertEqual(result["projects_total_costs"], 0.0)
    self.assertEqual(result["project_profitability"], 0.0)
