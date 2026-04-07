from ninja import Router
from apps.projects_and_clients.schemas.requests.emails import (
  ClientEmailSchema,
  AddClientEmailReq,
  UpdateClientEmailReq,
)
from apps.projects_and_clients.services.emails import ClientEmailService
from apps.core.schemas.response import BaseAPIResponse, PaginatedAPIResponse
from apps.core.exceptions import ResourceNotFoundError
from apps.core.utils.paginate import paginate_route

router = Router()


@router.post(
  "/{client_id}/emails",
  response={201: ClientEmailSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def create_email(request, client_id: str, data: AddClientEmailReq):
  """
  Add a new email to a client.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    email = ClientEmailService.create(
      client_id, data.model_dump(exclude_unset=True), request.user
    )
    return 201, email
  except ResourceNotFoundError as e:
    return 404, {"details": str(e), "success": False}


@router.get(
  "/{client_id}/emails",
  response={
    200: PaginatedAPIResponse[ClientEmailSchema],
    401: BaseAPIResponse,
    404: BaseAPIResponse,
  },
)
@paginate_route(per_page=250)
def list_emails(request, client_id: str, page: int = 1):
  """
  List all emails for a specific client.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    emails = ClientEmailService.list(client_id, request.user)
    return emails.order_by("id")
  except ResourceNotFoundError as e:
    return 404, {"details": str(e), "success": False}


@router.put(
  "/emails/{email_id}",
  response={200: ClientEmailSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def update_email(request, email_id: str, data: UpdateClientEmailReq):
  """
  Update a specific email.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    email = ClientEmailService.update(
      email_id, data.model_dump(exclude_unset=True), request.user
    )
    return 200, email
  except ResourceNotFoundError as e:
    return 404, {"details": str(e), "success": False}


@router.delete(
  "/emails/{email_id}",
  response={200: BaseAPIResponse, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def delete_email(request, email_id: str):
  """
  Delete a specific email.
  """
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    ClientEmailService.delete(email_id, request.user)
    return 200, {"details": f"Email with id {email_id} deleted.", "success": True}
  except ResourceNotFoundError as e:
    return 404, {"details": str(e), "success": False}
