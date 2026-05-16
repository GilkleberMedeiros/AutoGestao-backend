"""
.income_projects_composition method unit tests.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import date

from apps.finances.services.dashboard import DashboardService
from apps.finances.schemas.dashboard import DashboardPeriodFilter


class TestDashboardService_IncomeProjectsComposition(TestCase):
  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_income_projects_composition_calculation_logic(
    self, mock_projects_qs, mock_calc_metrics
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    p1 = MagicMock()
    p2 = MagicMock()

    mock_calc_metrics.return_value = [
      {
        "project": p1,
        "gain": 100.0,
        "cost": -40.0,
        "profit": 60.0,
        "hour_profit": 10.0,
      },
      {
        "project": p2,
        "gain": 200.0,
        "cost": -60.0,
        "profit": 140.0,
        "hour_profit": 20.0,
      },
    ]

    service = DashboardService(user, period, includes_open_projects=True)
    composition, total_profit = service.income_projects_composition()

    # Total profit = 60 + 140 = 200
    self.assertEqual(total_profit, 200.0)
    self.assertEqual(len(composition), 2)

    # p1 composition: 60/200 * 100 = 30%
    self.assertEqual(composition[0]["project"], p1)
    self.assertEqual(composition[0]["profit"], 60.0)
    self.assertEqual(composition[0]["percentage"], 30.0)

    # p2 composition: 140/200 * 100 = 70%
    self.assertEqual(composition[1]["project"], p2)
    self.assertEqual(composition[1]["profit"], 140.0)
    self.assertEqual(composition[1]["percentage"], 70.0)

  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_income_projects_composition_excludes_zero_or_negative_profit(
    self, mock_projects_qs, mock_calc_metrics
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    p1 = MagicMock()
    p2 = MagicMock()
    p3 = MagicMock()

    mock_calc_metrics.return_value = [
      {
        "project": p1,
        "gain": 100.0,
        "cost": 0.0,
        "profit": 100.0,
        "hour_profit": 10.0,
      },
      {
        "project": p2,
        "gain": 0.0,
        "cost": 0.0,
        "profit": 0.0,
        "hour_profit": 0.0,
      },
      {
        "project": p3,
        "gain": 50.0,
        "cost": -100.0,
        "profit": -50.0,
        "hour_profit": -5.0,
      },
    ]

    service = DashboardService(user, period, includes_open_projects=True)
    composition, total_profit = service.income_projects_composition()

    self.assertEqual(total_profit, 100.0)
    self.assertEqual(len(composition), 1)
    self.assertEqual(composition[0]["project"], p1)
    self.assertEqual(composition[0]["percentage"], 100.0)

  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_income_projects_composition_empty_projects(
    self, mock_projects_qs, mock_calc_metrics
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_calc_metrics.return_value = []

    service = DashboardService(user, period, includes_open_projects=True)
    composition, total_profit = service.income_projects_composition()

    self.assertEqual(composition, [])
    self.assertEqual(total_profit, 0.0)

  @patch("apps.finances.services.dashboard.DashboardService._calc_projects_base_metrics")
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_income_projects_composition_all_zero_or_negative_profit(
    self, mock_projects_qs, mock_calc_metrics
  ):
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
      },
      {
        "project": MagicMock(),
        "gain": 50.0,
        "cost": -60.0,
        "profit": -10.0,
        "hour_profit": -1.0,
      },
    ]

    service = DashboardService(user, period, includes_open_projects=True)
    composition, total_profit = service.income_projects_composition()

    self.assertEqual(composition, [])
    self.assertEqual(total_profit, 0.0)
