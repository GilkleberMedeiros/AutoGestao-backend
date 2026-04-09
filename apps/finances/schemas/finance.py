from uuid import UUID

from ninja import ModelSchema

from apps.finances.models import Finance


class FinanceSchema(ModelSchema):
  class Meta:
    model = Finance
    fields = [
      "id",
      "amount",
      "balance",
      "reason",
      "movemented_at",
      "created_at",
      "updated_at",
    ]

  fingroup_id: UUID


class CreateFinanceReq(ModelSchema):
  class Meta:
    model = Finance
    fields = [
      "amount",
      "balance",
      "reason",
      "movemented_at",
    ]


class UpdateFinanceReq(ModelSchema):
  class Meta:
    model = Finance
    fields = [
      "amount",
      "balance",
      "reason",
      "movemented_at",
    ]


class PartialUpdateFinanceReq(ModelSchema):
  class Meta:
    model = Finance
    fields = [
      "amount",
      "balance",
      "reason",
      "movemented_at",
    ]
    fields_optional = "__all__"
