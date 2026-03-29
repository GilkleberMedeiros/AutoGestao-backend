from ninja import ModelSchema
from typing import Optional
from apps.projects_and_clients.models import (
  Client,
  ClientAddress,
  ClientRating,
)


class ClientRatingClientSchema(ModelSchema):
  class Meta:
    model = ClientRating
    fields = ["score", "comment"]


class ClientAddressClientSchema(ModelSchema):
  class Meta:
    model = ClientAddress
    fields = ["state", "city", "neighborhood", "street", "house_number", "complement"]


class ClientSchema(ModelSchema):
  class Meta:
    model = Client
    fields = ["id", "user", "name", "cpf"]

  emails: Optional[list[str]] = None
  phones: Optional[list[str]] = None
  address: Optional[ClientAddressClientSchema] = None
  rating: Optional[ClientRatingClientSchema] = None


class CreateClientReq(ModelSchema):
  class Meta:
    model = Client
    fields = ["name", "cpf"]

  emails: Optional[list[str]] = None
  phones: Optional[list[str]] = None
  address: Optional[ClientAddressClientSchema] = None
  rating: Optional[ClientRatingClientSchema] = None


class UpdateClientReq(ModelSchema):
  class Meta:
    model = Client
    fields = ["name", "cpf"]

  emails: Optional[list[str]] = None
  phones: Optional[list[str]] = None
  address: Optional[ClientAddressClientSchema] = None
  rating: Optional[ClientRatingClientSchema] = None


class PartialUpdateClientReq(ModelSchema):
  class Meta:
    model = Client
    fields = ["name", "cpf"]
    fields_optional = "__all__"

  emails: Optional[list[str]] = None
  phones: Optional[list[str]] = None
  address: Optional[ClientAddressClientSchema] = None
  rating: Optional[ClientRatingClientSchema] = None
