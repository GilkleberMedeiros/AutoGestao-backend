from ninja import ModelSchema, Schema, Field
from pydantic import field_validator
from pydantic_core import PydanticCustomError

from apps.users.models import User
from apps.core.validation.br_phone import BRPhoneValidator, InvalidPhoneError


class LoginReq(Schema):
  email: str = Field(max_length=256, min_length=5)
  password: str = Field(max_length=128, min_length=8)

  @field_validator("email", mode="before")
  def normalize_email(cls, v):
    # Lower Case Email
    if isinstance(v, str):
      return v.lower()


class RegisterReq(ModelSchema):
  password: str = Field(max_length=128, min_length=8)

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

    if v == "":
      return None  # Convert empty string to None for optional phone field

    try:
      validator = BRPhoneValidator(v)
    except ValueError, InvalidPhoneError:
      raise PydanticCustomError("phone_invalid", "Invalid phone number")

    v = validator.get_formated(format="FULLPLAIN")
    return v


class UserMeRes(ModelSchema):
  class Meta:
    model = User
    fields = ["id", "name", "email", "phone"]


class AccessTokenRes(Schema):
  access: str
