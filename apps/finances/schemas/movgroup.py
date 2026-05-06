from ninja import ModelSchema
from apps.finances.models import MovGroup


class MovGroupSchema(ModelSchema):
  class Meta:
    model = MovGroup
    fields = [
      "id",
      "name",
      "description",
      "related_to",
      "relation",
      "created_at",
      "updated_at",
    ]


class CreateMovGroupReq(ModelSchema):
  class Meta:
    model = MovGroup
    fields = [
      "name",
      "description",
    ]


class UpdateMovGroupReq(ModelSchema):
  class Meta:
    model = MovGroup
    fields = [
      "name",
      "description",
    ]


class PartialUpdateMovGroupReq(ModelSchema):
  class Meta:
    model = MovGroup
    fields = [
      "name",
      "description",
    ]
    fields_optional = "__all__"
