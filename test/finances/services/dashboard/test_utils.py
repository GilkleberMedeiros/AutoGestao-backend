"""
Test constructor and utils/helper methods here.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import date

from apps.finances.services.dashboard import DashboardService
from apps.finances.schemas.dashboard import DashboardPeriodFilter


class TestDashboardService_Constructor(TestCase):
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_constructor_sets_attributes_and_calls_projects_qs(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_qs = MagicMock()
    mock_projects_qs.return_value = mock_qs

    service = DashboardService(user, period, includes_open_projects=True)

    # Verify attributes
    self.assertEqual(service.user, user)
    self.assertEqual(service.period, period)
    self.assertEqual(service.includes_open_projects, True)
    self.assertEqual(service._qs, mock_qs)

    # Verify _projects_qs call
    mock_projects_qs.assert_called_once_with(user, period, True)


class TestDashboardService_DateRange(TestCase):
  def test_date_range_multiple_days(self):
    start = date(2026, 1, 1)
    end = date(2026, 1, 3)
    expected = [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]
    result = list(DashboardService._date_range(start, end))
    self.assertEqual(result, expected)

  def test_date_range_single_day(self):
    start = date(2026, 1, 1)
    end = date(2026, 1, 1)
    expected = [date(2026, 1, 1)]
    result = list(DashboardService._date_range(start, end))
    self.assertEqual(result, expected)

  def test_date_range_end_before_start(self):
    start = date(2026, 1, 3)
    end = date(2026, 1, 1)
    result = list(DashboardService._date_range(start, end))
    self.assertEqual(result, [])


class TestDashboardService_ProjectsQS(TestCase):
  @patch("apps.finances.services.dashboard.Project.objects.filter")
  def test_projects_qs_filtering_and_optimization(self, mock_filter):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 5, 1), end_date=date(2026, 5, 31)
    )

    mock_qs = MagicMock()
    mock_filter.return_value = mock_qs
    mock_qs.prefetch_related.return_value = mock_qs

    result = DashboardService._projects_qs(user, period, includes_open_projects=True)

    # Verify filtering
    mock_filter.assert_called_once_with(
      user=user, created_at__date__range=(period.start_date, period.end_date)
    )

    # Verify optimization (prefetching)
    mock_qs.prefetch_related.assert_called_once_with("task_set__movimentation")

    self.assertEqual(result, mock_qs)

  @patch("apps.finances.services.dashboard.Project.objects.filter")
  def test_projects_qs_excludes_open_projects_when_requested(self, mock_filter):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 5, 1), end_date=date(2026, 5, 31)
    )

    mock_qs = MagicMock()
    mock_filter.return_value = mock_qs
    mock_qs.prefetch_related.return_value = mock_qs
    mock_qs.exclude.return_value = mock_qs

    DashboardService._projects_qs(user, period, includes_open_projects=False)

    # Verify that exclude was called with OPEN_STATUS
    from apps.projects_and_clients.models import Project

    mock_qs.exclude.assert_called_once_with(status=Project.OPEN_STATUS)


class TestDashboardService_CalcProjectsBaseMetrics(TestCase):
  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_calc_projects_base_metrics_caching_and_return_value(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 1, 31)
    )

    # Mock project
    project = MagicMock()
    project.calc_project_total_gain.return_value = 100.0
    project.calc_project_total_cost.return_value = -40.0
    project.calc_project_profitability.return_value = 60.0
    project.calc_project_hour_profitability.return_value = 10.0
    tasks = ["task1"]
    project.task_set.all.return_value = tasks

    mock_projects_qs.return_value = [project]

    service = DashboardService(user, period, includes_open_projects=True)

    # First call
    result1 = service._calc_projects_base_metrics()

    expected = [
      {
        "project": project,
        "gain": 100.0,
        "cost": -40.0,
        "profit": 60.0,
        "hour_profit": 10.0,
      }
    ]

    self.assertEqual(result1, expected)
    self.assertEqual(service._projects_data, expected)

    # Verify model methods were called
    project.calc_project_total_gain.assert_called_once_with(tasks)

    # Reset mocks to check caching
    project.calc_project_total_gain.reset_mock()

    # Second call (should use cache)
    result2 = service._calc_projects_base_metrics()

    self.assertEqual(result2, expected)
    project.calc_project_total_gain.assert_not_called()
