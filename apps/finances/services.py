from apps.finances.models import MovGroup
from apps.finances.schemas import (
  CreateMovGroupReq,
  UpdateMovGroupReq,
  PartialUpdateMovGroupReq,
)
from apps.core.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError


class MovGroupNameAlreadyExistsError(ResourceAlreadyExistsError):
  pass


class MovGroupService:
  @staticmethod
  def validate_unique_constraints(
    user, data: CreateMovGroupReq | PartialUpdateMovGroupReq, exclude_id: str = None
  ):
    """
    Validates unique constraints for MovGroup model.

    Args:
      user: The user who owns the mov_group
      data: The data to validate
      exclude_id: The ID of the mov_group to exclude from the validation (useful for updates)
    """
    # Validates unique (per user) name constraint
    queryset = MovGroup.objects.filter(user=user, name=data.name)
    if exclude_id:
      queryset = queryset.exclude(id=exclude_id)
    if queryset.exists():
      raise MovGroupNameAlreadyExistsError(
        "A Movimentation Group with this name already exists."
      )

  @staticmethod
  def create(user, data: CreateMovGroupReq) -> MovGroup:
    MovGroupService.validate_unique_constraints(user, data)

    mov_group = MovGroup.objects.create(
      user=user,
      name=data.name,
      description=data.description,
    )
    return mov_group

  @staticmethod
  def get(user, mov_group_id: str) -> MovGroup:
    mov_group = MovGroup.objects.filter(id=mov_group_id, user=user).first()
    if not mov_group:
      raise ResourceNotFoundError("Movimentation Group not found.")
    return mov_group

  @staticmethod
  def list(user):
    return MovGroup.objects.filter(user=user)

  @staticmethod
  def update(user, mov_group_id: str, data: UpdateMovGroupReq) -> MovGroup:
    mov_group = MovGroupService.get(user, mov_group_id)

    if data.name != mov_group.name:
      MovGroupService.validate_unique_constraints(user, data, exclude_id=mov_group.id)

    for attr, value in data.model_dump().items():
      setattr(mov_group, attr, value)

    mov_group.save()
    return mov_group

  @staticmethod
  def partial_update(
    user, mov_group_id: str, data: PartialUpdateMovGroupReq
  ) -> MovGroup:
    mov_group = MovGroupService.get(user, mov_group_id)

    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != mov_group.name:
      MovGroupService.validate_unique_constraints(user, data, exclude_id=mov_group.id)

    for attr, value in update_data.items():
      setattr(mov_group, attr, value)

    mov_group.save()
    return mov_group

  @staticmethod
  def delete(user, mov_group_id: str):
    mov_group = MovGroupService.get(user, mov_group_id)
    mov_group.delete()
    return {"success": True}
