"""
.projects_rankings method unit tests.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import date

from apps.finances.services.dashboard import DashboardService, InvalidRankingsCountError
from apps.finances.schemas.dashboard import DashboardPeriodFilter


class TestDashboardService_ProjectsRankings(TestCase):
  def _make_projects_mocks(self):
    # Project 1: High gain, High cost, High profit, High hour profit
    p1 = MagicMock()
    p1.calc_project_total_gain.return_value = 1000.0
    p1.calc_project_total_cost.return_value = -500.0
    p1.calc_project_profitability.return_value = 500.0
    p1.calc_project_hour_profitability.return_value = 100.0
    p1.task_set.all.return_value = []

    # Project 2: Low gain, Low cost, Low profit, Low hour profit
    p2 = MagicMock()
    p2.calc_project_total_gain.return_value = 200.0
    p2.calc_project_total_cost.return_value = -50.0
    p2.calc_project_profitability.return_value = 150.0
    p2.calc_project_hour_profitability.return_value = 30.0
    p2.task_set.all.return_value = []

    # Project 3: Medium gain, Very high cost (most negative), Medium profit, Medium hour profit
    p3 = MagicMock()
    p3.calc_project_total_gain.return_value = 600.0
    p3.calc_project_total_cost.return_value = -800.0
    p3.calc_project_profitability.return_value = -200.0
    p3.calc_project_hour_profitability.return_value = -40.0
    p3.task_set.all.return_value = []

    return [p1, p2, p3]

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_calculation_and_sorting(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    # Testing with 3 projects
    p1, p2, p3 = self._make_projects_mocks()
    mock_projects_qs.return_value = [p1, p2, p3]

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.projects_rankings(rankings_count=2)

    # Total Gain Rank: p1 (1000), p3 (600)
    self.assertEqual(result["total_gain"][0]["project"], p1)
    self.assertEqual(result["total_gain"][0]["value"], 1000.0)
    self.assertEqual(result["total_gain"][1]["project"], p3)
    self.assertEqual(result["total_gain"][1]["value"], 600.0)

    # Total Cost Rank: sorted by value ascending (most negative first)
    # p3 (-800), p1 (-500)
    self.assertEqual(result["total_cost"][0]["project"], p3)
    self.assertEqual(result["total_cost"][0]["value"], -800.0)
    self.assertEqual(result["total_cost"][1]["project"], p1)
    self.assertEqual(result["total_cost"][1]["value"], -500.0)

    # Profitability Rank: p1 (500), p2 (150)
    self.assertEqual(result["profitability"][0]["project"], p1)
    self.assertEqual(result["profitability"][0]["value"], 500.0)
    self.assertEqual(result["profitability"][1]["project"], p2)
    self.assertEqual(result["profitability"][1]["value"], 150.0)

    # Hour Profitability Rank: p1 (100), p2 (30)
    self.assertEqual(result["hour_profitability"][0]["project"], p1)
    self.assertEqual(result["hour_profitability"][0]["value"], 100.0)
    self.assertEqual(result["hour_profitability"][1]["project"], p2)
    self.assertEqual(result["hour_profitability"][1]["value"], 30.0)

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_slicing_less_projects_than_available(
    self, mock_projects_qs
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    # Three projects available to rank
    p1, p2, p3 = self._make_projects_mocks()
    mock_projects_qs.return_value = [p1, p2, p3]

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.projects_rankings(rankings_count=1)

    # Only 1 project for each rank
    self.assertEqual(len(result["total_gain"]), 1)
    self.assertEqual(len(result["total_cost"]), 1)
    self.assertEqual(len(result["profitability"]), 1)
    self.assertEqual(len(result["hour_profitability"]), 1)

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_slicing_more_projects_than_available(
    self, mock_projects_qs
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    # Three projects available to rank
    p1, p2, p3 = self._make_projects_mocks()
    mock_projects_qs.return_value = [p1, p2, p3]

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.projects_rankings(rankings_count=5)

    # Only 3 projects for each rank
    self.assertEqual(len(result["total_gain"]), 3)
    self.assertEqual(len(result["total_cost"]), 3)
    self.assertEqual(len(result["profitability"]), 3)
    self.assertEqual(len(result["hour_profitability"]), 3)

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_negative_rankings_count_raise_error(
    self, mock_projects_qs
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    service = DashboardService(user, period, includes_open_projects=True)

    with self.assertRaises(InvalidRankingsCountError):
      service.projects_rankings(rankings_count=-1)

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_zero_rankings_count_raise_error(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    service = DashboardService(user, period, includes_open_projects=True)

    with self.assertRaises(InvalidRankingsCountError):
      service.projects_rankings(rankings_count=0)

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_empty_projects(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_projects_qs.return_value = []

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.projects_rankings()

    self.assertEqual(result["total_gain"], [])
    self.assertEqual(result["total_cost"], [])
    self.assertEqual(result["profitability"], [])
    self.assertEqual(result["hour_profitability"], [])
