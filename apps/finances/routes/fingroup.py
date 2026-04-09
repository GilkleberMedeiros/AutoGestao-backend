from ninja import Router

from apps.core.schemas.response import BaseAPIResponse, PaginatedAPIResponse
from apps.core.exceptions import ResourceNotFoundError
from apps.core.utils.paginate import paginate_route
from apps.finances.schemas.fingroup import (
  FinGroupSchema,
  CreateFinGroupReq,
  UpdateFinGroupReq,
  PartialUpdateFinGroupReq,
)
from apps.finances.services.fingroup import FinGroupService

router = Router()


@router.post("", response={201: FinGroupSchema, 401: BaseAPIResponse})
def create_fingroup(request, data: CreateFinGroupReq):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  fingroup = FinGroupService.create(request.user, data)
  return 201, fingroup


@router.get("", response={200: PaginatedAPIResponse[FinGroupSchema], 401: BaseAPIResponse})
@paginate_route(per_page=250)
def list_fingroups(request):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  return FinGroupService.list(request.user).order_by("-created_at")


@router.get("/{fingroup_id}", response={200: FinGroupSchema, 401: BaseAPIResponse, 404: BaseAPIResponse})
def get_fingroup(request, fingroup_id: str):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    fingroup = FinGroupService.get(request.user, fingroup_id)
  except ResourceNotFoundError:
    return 404, {"details": "Financial group not found.", "success": False}

  return 200, fingroup


@router.put("/{fingroup_id}", response={200: FinGroupSchema, 401: BaseAPIResponse, 404: BaseAPIResponse})
def update_fingroup(request, fingroup_id: str, data: UpdateFinGroupReq):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = FinGroupService.update(request.user, fingroup_id, data)
  except ResourceNotFoundError:
    return 404, {"details": "Financial group not found.", "success": False}

  return 200, updated


@router.patch("/{fingroup_id}", response={200: FinGroupSchema, 401: BaseAPIResponse, 404: BaseAPIResponse})
def partial_update_fingroup(request, fingroup_id: str, data: PartialUpdateFinGroupReq):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = FinGroupService.partial_update(request.user, fingroup_id, data)
  except ResourceNotFoundError:
    return 404, {"details": "Financial group not found.", "success": False}

  return 200, updated


@router.delete("/{fingroup_id}", response={200: BaseAPIResponse, 401: BaseAPIResponse, 404: BaseAPIResponse})
def delete_fingroup(request, fingroup_id: str):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    FinGroupService.delete(request.user, fingroup_id)
  except ResourceNotFoundError:
    return 404, {"details": "Financial group not found.", "success": False}

  return 200, {"details": "Financial group deleted.", "success": True}
