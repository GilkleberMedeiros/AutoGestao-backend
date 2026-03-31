from django.db import transaction
from apps.projects_and_clients.models import (
  Client,
  ClientPhone,
  ClientEmail,
  ClientAddress,
  ClientRating,
)
from apps.users.models import User
from apps.core.exceptions import ResourceNotFoundError


class ClientService:
  """
  Service class for Client model.
  This class handles the business logic for the Client model
  creation, repr, update, partial update and delete.
  """

  @staticmethod
  @transaction.atomic
  def create(data: dict, user: User = None) -> Client:
    """
    Create a new client. Uses transaction. Expects data to be a dictionary.
    Expects User reference to be passed as param or be within data.
    """

    # Extract related data
    emails = data.pop("emails", []) or []
    phones = data.pop("phones", []) or []
    address_data = data.pop("address", None)
    rating_data = data.pop("rating", None)

    # Ensure user is set (from argument or within data)
    user_obj = data.pop("user", None) or user

    # Create main client
    client = Client.objects.create(user=user_obj, **data)

    # Create emails
    if emails:
      ClientEmail.objects.bulk_create(
        [ClientEmail(client=client, email=e) for e in emails]
      )

    # Create phones
    if phones:
      ClientPhone.objects.bulk_create(
        [ClientPhone(client=client, phone=p) for p in phones]
      )

    # Create address
    if address_data:
      ClientAddress.objects.create(client=client, **address_data)

    # Create rating
    if rating_data:
      ClientRating.objects.create(client=client, **rating_data)

    return client

  @staticmethod
  def get(client_id: str, user: User = None) -> Client | None:
    """
    Retrieves a single client by ID.
    Optionally scopes to a specific user.
    """
    filters = {"id": client_id}
    if user:
      filters["user"] = user
    return Client.objects.filter(**filters).first()

  @staticmethod
  def list(user: User = None):
    """
    Lists clients. Optionally filters by user.
    """
    qs = Client.objects.all()
    if user:
      qs = qs.filter(user=user)
    return qs

  @staticmethod
  @transaction.atomic
  def update(client_id: str, data: dict, user: User = None) -> Client:
    """
    Fully updates a client, replacing nested collections entirely.
    """
    client = ClientService.get(client_id, user)

    if not client:
      raise ResourceNotFoundError("Client not found")

    # Extract nested collections
    emails = data.pop("emails", []) or []
    phones = data.pop("phones", []) or []
    address_data = data.pop("address", None)
    rating_data = data.pop("rating", None)

    # Update main client fields
    for field, value in data.items():
      setattr(client, field, value)
    client.save()

    # Recreate emails (Full update replaces them)
    ClientEmail.objects.filter(client=client).delete()
    if emails:
      ClientEmail.objects.bulk_create(
        [ClientEmail(client=client, email=e) for e in emails]
      )

    # Recreate phones
    ClientPhone.objects.filter(client=client).delete()
    if phones:
      ClientPhone.objects.bulk_create(
        [ClientPhone(client=client, phone=p) for p in phones]
      )

    # Update or create address
    if address_data is not None:
      ClientAddress.objects.update_or_create(client=client, defaults=address_data)
    else:
      ClientAddress.objects.filter(client=client).delete()

    # Update or create rating
    if rating_data is not None:
      ClientRating.objects.update_or_create(client=client, defaults=rating_data)
    else:
      ClientRating.objects.filter(client=client).delete()

    return client

  @staticmethod
  @transaction.atomic
  def partial_update(client_id: str, data: dict, user: User = None) -> Client:
    """
    Partially updates a client. Only modifies provided fields.
    """
    client = ClientService.get(client_id, user)

    if not client:
      raise ResourceNotFoundError("Client not found")

    if "emails" in data:
      emails = data.pop("emails")
      ClientEmail.objects.filter(client=client).delete()
      if emails:
        ClientEmail.objects.bulk_create(
          [ClientEmail(client=client, email=e) for e in emails]
        )

    if "phones" in data:
      phones = data.pop("phones")
      ClientPhone.objects.filter(client=client).delete()
      if phones:
        ClientPhone.objects.bulk_create(
          [ClientPhone(client=client, phone=p) for p in phones]
        )

    if "address" in data:
      address_data = data.pop("address")
      if address_data is None:
        ClientAddress.objects.filter(client=client).delete()
      else:
        ClientAddress.objects.update_or_create(client=client, defaults=address_data)

    if "rating" in data:
      rating_data = data.pop("rating")
      if rating_data is None:
        ClientRating.objects.filter(client=client).delete()
      else:
        ClientRating.objects.update_or_create(client=client, defaults=rating_data)

    # Update main fields
    updated = False
    for field, value in data.items():
      setattr(client, field, value)
      updated = True

    if updated:
      client.save()

    return client

  @staticmethod
  def delete(client_id: str, user: User = None) -> bool:
    """
    Deletes a client.
    """
    client = ClientService.get(client_id, user)

    if not client:
      raise ResourceNotFoundError("Client not found")

    client.delete()
    return True
