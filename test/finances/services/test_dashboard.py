from django.test import TestCase
from django.utils import timezone
from datetime import date
from decimal import Decimal

from apps.users.models import User
from apps.projects_and_clients.models import Client, Project
from apps.finances.models import FinGroup, Finance
from apps.finances.services.dashboard import DashboardService
from apps.finances.schemas.dashboard import DashboardFiltersSchema


class TestDashboardService(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="dashuser",
      email="dash@test.com",
      password="pass",
      phone="5584000000000",
    )
    cls.client_obj = Client.objects.create(user=cls.user, name="C1", cpf="12345678901")
    
    # Project 1: Concluded, with project gain (actual_cost) and task gain
    cls.p1 = Project.objects.create(
      user=cls.user, client=cls.client_obj, name="Proj 1", status="CONCLUDED",
      estimated_deadline=date.today(), estimated_cost=100,
      actual_cost=Decimal("2000.00"), closed_at=timezone.now()
    )
    cls.g1 = FinGroup.objects.create(user=cls.user, name="G1", relation="PROJECT", related_to=cls.p1.id)
    Finance.objects.create(
      fingroup=cls.g1, amount=Decimal("1000.00"), balance="POSITIVE",
      reason="Gain 1", movemented_at=timezone.now()
    )

    # Project 3: Partially Concluded, with actual_cost but NO finances
    cls.p3 = Project.objects.create(
      user=cls.user, client=cls.client_obj, name="Proj 3", status="PARTIALLY_CONCLUDED",
      estimated_deadline=date.today(), estimated_cost=50,
      actual_cost=Decimal("500.00"), closed_at=timezone.now()
    )

    # Project 2: Cancelled (RN05: Should be ignored in totals/rankings)
    cls.p2 = Project.objects.create(
      user=cls.user, client=cls.client_obj, name="Proj 2", status="CANCELLED",
      estimated_deadline=date.today(), estimated_cost=100
    )
    cls.g2 = FinGroup.objects.create(user=cls.user, name="G2", relation="PROJECT", related_to=cls.p2.id)
    Finance.objects.create(
      fingroup=cls.g2, amount=Decimal("500.00"), balance="POSITIVE",
      reason="Gain 2", movemented_at=timezone.now()
    )

    # Personal Group (RN10)
    cls.gp = FinGroup.objects.create(user=cls.user, name="Personal", relation="PERSONAL")
    Finance.objects.create(
      fingroup=cls.gp, amount=Decimal("200.00"), balance="NEGATIVE",
      reason="Lunch", movemented_at=timezone.now()
    )

  @classmethod
  def tearDownClass(cls):
    cls.gp.delete()
    cls.p1.delete()
    cls.p2.delete()
    cls.p3.delete()
    cls.client_obj.delete()
    cls.user.delete()
    super().tearDownClass()

  def test_metric_summary_respects_rn05(self):
    # Should exclude P2 (Cancelled)
    filters = DashboardFiltersSchema(include_personal=True)
    metrics = DashboardService.get_metric_summary(self.user, filters)
    
    # Total Gain: P1_task(1000) + P1_actual(2000) + P3_actual(500) = 3500 (P2 ignored)
    self.assertEqual(metrics.total_gain, Decimal("3500.00"))
    # Total Expense: GP(200) = 200
    self.assertEqual(metrics.total_expense, Decimal("200.00"))
    self.assertEqual(metrics.total_profit, Decimal("3300.00"))

  def test_metric_summary_exclude_personal(self):
    filters = DashboardFiltersSchema(include_personal=False)
    metrics = DashboardService.get_metric_summary(self.user, filters)
    
    # Total Gain: P1_task(1000) + P1_actual(2000) + P3_actual(500) = 3500
    self.assertEqual(metrics.total_gain, Decimal("3500.00"))
    self.assertEqual(metrics.total_expense, Decimal("0.00"))

  def test_rankings_logic(self):
    filters = DashboardFiltersSchema()
    rankings = DashboardService.get_rankings(self.user, filters)
    
    # High gain should be P1 (3000 total) and P3 (500 total)
    self.assertEqual(len(rankings.highest_gain), 2)
    self.assertEqual(rankings.highest_gain[0].project_name, "Proj 1")
    # P2 should be missing as it is CANCELLED
    project_names = [item.project_name for item in rankings.highest_gain]
    self.assertNotIn("Proj 2", project_names)

  def test_income_composition(self):
    filters = DashboardFiltersSchema()
    comp = DashboardService.get_income_composition(self.user, filters)
    
    # P1 (3000) and P3 (500). Total 3500.
    self.assertEqual(len(comp), 2)

  def test_profitability_history(self):
    filters = DashboardFiltersSchema()
    history = DashboardService.get_profitability_history(self.user, filters)
    
    # Current month should have profit of 3300 (3500 - 200)
    self.assertEqual(len(history), 1)
    label = timezone.now().strftime("%b %Y")
    self.assertEqual(history[0].period_label, label)
    self.assertEqual(history[0].value, Decimal("3300.00"))
