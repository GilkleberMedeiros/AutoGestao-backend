from unittest import TestCase
from unittest.mock import MagicMock
from datetime import timedelta

from apps.projects_and_clients.models import Project


class TestProjectModelMethods(TestCase):
  def setUp(self):
    self.project = Project(labor_fee=100.00)

  def test_calc_project_total_gain(self):
    # Gain should be labor_fee (100) + positive task movimentations
    task1 = MagicMock()
    task1.movimentation.value = 50.0
    task2 = MagicMock()
    task2.movimentation.value = -30.0  # Negative, should be ignored
    task3 = MagicMock()
    task3.movimentation = None  # None, should be ignored

    tasks_qs = [task1, task2, task3]

    result = self.project.calc_project_total_gain(tasks_qs)
    # 100 (labor_fee) + 50 (task1) = 150.0
    self.assertEqual(result, 150.0)

  def test_calc_project_total_cost(self):
    # Cost should be sum of negative task movimentations
    task1 = MagicMock()
    task1.movimentation.value = 50.0  # Positive, should be ignored
    task2 = MagicMock()
    task2.movimentation.value = -30.0
    task3 = MagicMock()
    task3.movimentation.value = -20.0
    task4 = MagicMock()
    task4.movimentation = None  # None, should be ignored

    tasks_qs = [task1, task2, task3, task4]

    result = self.project.calc_project_total_cost(tasks_qs)
    # -30 + -20 = -50.0
    self.assertEqual(result, -50.0)

  def test_calc_project_profitability(self):
    # profitability = total_gain (incl. labor_fee) + total_cost
    task1 = MagicMock()
    task1.movimentation.value = 80.0
    task2 = MagicMock()
    task2.movimentation.value = -30.0

    tasks_qs = [task1, task2]

    result = self.project.calc_project_profitability(tasks_qs)
    # gain = 100 (labor) + 80 = 180
    # cost = -30
    # 180 + (-30) = 150.0
    self.assertEqual(result, 150.0)

  def test_calc_project_hour_profitability(self):
    self.project.spent_time = timedelta(hours=20)
    profitability = 300.0

    # 300 / 20 hours = 15.0
    result = self.project.calc_project_hour_profitability(profitability)
    self.assertEqual(result, 15.0)

  def test_calc_project_hour_profitability_with_none_spent_time(self):
    self.project.spent_time = None
    result = self.project.calc_project_hour_profitability(300.0)
    self.assertEqual(result, 0.0)

  def test_calc_project_hour_profitability_float_result(self):
    # Test that we get a float result, not floor division
    self.project.spent_time = timedelta(hours=1000)
    profitability = 150.0

    # 150 / 1000 = 0.15
    result = self.project.calc_project_hour_profitability(profitability)
    self.assertEqual(result, 0.15)
