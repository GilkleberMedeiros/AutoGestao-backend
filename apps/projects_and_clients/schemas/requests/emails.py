from ninja import ModelSchema
from pydantic import field_validator
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.projects_and_clients.models import ClientEmail


class ClientEmailSchema(ModelSchema):
  class Meta:
    model = ClientEmail
    fields = ["id", "email"]


class AddClientEmailReq(ModelSchema):
  class Meta:
    model = ClientEmail
    fields = ["email"]

  @field_validator("email", check_fields=False)
  @classmethod
  def validate_email_format(cls, v):
    try:
      validate_email(v)
    except DjangoValidationError:
      raise ValueError("Invalid email format")
    return v


class UpdateClientEmailReq(ModelSchema):
  class Meta:
    model = ClientEmail
    fields = ["email"]

  @field_validator("email", check_fields=False)
  @classmethod
  def validate_email_format(cls, v):
    try:
      validate_email(v)
    except DjangoValidationError:
      raise ValueError("Invalid email format")
    return v
