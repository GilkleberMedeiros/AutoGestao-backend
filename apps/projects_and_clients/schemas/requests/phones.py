from ninja import ModelSchema
from pydantic import field_validator
from apps.projects_and_clients.models import ClientPhone
from apps.core.validation.br_phone import BRPhoneValidator, InvalidPhoneError


class ClientPhoneSchema(ModelSchema):
  class Meta:
    model = ClientPhone
    fields = ["id", "phone"]


class AddClientPhoneReq(ModelSchema):
  class Meta:
    model = ClientPhone
    fields = ["phone"]

  @field_validator("phone", check_fields=False)
  @classmethod
  def validate_phone_format(cls, v):
    try:
      BRPhoneValidator(v)
    except (ValueError, InvalidPhoneError):
      raise ValueError("Invalid phone format")
    return v


class UpdateClientPhoneReq(ModelSchema):
  class Meta:
    model = ClientPhone
    fields = ["phone"]

  @field_validator("phone", check_fields=False)
  @classmethod
  def validate_phone_format(cls, v):
    try:
      return BRPhoneValidator(v).get_formated(format="FULLPLAIN")
    except (ValueError, InvalidPhoneError):
      raise ValueError("Invalid phone format")
