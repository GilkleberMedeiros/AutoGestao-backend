from apps.finances.models import FinGroup
from apps.finances.schemas.fingroup import (
  CreateFinGroupReq,
  UpdateFinGroupReq,
  PartialUpdateFinGroupReq,
)
from apps.core.exceptions import ResourceNotFoundError


class FinGroupService:
  @staticmethod
  def create(user, data: CreateFinGroupReq) -> FinGroup:
    fingroup = FinGroup.objects.create(
      user=user,
      name=data.name,
      related_to=data.related_to,
      relation=data.relation,
    )
    return fingroup

  @staticmethod
  def get(user, fingroup_id: str) -> FinGroup:
    fingroup = FinGroup.objects.filter(id=fingroup_id, user=user).first()
    if not fingroup:
      raise ResourceNotFoundError("Financial group not found.")
    return fingroup

  @staticmethod
  def list(user):
    return FinGroup.objects.filter(user=user)

  @staticmethod
  def update(user, fingroup_id: str, data: UpdateFinGroupReq) -> FinGroup:
    fingroup = FinGroupService.get(user, fingroup_id)
    for attr, value in data.dict().items():
      setattr(fingroup, attr, value)
    fingroup.save()
    return fingroup

  @staticmethod
  def partial_update(user, fingroup_id: str, data: PartialUpdateFinGroupReq) -> FinGroup:
    fingroup = FinGroupService.get(user, fingroup_id)
    for attr, value in data.dict(exclude_unset=True).items():
      setattr(fingroup, attr, value)
    fingroup.save()
    return fingroup

  @staticmethod
  def delete(user, fingroup_id: str):
    fingroup = FinGroupService.get(user, fingroup_id)
    fingroup.delete()
    return {"success": True}
