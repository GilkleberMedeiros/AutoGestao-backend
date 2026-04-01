from ninja import ModelSchema
from pydantic import field_validator

from typing import Optional

from apps.projects_and_clients.models import (
  Client,
  ClientEmail,
  ClientPhone,
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
    fields = ["id", "name", "cpf"]

  emails: Optional[list[str]] = None
  phones: Optional[list[str]] = None
  address: Optional[ClientAddressClientSchema] = None
  rating: Optional[ClientRatingClientSchema] = None

  @field_validator("emails", mode="before")
  @classmethod
  def parse_emails(cls, value):
    if value is None:
      return value

    # For querysets
    if hasattr(value, "all"):
      value = value.all()

    try:
      return [item.email if isinstance(item, ClientEmail) else item for item in value]
    except TypeError:
      return value

  @field_validator("phones", mode="before")
  @classmethod
  def parse_phones(cls, value):
    if value is None:
      return value

    if hasattr(value, "all"):
      value = value.all()

    try:
      return [item.phone if isinstance(item, ClientPhone) else item for item in value]
    except TypeError:
      return value


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
