from ninja import ModelSchema
from apps.projects_and_clients.models import ClientEmail


class ClientEmailSchema(ModelSchema):
  class Meta:
    model = ClientEmail
    fields = ["id", "email"]


class AddClientEmailReq(ModelSchema):
  class Meta:
    model = ClientEmail
    fields = ["email"]


class UpdateClientEmailReq(ModelSchema):
  class Meta:
    model = ClientEmail
    fields = ["email"]
