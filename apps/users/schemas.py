from ninja import ModelSchema, Schema
from pydantic import field_validator
from pydantic_core import PydanticCustomError
from typing import Optional

from apps.users.models import User
from apps.core.validation.br_phone import BRPhoneValidator, InvalidPhoneError


class UpdateUserReq(ModelSchema):
  class Meta:
    model = User
    fields = ["name", "email", "phone"]

  @field_validator("email", check_fields=False)
  def validate_email(cls, v):
    # Normalize email to lowercase
    if isinstance(v, str):
      v = v.lower().strip()

    if v == "":
      raise PydanticCustomError("email_invalid", "Email cannot be empty")
    if " " in v:
      raise PydanticCustomError("email_invalid", "Email shouldn't have white spaces")
    return v

  @field_validator("name", check_fields=False)
  def validate_name(cls, v):
    # Normalize name - strip whitespace
    if isinstance(v, str):
      v = v.strip()

    if v == "":
      raise PydanticCustomError("name_invalid", "Name cannot be empty")
    return v

  @field_validator("phone", check_fields=False)
  def validate_phone(cls, v):
    if not v:
      return None

    if isinstance(v, str):
      v = v.strip()

    try:
      validator = BRPhoneValidator(v)
    except (ValueError, InvalidPhoneError):
      raise PydanticCustomError("phone_invalid", "Invalid phone number")

    v = validator.get_formated(format="FULLPLAIN")
    return v


class PartialUpdateUserReq(Schema):
  name: Optional[str] = None
  email: Optional[str] = None
  phone: Optional[str] = None

  @field_validator("email", check_fields=False)
  def validate_email(cls, v):
    if v is None:
      return v
    # Normalize email to lowercase
    if isinstance(v, str):
      v = v.lower().strip()

    if v == "":
      return None
    if " " in v:
      raise PydanticCustomError("email_invalid", "Email shouldn't have white spaces")
    return v

  @field_validator("name", check_fields=False)
  def validate_name(cls, v):
    if v is None:
      return v
    # Normalize name - strip whitespace
    if isinstance(v, str):
      v = v.strip()

    if v == "":
      return None
    return v

  @field_validator("phone", check_fields=False)
  def validate_phone(cls, v):
    if not v:
      return None

    if isinstance(v, str):
      v = v.strip()

    if v == "":
      return None

    try:
      validator = BRPhoneValidator(v)
    except (ValueError, InvalidPhoneError):
      raise PydanticCustomError("phone_invalid", "Invalid phone number")

    v = validator.get_formated(format="FULLPLAIN")
    return v
