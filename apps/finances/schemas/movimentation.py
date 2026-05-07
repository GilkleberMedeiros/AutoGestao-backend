from uuid import UUID
from ninja import ModelSchema
from apps.finances.models import Movimentation


class MovimentationSchema(ModelSchema):
  class Meta:
    model = Movimentation
    fields = [
      "id",
      "amount",
      "balance",
      "reason",
      "movemented_at",
    ]

  mov_group_id: UUID


class CreateMovimentationReq(ModelSchema):
  class Meta:
    model = Movimentation
    fields = [
      "amount",
      "balance",
      "reason",
      "movemented_at",
    ]


class UpdateMovimentationReq(ModelSchema):
  class Meta:
    model = Movimentation
    fields = [
      "amount",
      "balance",
      "reason",
      "movemented_at",
    ]


class PartialUpdateMovimentationReq(ModelSchema):
  class Meta:
    model = Movimentation
    fields = [
      "amount",
      "balance",
      "reason",
      "movemented_at",
    ]
    fields_optional = "__all__"
