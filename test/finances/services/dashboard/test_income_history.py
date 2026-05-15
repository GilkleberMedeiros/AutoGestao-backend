"""
.income_history method unit tests.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import date, datetime

from apps.finances.services.dashboard import DashboardService
from apps.finances.schemas.dashboard import DashboardPeriodFilter


class TestDashboardService_IncomeHistory(TestCase):
  def setUp(self):
    self.user = MagicMock()
    self.period = DashboardPeriodFilter(
      start_date=date(2026, 1, 1), end_date=date(2026, 1, 2)
    )

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  @patch("apps.finances.services.dashboard.Movimentation.objects.filter")
  def test_income_history_aggregations_and_exclusions(self, mock_mov_filter, mock_projects_qs):
    # p1: Closed within period (Jan 1)
    p1 = MagicMock(closed_at=datetime(2026, 1, 1), labor_fee=100.0)
    # t1: Movimentation within period (Jan 2)
    t1 = MagicMock()
    t1.movimentation.movemented_at = datetime(2026, 1, 2)
    t1.movimentation.value = 50.0
    p1.task_set.all.return_value = [t1]

    # p2: Closed OUTSIDE period (Jan 3)
    p2 = MagicMock(closed_at=datetime(2026, 1, 3), labor_fee=200.0)
    # t2: Movimentation OUTSIDE period (Jan 3)
    t2 = MagicMock()
    t2.movimentation.movemented_at = datetime(2026, 1, 3)
    t2.movimentation.value = 300.0
    p2.task_set.all.return_value = [t2]

    mock_projects_qs.return_value = [p1, p2]
    mock_mov_filter.return_value = []

    service = DashboardService(self.user, self.period, True)
    result = service.income_history(False)

    # Jan 1: 100.0 (p1 labor fee)
    # Jan 2: 50.0 (t1 movement)
    # p2 labor fee and t2 movement are ignored (> Jan 2)
    self.assertEqual(result, [
      {"date": "2026-01-01", "profit": 100.0},
      {"date": "2026-01-02", "profit": 50.0}
    ])

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  @patch("apps.finances.services.dashboard.Movimentation.objects.filter")
  def test_income_history_personal_finances_filter(self, mock_mov_filter, mock_projects_qs):
    mock_projects_qs.return_value = []
    mock_mov_filter.return_value = []

    service = DashboardService(self.user, self.period, True)
    service.income_history(True)

    mock_mov_filter.assert_called_once_with(
      mov_group__user=self.user,
      mov_group__relation="NORELATION",
      movemented_at__date__range=(self.period.start_date, self.period.end_date)
    )

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  @patch("apps.finances.services.dashboard.Movimentation.objects.filter")
  def test_income_history_excludes_personal_finances_when_false(self, mock_mov_filter, mock_projects_qs):
    mock_projects_qs.return_value = []
    service = DashboardService(self.user, self.period, True)
    service.income_history(False)
    mock_mov_filter.assert_not_called()

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  @patch("apps.finances.services.dashboard.Movimentation.objects.filter")
  def test_income_history_includes_personal_finances_when_true(self, mock_mov_filter, mock_projects_qs):
    mock_projects_qs.return_value = []
    # Movimentation on Jan 1 with value 50
    mov = MagicMock()
    mov.movemented_at = datetime(2026, 1, 1)
    mov.value = 50.0
    mock_mov_filter.return_value = [mov]

    service = DashboardService(self.user, self.period, True)
    result = service.income_history(True)

    # Jan 1 should have 50.0 from personal finance
    self.assertEqual(result[0], {"date": "2026-01-01", "profit": 50.0})
    self.assertEqual(result[1], {"date": "2026-01-02", "profit": 0.0})

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_income_history_sorting(self, mock_projects_qs):
    # Ensure even if generated out of order (though generator is sequential), 
    # the output is sorted.
    self.period.start_date = date(2026, 1, 1)
    self.period.end_date = date(2026, 1, 3)
    
    # We mock _date_range to yield dates out of order to test the sort
    with patch("apps.finances.services.dashboard.DashboardService._date_range") as mock_range:
      mock_range.return_value = [date(2026, 1, 3), date(2026, 1, 1), date(2026, 1, 2)]
      mock_projects_qs.return_value = []
      
      service = DashboardService(self.user, self.period, True)
      result = service.income_history(False)
      
      dates = [r["date"] for r in result]
      self.assertEqual(dates, ["2026-01-01", "2026-01-02", "2026-01-03"])

  @patch("apps.finances.services.dashboard.DashboardService._projects_qs")
  def test_income_history_empty_range(self, mock_projects_qs):
    self.period.start_date, self.period.end_date = date(2026, 1, 2), date(2026, 1, 1)
    mock_projects_qs.return_value = []
    
    service = DashboardService(self.user, self.period, True)
    self.assertEqual(service.income_history(False), [])
