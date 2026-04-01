"""
Routes for client manipulation.
"""

from ninja import Router

from apps.core.schemas.response import BaseAPIResponse
from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.schemas.requests.client import (
  ClientSchema,
  CreateClientReq,
  UpdateClientReq,
  PartialUpdateClientReq,
)
from apps.projects_and_clients.services.client import ClientService

router = Router()


@router.post("", response={201: ClientSchema, 401: BaseAPIResponse})
def create_client(request, data: CreateClientReq):
  """
  Create a new client.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  created = ClientService.create(
    data.model_dump(exclude_none=True, exclude_unset=True), request.user
  )

  return 201, created


@router.get("", response={200: list[ClientSchema], 401: BaseAPIResponse})
def list_clients(request):
  """
  List all clients for the authenticated user.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  clients = ClientService.list(request.user)

  return clients


@router.get(
  "/{client_id}",
  response={200: ClientSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def get_client(request, client_id: str):
  """
  Get a client by ID.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  client = ClientService.get(client_id, request.user)

  if not client:
    return 404, {"details": f"Client with id {client_id}, not found.", "success": False}

  return client


@router.put(
  "/{client_id}",
  response={200: ClientSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def update_client(request, client_id: str, data: UpdateClientReq):
  """
  Update a client. Caution: This method replaces the entire client, even
  those fields that were not provided will be replaced as None or deleted from the Model.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = ClientService.update(
      client_id, data.model_dump(exclude_none=True, exclude_unset=True), request.user
    )
  except ResourceNotFoundError:
    return 404, {"details": f"Client with id {client_id}, not found.", "success": False}

  return updated


@router.patch(
  "/{client_id}",
  response={200: ClientSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def partial_update_client(request, client_id: str, data: PartialUpdateClientReq):
  """
  Partially update a client. Caution: This method only updates the fields that are provided.
  If you provide a field as None, or other empty value ([], {}, "", etc...),
  the field will be updated to None or deleted from the Model.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = ClientService.partial_update(
      client_id, data.model_dump(exclude_unset=True), request.user
    )
  except ResourceNotFoundError:
    return 404, {"details": f"Client with id {client_id}, not found.", "success": False}

  return updated


@router.delete("/{client_id}", response={200: BaseAPIResponse, 401: BaseAPIResponse, 404: BaseAPIResponse})
def delete_client(request, client_id: str):
  """
  Delete a client.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    ClientService.delete(client_id, request.user)
  except ResourceNotFoundError:
    return 404, {"details": f"Client with id {client_id}, not found.", "success": False}

  return 200, {"details": f"Client with id {client_id}, deleted.", "success": True}
