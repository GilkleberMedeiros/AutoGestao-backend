"""
.dashboard method unit tests.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import date

from apps.finances.services.dashboard import DashboardService
from apps.finances.schemas.dashboard import DashboardPeriodFilter


class TestDashboardService_Dashboard(TestCase):
  def setUp(self):
    self.user = MagicMock()
    self.period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 1, 31)
    )

    with patch("apps.finances.services.dashboard.DashboardService._projects_qs"):
      self.service = DashboardService(
        self.user, self.period, includes_open_projects=True
      )

  @patch("apps.finances.services.dashboard.DashboardService.fast_views")
  @patch("apps.finances.services.dashboard.DashboardService.projects_rankings")
  @patch(
    "apps.finances.services.dashboard.DashboardService.income_projects_composition"
  )
  @patch("apps.finances.services.dashboard.DashboardService.income_history")
  def test_dashboard_all_metrics_by_default(
    self, mock_history, mock_composition, mock_rankings, mock_fast_views
  ):
    # Set return values for mocked methods
    mock_fast_views.return_value = {"total_gains": 100.0}
    mock_rankings.return_value = {"total_gain": []}
    mock_composition.return_value = ([], 0.0)
    mock_history.return_value = []

    result = self.service.dashboard(includes_personal_finances=True, rankings_count=10)

    # Assertions
    self.assertEqual(result["projects_fast_views"], mock_fast_views.return_value)
    self.assertEqual(result["projects_rankings"], mock_rankings.return_value)
    self.assertEqual(
      result["income_projects_composition"], mock_composition.return_value
    )
    self.assertEqual(result["income_history"], mock_history.return_value)

    # Verify method calls
    mock_fast_views.assert_called_once()
    mock_rankings.assert_called_once_with(10)
    mock_composition.assert_called_once()
    mock_history.assert_called_once_with(True)

  @patch("apps.finances.services.dashboard.DashboardService.fast_views")
  @patch("apps.finances.services.dashboard.DashboardService.projects_rankings")
  @patch(
    "apps.finances.services.dashboard.DashboardService.income_projects_composition"
  )
  @patch("apps.finances.services.dashboard.DashboardService.income_history")
  def test_dashboard_selective_metrics(
    self, mock_history, mock_composition, mock_rankings, mock_fast_views
  ):
    # Set return values
    mock_fast_views.return_value = {"total_gains": 100.0}
    mock_history.return_value = []

    metrics = {"projects_fast_views": True, "income_history": True}

    result = self.service.dashboard(includes_personal_finances=False, metrics=metrics)

    # Assertions for requested metrics
    self.assertEqual(result["projects_fast_views"], mock_fast_views.return_value)
    self.assertEqual(result["income_history"], mock_history.return_value)

    # Assertions for non-requested metrics
    self.assertIsNone(result["projects_rankings"])
    self.assertIsNone(result["income_projects_composition"])

    # Verify method calls
    mock_fast_views.assert_called_once()
    mock_history.assert_called_once_with(False)
    mock_rankings.assert_not_called()
    mock_composition.assert_not_called()

  @patch("apps.finances.services.dashboard.DashboardService.fast_views")
  @patch("apps.finances.services.dashboard.DashboardService.projects_rankings")
  @patch(
    "apps.finances.services.dashboard.DashboardService.income_projects_composition"
  )
  @patch("apps.finances.services.dashboard.DashboardService.income_history")
  def test_dashboard_no_metrics_requested(
    self, mock_history, mock_composition, mock_rankings, mock_fast_views
  ):
    metrics = {"projects_fast_views": False, "projects_rankings": False}

    result = self.service.dashboard(includes_personal_finances=True, metrics=metrics)

    # All should be None
    self.assertIsNone(result["projects_fast_views"])
    self.assertIsNone(result["projects_rankings"])
    self.assertIsNone(result["income_projects_composition"])
    self.assertIsNone(result["income_history"])

    # No methods should be called
    mock_fast_views.assert_not_called()
    mock_rankings.assert_not_called()
    mock_composition.assert_not_called()
    mock_history.assert_not_called()
