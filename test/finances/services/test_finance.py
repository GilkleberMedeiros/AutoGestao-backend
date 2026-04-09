from django.test import TestCase
from django.utils import timezone
import uuid
from decimal import Decimal

from apps.users.models import User
from apps.finances.models import FinGroup, Finance
from apps.finances.services.finance import FinanceService
from apps.core.exceptions import ResourceNotFoundError
from apps.finances.schemas.finance import (
  CreateFinanceReq,
  UpdateFinanceReq,
  PartialUpdateFinanceReq,
)


class BaseFinanceTest(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="finuser",
      email="finuser@test.com",
      password="testpass",
      phone="5584000000000",
    )
    cls.other_user = User.objects.create_user(
      name="otherfinuser",
      email="otherfinuser@test.com",
      password="testpass",
      phone="5584000000001",
    )
    cls.fingroup = FinGroup.objects.create(
      user=cls.user, name="Project A", relation="PROJECT"
    )

  @classmethod
  def tearDownClass(cls):
    cls.fingroup.delete()
    cls.other_user.delete()
    cls.user.delete()
    super().tearDownClass()


class TestCreateFinance(BaseFinanceTest):
  def test_create_finance_success(self):
    now = timezone.now()
    data = CreateFinanceReq(
      amount=Decimal("150.00"),
      balance="POSITIVE",
      reason="Test Gain",
      movemented_at=now,
    )
    fin = FinanceService.create(self.user, str(self.fingroup.id), data)
    self.assertEqual(fin.amount, Decimal("150.00"))
    self.assertEqual(fin.balance, "POSITIVE")
    self.assertEqual(fin.reason, "Test Gain")
    self.assertEqual(fin.fingroup, self.fingroup)

  def test_create_finance_other_user_group_fails(self):
    data = CreateFinanceReq(
      amount=Decimal("10.00"),
      balance="NEGATIVE",
      reason="Error",
      movemented_at=timezone.now(),
    )
    with self.assertRaises(ResourceNotFoundError):
      FinanceService.create(self.other_user, str(self.fingroup.id), data)


class TestGetFinance(BaseFinanceTest):
  def test_get_success(self):
    fin = Finance.objects.create(
      fingroup=self.fingroup,
      amount=Decimal("50.00"),
      balance="NEGATIVE",
      reason="Lunch",
      movemented_at=timezone.now(),
    )
    result = FinanceService.get(self.user, str(self.fingroup.id), str(fin.id))
    self.assertEqual(result.id, fin.id)

  def test_get_not_found(self):
    with self.assertRaises(ResourceNotFoundError):
      FinanceService.get(self.user, str(self.fingroup.id), str(uuid.uuid4()))


class TestListFinance(BaseFinanceTest):
  def test_list_success(self):
    Finance.objects.create(
      fingroup=self.fingroup,
      amount=Decimal("10.00"),
      balance="POSITIVE",
      reason="R1",
      movemented_at=timezone.now(),
    )
    Finance.objects.create(
      fingroup=self.fingroup,
      amount=Decimal("20.00"),
      balance="NEGATIVE",
      reason="R2",
      movemented_at=timezone.now(),
    )
    items = FinanceService.list(self.user, str(self.fingroup.id))
    self.assertGreaterEqual(items.count(), 2)


class TestUpdateFinance(BaseFinanceTest):
  def test_update_success(self):
    fin = Finance.objects.create(
      fingroup=self.fingroup,
      amount=Decimal("10.00"),
      balance="POSITIVE",
      reason="Old",
      movemented_at=timezone.now(),
    )
    data = UpdateFinanceReq(
      amount=Decimal("20.00"),
      balance="POSITIVE",
      reason="New",
      movemented_at=timezone.now(),
    )
    updated = FinanceService.update(self.user, str(self.fingroup.id), str(fin.id), data)
    self.assertEqual(updated.reason, "New")
    self.assertEqual(updated.amount, Decimal("20.00"))


class TestDeleteFinance(BaseFinanceTest):
  def test_delete_success(self):
    fin = Finance.objects.create(
      fingroup=self.fingroup,
      amount=Decimal("10.00"),
      balance="POSITIVE",
      reason="Bye",
      movemented_at=timezone.now(),
    )
    FinanceService.delete(self.user, str(self.fingroup.id), str(fin.id))
    with self.assertRaises(ResourceNotFoundError):
      FinanceService.get(self.user, str(self.fingroup.id), str(fin.id))
