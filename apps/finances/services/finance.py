from apps.finances.models import Finance, FinGroup
from apps.finances.services.fingroup import FinGroupService
from apps.finances.schemas.finance import (
  CreateFinanceReq,
  UpdateFinanceReq,
  PartialUpdateFinanceReq,
)
from apps.core.exceptions import ResourceNotFoundError


class FinanceService:
  @staticmethod
  def _get_fingroup(user, fingroup_id: str) -> FinGroup:
    return FinGroupService.get(user, fingroup_id)

  @staticmethod
  def create(user, fingroup_id: str, data: CreateFinanceReq) -> Finance:
    fingroup = FinanceService._get_fingroup(user, fingroup_id)
    finance = Finance.objects.create(
      fingroup=fingroup,
      amount=data.amount,
      balance=data.balance,
      reason=data.reason,
      movemented_at=data.movemented_at,
    )
    return finance

  @staticmethod
  def get(user, fingroup_id: str, finance_id: str) -> Finance:
    fingroup = FinanceService._get_fingroup(user, fingroup_id)
    finance = Finance.objects.filter(id=finance_id, fingroup=fingroup).first()
    if not finance:
      raise ResourceNotFoundError("Finance movement not found.")
    return finance

  @staticmethod
  def list(user, fingroup_id: str):
    fingroup = FinanceService._get_fingroup(user, fingroup_id)
    return Finance.objects.filter(fingroup=fingroup)

  @staticmethod
  def update(user, fingroup_id: str, finance_id: str, data: UpdateFinanceReq) -> Finance:
    finance = FinanceService.get(user, fingroup_id, finance_id)
    for attr, value in data.dict().items():
      setattr(finance, attr, value)
    finance.save()
    return finance

  @staticmethod
  def partial_update(user, fingroup_id: str, finance_id: str, data: PartialUpdateFinanceReq) -> Finance:
    finance = FinanceService.get(user, fingroup_id, finance_id)
    for attr, value in data.dict(exclude_unset=True).items():
      setattr(finance, attr, value)
    finance.save()
    return finance

  @staticmethod
  def delete(user, fingroup_id: str, finance_id: str):
    finance = FinanceService.get(user, fingroup_id, finance_id)
    finance.delete()
    return {"success": True}
