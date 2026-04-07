from ninja import Router
from apps.projects_and_clients.schemas.requests.phones import (
  ClientPhoneSchema,
  AddClientPhoneReq,
  UpdateClientPhoneReq,
)
from apps.projects_and_clients.services.phones import ClientPhoneService
from apps.core.schemas.response import BaseAPIResponse, PaginatedAPIResponse
from apps.core.exceptions import ResourceNotFoundError
from apps.core.utils.paginate import paginate_route

router = Router()


@router.post(
  "/{client_id}/phones",
  response={201: ClientPhoneSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def create_phone(request, client_id: str, data: AddClientPhoneReq):
  """
  Add a new phone to a client.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    phone = ClientPhoneService.create(
      client_id, data.model_dump(exclude_unset=True), request.user
    )
    return 201, phone
  except ResourceNotFoundError as e:
    return 404, {"details": str(e), "success": False}


@router.get(
  "/{client_id}/phones",
  response={
    200: PaginatedAPIResponse[ClientPhoneSchema],
    401: BaseAPIResponse,
    404: BaseAPIResponse,
  },
)
@paginate_route(per_page=250)
def list_phones(request, client_id: str, page: int = 1):
  """
  List all phones for a specific client.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    phones = ClientPhoneService.list(client_id, request.user)
    return phones
  except ResourceNotFoundError as e:
    return 404, {"details": str(e), "success": False}


@router.put(
  "/phones/{phone_id}",
  response={200: ClientPhoneSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def update_phone(request, phone_id: str, data: UpdateClientPhoneReq):
  """
  Update a specific phone.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    phone = ClientPhoneService.update(
      phone_id, data.model_dump(exclude_unset=True), request.user
    )
    return 200, phone
  except ResourceNotFoundError as e:
    return 404, {"details": str(e), "success": False}


@router.delete(
  "/phones/{phone_id}",
  response={200: BaseAPIResponse, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def delete_phone(request, phone_id: str):
  """
  Delete a specific phone.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    ClientPhoneService.delete(phone_id, request.user)
    return 200, {"details": f"Phone with id {phone_id} deleted.", "success": True}
  except ResourceNotFoundError as e:
    return 404, {"details": str(e), "success": False}
