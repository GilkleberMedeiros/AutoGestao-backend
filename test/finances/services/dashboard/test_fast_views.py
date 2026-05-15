"""
.fast_views method unit tests.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import date

from apps.finances.services.dashboard import DashboardService
from apps.finances.schemas.dashboard import DashboardPeriodFilter


class TestDashboardService_FastViews(TestCase):
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

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.fast_views()

    # Verify totals
    self.assertEqual(result["total_gains"], 350.0)
    self.assertEqual(result["total_costs"], -140.0)
    self.assertEqual(result["profitability"], 210.0)

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

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.fast_views()

    self.assertEqual(result["total_gains"], 0.0)
    self.assertEqual(result["total_costs"], 0.0)
    self.assertEqual(result["profitability"], 0.0)

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

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.fast_views()

    self.assertEqual(result["profitability"], -50.0)
    self.assertEqual(result["total_gains"], 50.0)
    self.assertEqual(result["total_costs"], -100.0)

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

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.fast_views()

    self.assertEqual(result["total_gains"], 0.0)
    self.assertEqual(result["total_costs"], 0.0)
    self.assertEqual(result["profitability"], 0.0)
