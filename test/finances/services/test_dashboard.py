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

    result = DashboardService.fast_views(user, period)

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

    result = DashboardService.fast_views(user, period)

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

    result = DashboardService.fast_views(user, period)

    self.assertEqual(result["total_gains"], 0.0)
    self.assertEqual(result["total_costs"], 0.0)
    self.assertEqual(result["profitability"], 0.0)


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
  def test_projects_rankings_calls_projects_qs_when_none_provided(
    self, mock_projects_qs
  ):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    mock_projects_qs.return_value = []

    DashboardService.projects_rankings(user, period)

    mock_projects_qs.assert_called_once_with(user, period)

  def test_projects_rankings_uses_provided_projects_qs(self):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_qs = MagicMock()

    with patch(
      "apps.finances.services.dashboard.DashboardService._projects_qs"
    ) as mock_projects_qs:
      DashboardService.projects_rankings(user, period, projects_qs=mock_qs)
      mock_projects_qs.assert_not_called()

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_calculation_and_sorting(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )

    # Testing with 3 projects
    p1, p2, p3 = self._make_projects_mocks()
    mock_projects_qs.return_value = [p1, p2, p3]

    # rankings_count = 2 less comparisons
    result = DashboardService.projects_rankings(user, period, rankings_count=2)

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

    # Only 1 project requested for each rank
    result = DashboardService.projects_rankings(user, period, rankings_count=1)

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

    # Asking to return 5 projects per rank, but only 3 are available
    result = DashboardService.projects_rankings(user, period, rankings_count=5)

    # Only 3 projects for each rank
    self.assertEqual(len(result["total_gain"]), 3)
    self.assertEqual(len(result["total_cost"]), 3)
    self.assertEqual(len(result["profitability"]), 3)
    self.assertEqual(len(result["hour_profitability"]), 3)

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_projects_rankings_empty_projects(self, mock_projects_qs):
    user = MagicMock()
    period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
    )
    mock_projects_qs.return_value = []

    result = DashboardService.projects_rankings(user, period)

    self.assertEqual(result["total_gain"], [])
    self.assertEqual(result["total_cost"], [])
    self.assertEqual(result["profitability"], [])
    self.assertEqual(result["hour_profitability"], [])


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

    result = DashboardService._projects_qs(user, period)

    # Verify filtering
    mock_filter.assert_called_once_with(
      user=user, created_at__date__range=(period.start_date, period.end_date)
    )

    # Verify optimization (prefetching)
    mock_qs.prefetch_related.assert_called_once_with("task_set__movimentation")

    self.assertEqual(result, mock_qs)
