from ninja import Router, Path

from apps.core.exceptions import ResourceNotFoundError
from apps.core.schemas.response import BaseAPIResponse, PaginatedAPIResponse
from apps.core.utils.paginate import paginate_route
from apps.finances.schemas.movimentation import (
  MovimentationSchema,
  CreateMovimentationReq,
  UpdateMovimentationReq,
  PartialUpdateMovimentationReq,
)
from apps.finances.services.movimentation import MovimentationService

router = Router()


@router.post(
  "",
  response={201: MovimentationSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def create_movimentation(
  request, movgroup_id: str = Path(...), data: CreateMovimentationReq = None
):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    created = MovimentationService.create(request.user, movgroup_id, data)
  except ResourceNotFoundError:
    return 404, {
      "details": f"Movimentation Group with id {movgroup_id} not found.",
      "success": False,
    }

  return 201, created


@router.get(
  "", response={200: PaginatedAPIResponse[MovimentationSchema], 401: BaseAPIResponse}
)
@paginate_route
def list_movimentations(request, movgroup_id: str = Path(...)):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  movimentations = MovimentationService.list(request.user, movgroup_id)
  return movimentations.order_by("-movemented_at")


@router.get(
  "/{movimentation_id}",
  response={200: MovimentationSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def get_movimentation(
  request, movgroup_id: str = Path(...), movimentation_id: str = Path(...)
):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    movimentation = MovimentationService.get(request.user, movimentation_id)
  except ResourceNotFoundError:
    return 404, {
      "details": f"Movimentation with id {movimentation_id} not found.",
      "success": False,
    }

  return 200, movimentation


@router.put(
  "/{movimentation_id}",
  response={
    200: MovimentationSchema,
    401: BaseAPIResponse,
    404: BaseAPIResponse,
  },
)
def update_movimentation(
  request,
  movgroup_id: str = Path(...),
  movimentation_id: str = Path(...),
  data: UpdateMovimentationReq = None,
):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = MovimentationService.update(request.user, movimentation_id, data)
  except ResourceNotFoundError:
    return 404, {
      "details": f"Movimentation with id {movimentation_id} not found.",
      "success": False,
    }

  return 200, updated


@router.patch(
  "/{movimentation_id}",
  response={
    200: MovimentationSchema,
    401: BaseAPIResponse,
    404: BaseAPIResponse,
  },
)
def partial_update_movimentation(
  request,
  movgroup_id: str = Path(...),
  movimentation_id: str = Path(...),
  data: PartialUpdateMovimentationReq = None,
):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = MovimentationService.partial_update(request.user, movimentation_id, data)
  except ResourceNotFoundError:
    return 404, {
      "details": f"Movimentation with id {movimentation_id} not found.",
      "success": False,
    }

  return 200, updated


@router.delete(
  "/{movimentation_id}",
  response={200: BaseAPIResponse, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def delete_movimentation(
  request,
  movgroup_id: str = Path(...),
  movimentation_id: str = Path(...),
):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    MovimentationService.delete(request.user, movimentation_id)
  except ResourceNotFoundError:
    return 404, {
      "details": f"Movimentation with id {movimentation_id} not found.",
      "success": False,
    }

  return 200, {
    "details": f"Movimentation with id {movimentation_id} deleted.",
    "success": True,
  }
