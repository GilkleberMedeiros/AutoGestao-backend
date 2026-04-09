from ninja import Router

from apps.core.schemas.response import BaseAPIResponse, PaginatedAPIResponse
from apps.core.exceptions import ResourceNotFoundError
from apps.core.utils.paginate import paginate_route
from apps.finances.schemas.finance import (
  FinanceSchema,
  CreateFinanceReq,
  UpdateFinanceReq,
  PartialUpdateFinanceReq,
)
from apps.finances.services.finance import FinanceService

router = Router()


@router.post(
  "/{fingroup_id}/finances",
  response={201: FinanceSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def create_finance(request, fingroup_id: str, data: CreateFinanceReq):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    finance = FinanceService.create(request.user, fingroup_id, data)
  except ResourceNotFoundError:
    return 404, {"details": "Financial group not found.", "success": False}

  return 201, finance


@router.get(
  "/{fingroup_id}/finances",
  response={200: PaginatedAPIResponse[FinanceSchema], 401: BaseAPIResponse, 404: BaseAPIResponse},
)
@paginate_route(per_page=250)
def list_finances(request, fingroup_id: str):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    finances = FinanceService.list(request.user, fingroup_id)
  except ResourceNotFoundError:
    return 404, {"details": "Financial group not found.", "success": False}

  return finances.order_by("-movemented_at")


@router.get(
  "/{fingroup_id}/finances/{finance_id}",
  response={200: FinanceSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def get_finance(request, fingroup_id: str, finance_id: str):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    finance = FinanceService.get(request.user, fingroup_id, finance_id)
  except ResourceNotFoundError:
    return 404, {"details": "Finance movement not found.", "success": False}

  return 200, finance


@router.put(
  "/{fingroup_id}/finances/{finance_id}",
  response={200: FinanceSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def update_finance(request, fingroup_id: str, finance_id: str, data: UpdateFinanceReq):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = FinanceService.update(request.user, fingroup_id, finance_id, data)
  except ResourceNotFoundError:
    return 404, {"details": "Finance movement not found.", "success": False}

  return 200, updated


@router.patch(
  "/{fingroup_id}/finances/{finance_id}",
  response={200: FinanceSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def partial_update_finance(request, fingroup_id: str, finance_id: str, data: PartialUpdateFinanceReq):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = FinanceService.partial_update(request.user, fingroup_id, finance_id, data)
  except ResourceNotFoundError:
    return 404, {"details": "Finance movement not found.", "success": False}

  return 200, updated


@router.delete(
  "/{fingroup_id}/finances/{finance_id}",
  response={200: BaseAPIResponse, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def delete_finance(request, fingroup_id: str, finance_id: str):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    FinanceService.delete(request.user, fingroup_id, finance_id)
  except ResourceNotFoundError:
    return 404, {"details": "Finance movement not found.", "success": False}

  return 200, {"details": "Finance movement deleted.", "success": True}
