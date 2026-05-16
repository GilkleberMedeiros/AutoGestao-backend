"""
.projects_rankings method unit tests.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import date

from apps.finances.services.dashboard import DashboardService, InvalidRankingsCountError
from apps.finances.schemas.dashboard import DashboardPeriodFilter


class TestDashboardService_ProjectsRankings(TestCase):
  def _make_metrics_mocks(self):
    p1 = MagicMock()
    p2 = MagicMock()
    p3 = MagicMock()

    return [
      {
        "project": p1,
        "gain": 1000.0,
        "cost": -500.0,
        "profit": 500.0,
        "hour_profit": 100.0,
      },
      {
        "project": p2,
        "gain": 200.0,
        "cost": -50.0,
        "profit": 150.0,
        "hour_profit": 30.0,
      },
      {
        "project": p3,
        "gain": 600.0,
        "cost": -800.0,
        "profit": -200.0,
        "hour_profit": -40.0,
      },
    ]

  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_calculation_and_sorting(
    self, mock_projects_qs, mock_calc_metrics
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    metrics = self._make_metrics_mocks()
    mock_calc_metrics.return_value = metrics
    p1, p2, p3 = metrics[0]["project"], metrics[1]["project"], metrics[2]["project"]

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

  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_slicing_less_projects_than_available(
    self, mock_projects_qs, mock_calc_metrics
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_calc_metrics.return_value = self._make_metrics_mocks()

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.projects_rankings(rankings_count=1)

    # Only 1 project for each rank
    self.assertEqual(len(result["total_gain"]), 1)
    self.assertEqual(len(result["total_cost"]), 1)
    self.assertEqual(len(result["profitability"]), 1)
    self.assertEqual(len(result["hour_profitability"]), 1)

  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_slicing_more_projects_than_available(
    self, mock_projects_qs, mock_calc_metrics
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_calc_metrics.return_value = self._make_metrics_mocks()

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

  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_empty_projects(self, mock_projects_qs, mock_calc_metrics):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_calc_metrics.return_value = []

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.projects_rankings()

    self.assertEqual(result["total_gain"], [])
    self.assertEqual(result["total_cost"], [])
    self.assertEqual(result["profitability"], [])
    self.assertEqual(result["hour_profitability"], [])
