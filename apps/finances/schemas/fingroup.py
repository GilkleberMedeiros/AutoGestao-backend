from typing import Optional
from uuid import UUID

from ninja import ModelSchema

from apps.finances.models import FinGroup


class FinGroupSchema(ModelSchema):
  class Meta:
    model = FinGroup
    fields = [
      "id",
      "name",
      "related_to",
      "relation",
      "created_at",
      "updated_at",
    ]

  user_id: UUID


class CreateFinGroupReq(ModelSchema):
  class Meta:
    model = FinGroup
    fields = [
      "name",
      "related_to",
      "relation",
    ]

  related_to: Optional[str] = None
  relation: Optional[str] = "PERSONAL"


class UpdateFinGroupReq(ModelSchema):
  class Meta:
    model = FinGroup
    fields = [
      "name",
      "related_to",
      "relation",
    ]

  related_to: Optional[str] = None
  relation: Optional[str] = "PERSONAL"


class PartialUpdateFinGroupReq(ModelSchema):
  class Meta:
    model = FinGroup
    fields = [
      "name",
      "related_to",
      "relation",
    ]
    fields_optional = "__all__"
