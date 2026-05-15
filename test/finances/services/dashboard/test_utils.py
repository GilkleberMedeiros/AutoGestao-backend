"""
Test utils/helper method here.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import date

from apps.finances.services.dashboard import DashboardService
from apps.finances.schemas.dashboard import DashboardPeriodFilter


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
