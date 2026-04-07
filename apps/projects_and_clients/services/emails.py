from apps.projects_and_clients.models import Client, ClientEmail
from apps.users.models import User
from apps.core.exceptions import ResourceNotFoundError


class ClientEmailService:
  """
  Service class for ClientEmail model.
  Handles individual CRUD operations for client emails.
  """

  @staticmethod
  def create(client_id: str, email_data: dict, user: User) -> ClientEmail:
    """
    Adds a new email to a client, verifying ownership.
    """
    client = Client.objects.filter(id=client_id, user=user).first()
    if not client:
      raise ResourceNotFoundError(f"Client with id {client_id} not found.")

    return ClientEmail.objects.create(client=client, **email_data)

  @staticmethod
  def list(client_id: str, user: User):
    """
    Lists all emails for a specific client.
    """
    client = Client.objects.filter(id=client_id, user=user).first()
    if not client:
      raise ResourceNotFoundError(f"Client with id {client_id} not found.")

    return client.emails.all()

  @staticmethod
  def update(email_id: str, email_data: dict, user: User) -> ClientEmail:
    """
    Updates a specific email, verifying ownership via the client.
    """
    email = ClientEmail.objects.filter(id=email_id, client__user=user).first()
    if not email:
      raise ResourceNotFoundError(f"Email with id {email_id} not found.")

    for field, value in email_data.items():
      setattr(email, field, value)

    email.save()
    return email

  @staticmethod
  def delete(email_id: str, user: User) -> bool:
    """
    Deletes a specific email.
    """
    email = ClientEmail.objects.filter(id=email_id, client__user=user).first()
    if not email:
      raise ResourceNotFoundError(f"Email with id {email_id} not found.")

    email.delete()
    return True
