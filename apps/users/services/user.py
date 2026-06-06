from apps.users.models import User
from apps.users.schemas import UpdateUserReq, PartialUpdateUserReq
from apps.core.exceptions import ResourceAlreadyExistsError


class UserEmailAlreadyExistsError(ResourceAlreadyExistsError):
  pass


class UserPhoneAlreadyExistsError(ResourceAlreadyExistsError):
  pass


class UserService:
  """Service class for handling user-related operations (update, partial update, delete)."""

  @staticmethod
  def update_user(user: User, body: UpdateUserReq):
    UserService.check_unique_constraints(user, body)

    body_data = body.model_dump(exclude_unset=True, exclude_defaults=True)

    user.name = body.name
    if user.email != body.email:
      user.is_email_valid = False  # Set email as invalid if it was changed
    user.email = body.email

    # Check if phone was provided in the request
    if body_data.get("phone", "##$$%%&&") != "##$$%%&&":
      user.phone = body.phone

    user.save()

    return user

  @staticmethod
  def partial_update_user(user: User, body: PartialUpdateUserReq):
    UserService.check_unique_constraints(user, body)

    update_data = body.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] is not None:
      user.name = update_data["name"]
    if "email" in update_data and update_data["email"] is not None:
      if user.email != update_data["email"]:
        user.is_email_valid = False  # Set email as invalid if it was changed
      user.email = update_data["email"]
    if "phone" in update_data:
      user.phone = update_data["phone"]

    user.save()
    return user

  @staticmethod
  def check_unique_constraints(user: User, data: UpdateUserReq | PartialUpdateUserReq):
    # If already has a user with the same email or phone, raises an exception
    if User.objects.filter(email=data.email).exclude(id=user.id).count() > 0:
      raise UserEmailAlreadyExistsError("Provided email is already used.")
    if User.objects.filter(phone=data.phone).exclude(id=user.id).count() > 0:
      raise UserPhoneAlreadyExistsError("Provided phone is already used.")
