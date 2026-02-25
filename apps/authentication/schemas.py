from ninja import ModelSchema, Schema, Field

from apps.users.models import User


class LoginReq(Schema):
  email: str = Field(max_length=256, min_length=5)
  password: str = Field(max_length=128, min_length=8)

  class Meta:
    model = User
    fields = ["email", "password"]


class RegisterReq(ModelSchema):
  password: str = Field(max_length=128, min_length=8)

  class Meta:
    model = User
    fields = ["name", "email", "password", "phone"]


class UserMeRes(ModelSchema):
  class Meta:
    model = User
    fields = ["id", "name", "email", "phone"]


class AccessTokenRes(Schema):
  access: str
