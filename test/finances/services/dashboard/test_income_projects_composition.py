"""
.income_projects_composition method unit tests.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import date

from apps.finances.services.dashboard import DashboardService
from apps.finances.schemas.dashboard import DashboardPeriodFilter


class TestDashboardService_IncomeProjectsComposition(TestCase):
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_income_projects_composition_calls_projects_qs_when_none_provided(
    self, mock_projects_qs
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    mock_projects_qs.return_value = []

    DashboardService.income_projects_composition(
      user, period, includes_open_projects=True
    )

    mock_projects_qs.assert_called_once_with(user, period, True)

  def test_income_projects_composition_uses_provided_projects_qs(self):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_qs = MagicMock()

    with patch(
      "apps.finances.services.dashboard.DashboardService._projects_qs"
    ) as mock_projects_qs:
      DashboardService.income_projects_composition(
        user, period, True, projects_qs=mock_qs
      )
      mock_projects_qs.assert_not_called()

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_income_projects_composition_calculation_logic(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    # Project 1: profit = 60
    p1 = MagicMock()
    p1.calc_project_profitability.return_value = 60.0
    p1.task_set.all.return_value = []

    # Project 2: profit = 140
    p2 = MagicMock()
    p2.calc_project_profitability.return_value = 140.0
    p2.task_set.all.return_value = []

    mock_projects_qs.return_value = [p1, p2]

    composition, total_profit = DashboardService.income_projects_composition(
      user, period, includes_open_projects=True
    )

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

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_income_projects_composition_excludes_zero_or_negative_profit(
    self, mock_projects_qs
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    # Project 1: profit = 100 (included)
    p1 = MagicMock()
    p1.calc_project_profitability.return_value = 100.0
    p1.task_set.all.return_value = []

    # Project 2: profit = 0 (excluded)
    p2 = MagicMock()
    p2.calc_project_profitability.return_value = 0.0
    p2.task_set.all.return_value = []

    # Project 3: profit = -50 (excluded)
    p3 = MagicMock()
    p3.calc_project_profitability.return_value = -50.0
    p3.task_set.all.return_value = []

    mock_projects_qs.return_value = [p1, p2, p3]

    composition, total_profit = DashboardService.income_projects_composition(
      user, period, includes_open_projects=True
    )

    self.assertEqual(total_profit, 100.0)
    self.assertEqual(len(composition), 1)
    self.assertEqual(composition[0]["project"], p1)
    self.assertEqual(composition[0]["percentage"], 100.0)

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_income_projects_composition_empty_projects(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_projects_qs.return_value = []

    composition, total_profit = DashboardService.income_projects_composition(
      user, period, includes_open_projects=True
    )

    self.assertEqual(composition, [])
    self.assertEqual(total_profit, 0.0)

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_income_projects_composition_all_zero_or_negative_profit(
    self, mock_projects_qs
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    p1 = MagicMock()
    p1.calc_project_profitability.return_value = 0.0
    p1.task_set.all.return_value = []

    p2 = MagicMock()
    p2.calc_project_profitability.return_value = -10.0
    p2.task_set.all.return_value = []

    mock_projects_qs.return_value = [p1, p2]

    composition, total_profit = DashboardService.income_projects_composition(
      user, period, includes_open_projects=True
    )

    self.assertEqual(composition, [])
    self.assertEqual(total_profit, 0.0)
