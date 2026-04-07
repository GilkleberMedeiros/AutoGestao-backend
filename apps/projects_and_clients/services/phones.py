from apps.projects_and_clients.models import Client, ClientPhone
from apps.users.models import User
from apps.core.exceptions import ResourceNotFoundError

from apps.core.validation.br_phone import BRPhoneValidator


class ClientPhoneService:
  """
  Service class for ClientPhone model.
  Handles individual CRUD operations for client phones.
  """

  @staticmethod
  def create(client_id: str, phone_data: dict, user: User) -> ClientPhone:
    """
    Adds a new phone to a client, verifying ownership.
    """
    client = Client.objects.filter(id=client_id, user=user).first()
    if not client:
      raise ResourceNotFoundError(f"Client with id {client_id} not found.")

    if "phone" in phone_data:
      phone_data["phone"] = BRPhoneValidator(phone_data["phone"]).get_formated(
        format="FULLPLAIN"
      )

    created_phone = ClientPhone.objects.create(client=client, **phone_data)
    created_phone.phone = BRPhoneValidator(created_phone.phone).get_formated(
      format="FULL"
    )
    return created_phone

  @staticmethod
  def list(client_id: str, user: User):
    """
    Lists all phones for a specific client.
    """
    client = Client.objects.filter(id=client_id, user=user).first()
    if not client:
      raise ResourceNotFoundError(f"Client with id {client_id} not found.")

    phones = client.phones.all().order_by("id")
    from apps.core.validation.br_phone import BRPhoneValidator

    for p in phones:
      p.phone = BRPhoneValidator(p.phone).get_formated(format="FULL")
    return list(phones)

  @staticmethod
  def update(phone_id: str, phone_data: dict, user: User) -> ClientPhone:
    """
    Updates a specific phone, verifying ownership via the client.
    """
    phone = ClientPhone.objects.filter(id=phone_id, client__user=user).first()
    if not phone:
      raise ResourceNotFoundError(f"Phone with id {phone_id} not found.")

    if "phone" in phone_data:
      from apps.core.validation.br_phone import BRPhoneValidator

      phone_data["phone"] = BRPhoneValidator(phone_data["phone"]).get_formated(
        format="FULLPLAIN"
      )

    for field, value in phone_data.items():
      setattr(phone, field, value)

    phone.save()

    phone.phone = BRPhoneValidator(phone.phone).get_formated(format="FULL")
    return phone

  @staticmethod
  def delete(phone_id: str, user: User) -> bool:
    """
    Deletes a specific phone.
    """
    phone = ClientPhone.objects.filter(id=phone_id, client__user=user).first()
    if not phone:
      raise ResourceNotFoundError(f"Phone with id {phone_id} not found.")

    phone.delete()
    return True
