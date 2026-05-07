from ninja import Router

from apps.core.exceptions import ResourceNotFoundError
from apps.core.schemas.response import BaseAPIResponse, PaginatedAPIResponse
from apps.core.utils.paginate import paginate_route
from apps.finances.schemas.movgroup import (
  MovGroupSchema,
  CreateMovGroupReq,
  UpdateMovGroupReq,
  PartialUpdateMovGroupReq,
)
from apps.finances.services.movgroup import (
  MovGroupService,
  MovGroupNameAlreadyExistsError,
)

router = Router()


@router.post(
  "", response={201: MovGroupSchema, 400: BaseAPIResponse, 401: BaseAPIResponse}
)
def create_mov_group(request, data: CreateMovGroupReq):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    created = MovGroupService.create(request.user, data)
  except MovGroupNameAlreadyExistsError:
    return 400, {
      "details": (
        "Already exists a Movimentation Group with the given "
        "name for authenticated user."
      ),
      "success": False,
    }

  return 201, created


@router.get(
  "", response={200: PaginatedAPIResponse[MovGroupSchema], 401: BaseAPIResponse}
)
@paginate_route
def list_mov_groups(request):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  groups = MovGroupService.list(request.user)
  return groups.order_by("-created_at")


@router.get(
  "/{mov_group_id}",
  response={200: MovGroupSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def get_mov_group(request, mov_group_id: str):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    group = MovGroupService.get(request.user, mov_group_id)
  except ResourceNotFoundError:
    return 404, {
      "details": f"Movimentation Group with id {mov_group_id} not found.",
      "success": False,
    }

  return 200, group


@router.put(
  "/{mov_group_id}",
  response={
    200: MovGroupSchema,
    400: BaseAPIResponse,
    401: BaseAPIResponse,
    404: BaseAPIResponse,
  },
)
def update_mov_group(request, mov_group_id: str, data: UpdateMovGroupReq):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = MovGroupService.update(request.user, mov_group_id, data)
  except ResourceNotFoundError:
    return 404, {
      "details": f"Movimentation Group with id {mov_group_id} not found.",
      "success": False,
    }
  except MovGroupNameAlreadyExistsError:
    return 400, {
      "details": (
        "Already exists a Movimentation Group with the given "
        "name for authenticated user."
      ),
      "success": False,
    }

  return 200, updated


@router.patch(
  "/{mov_group_id}",
  response={
    200: MovGroupSchema,
    400: BaseAPIResponse,
    401: BaseAPIResponse,
    404: BaseAPIResponse,
  },
)
def partial_update_mov_group(
  request, mov_group_id: str, data: PartialUpdateMovGroupReq
):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = MovGroupService.partial_update(request.user, mov_group_id, data)
  except ResourceNotFoundError:
    return 404, {
      "details": f"Movimentation Group with id {mov_group_id} not found.",
      "success": False,
    }
  except MovGroupNameAlreadyExistsError:
    return 400, {
      "details": (
        "Already exists a Movimentation Group with the given "
        "name for authenticated user."
      ),
      "success": False,
    }

  return 200, updated


@router.delete(
  "/{mov_group_id}",
  response={200: BaseAPIResponse, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def delete_mov_group(request, mov_group_id: str):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    MovGroupService.delete(request.user, mov_group_id)
  except ResourceNotFoundError:
    return 404, {
      "details": f"Movimentation Group with id {mov_group_id} not found.",
      "success": False,
    }

  return 200, {
    "details": f"Movimentation Group with id {mov_group_id} deleted.",
    "success": True,
  }
