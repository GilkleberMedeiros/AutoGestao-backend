from apps.finances.models import Movimentation
from apps.finances.schemas.movimentation import (
  CreateMovimentationReq,
  UpdateMovimentationReq,
  PartialUpdateMovimentationReq,
)
from apps.core.exceptions import ResourceNotFoundError
from apps.finances.services.movgroup import MovGroupService


class MovimentationService:
  @staticmethod
  def create(user, mov_group_id: str, data: CreateMovimentationReq) -> Movimentation:
    mov_group = MovGroupService.get(user, mov_group_id)

    movimentation = Movimentation.objects.create(
      mov_group=mov_group,
      amount=abs(data.amount),
      balance=data.balance,
      reason=data.reason,
      movemented_at=data.movemented_at,
    )
    return movimentation

  @staticmethod
  def get(user, movimentation_id: str) -> Movimentation:
    movimentation = Movimentation.objects.filter(
      id=movimentation_id, mov_group__user=user
    ).first()
    if not movimentation:
      raise ResourceNotFoundError("Movimentation not found.")
    return movimentation

  @staticmethod
  def list(user, mov_group_id: str = None):
    queryset = Movimentation.objects.filter(mov_group__user=user)
    if mov_group_id:
      queryset = queryset.filter(mov_group_id=mov_group_id)
    return queryset

  @staticmethod
  def update(
    user, movimentation_id: str, data: UpdateMovimentationReq
  ) -> Movimentation:
    movimentation = MovimentationService.get(user, movimentation_id)

    for attr, value in data.model_dump(
      exclude={"mov_group_id"}, exclude_unset=True
    ).items():
      setattr(movimentation, attr, value)

    movimentation.save()
    return movimentation

  @staticmethod
  def partial_update(
    user, movimentation_id: str, data: PartialUpdateMovimentationReq
  ) -> Movimentation:
    movimentation = MovimentationService.get(user, movimentation_id)

    update_data = data.model_dump(exclude_unset=True)
    for attr, value in update_data.items():
      setattr(movimentation, attr, value)

    movimentation.save()
    return movimentation

  @staticmethod
  def delete(user, movimentation_id: str):
    movimentation = MovimentationService.get(user, movimentation_id)
    movimentation.delete()
    return {"success": True}
