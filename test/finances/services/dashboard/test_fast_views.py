"""
.fast_views method unit tests.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import date

from apps.finances.services.dashboard import DashboardService
from apps.finances.schemas.dashboard import DashboardPeriodFilter


class TestDashboardService_FastViews(TestCase):
  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_fast_views_calculation_logic(self, mock_projects_qs, mock_calc_metrics):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    mock_calc_metrics.return_value = [
      {
        "project": MagicMock(),
        "gain": 100.0,
        "cost": -40.0,
        "profit": 60.0,
        "hour_profit": 10.0,
      },
      {
        "project": MagicMock(),
        "gain": 250.0,
        "cost": -100.0,
        "profit": 150.0,
        "hour_profit": 25.0,
      },
    ]

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.fast_views()

    # Verify totals
    self.assertEqual(result["total_gains"], 350.0)
    self.assertEqual(result["total_costs"], -140.0)
    self.assertEqual(result["profitability"], 210.0)

    mock_calc_metrics.assert_called_once()

  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_fast_views_empty_projects(self, mock_projects_qs, mock_calc_metrics):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_calc_metrics.return_value = []

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.fast_views()

    self.assertEqual(result["total_gains"], 0.0)
    self.assertEqual(result["total_costs"], 0.0)
    self.assertEqual(result["profitability"], 0.0)

  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_fast_views_negative_profitability(self, mock_projects_qs, mock_calc_metrics):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    mock_calc_metrics.return_value = [
      {
        "project": MagicMock(),
        "gain": 50.0,
        "cost": -100.0,
        "profit": -50.0,
        "hour_profit": -5.0,
      }
    ]

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.fast_views()

    self.assertEqual(result["profitability"], -50.0)
    self.assertEqual(result["total_gains"], 50.0)
    self.assertEqual(result["total_costs"], -100.0)

  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_fast_views_zero_gains_and_costs(self, mock_projects_qs, mock_calc_metrics):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    mock_calc_metrics.return_value = [
      {
        "project": MagicMock(),
        "gain": 0.0,
        "cost": 0.0,
        "profit": 0.0,
        "hour_profit": 0.0,
      }
    ]

    service = DashboardService(user, period, includes_open_projects=True)
    result = service.fast_views()

    self.assertEqual(result["total_gains"], 0.0)
    self.assertEqual(result["total_costs"], 0.0)
    self.assertEqual(result["profitability"], 0.0)
