from apps.users.models import User
from apps.users.schemas import UpdateUserReq, PartialUpdateUserReq


class UserService:
  """Service class for handling user-related operations (update, partial update, delete)."""

  @staticmethod
  def update_user(user: User, body: UpdateUserReq):
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
