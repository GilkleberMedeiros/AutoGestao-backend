from ninja import Router

from apps.core.schemas.response import BaseAPIResponse
from apps.notifications.schemas.spending_limit import (
  SpendingLimitNotificationSchema,
  SpendingLimitNotificationCreateReq,
  UpdateSpendingLimitNotificationReq,
)
from apps.notifications.services.spending_limit import SpendingLimitNotificationService

router = Router()


@router.post("/", response=SpendingLimitNotificationSchema)
def create_spending_limit_notification(
  request, data: SpendingLimitNotificationCreateReq
):
  return SpendingLimitNotificationService.create(str(request.user.id), data)


@router.get(
  "/{notif_id}", response={200: SpendingLimitNotificationSchema, 404: BaseAPIResponse}
)
def get_spending_limit_notification(request, notif_id: str):
  notif = SpendingLimitNotificationService.get(str(request.user.id), notif_id)
  if not notif:
    return 404, {"details": "Spending limit rule not found", "success": False}
  return notif


@router.patch(
  "/{notif_id}", response={200: SpendingLimitNotificationSchema, 404: BaseAPIResponse}
)
def update_spending_limit_notification(
  request, notif_id: str, data: UpdateSpendingLimitNotificationReq
):
  notif = SpendingLimitNotificationService.update(str(request.user.id), notif_id, data)
  if not notif:
    return 404, {"details": "Spending limit rule not found", "success": False}
  return notif


@router.delete("/{notif_id}", response={200: BaseAPIResponse, 404: BaseAPIResponse})
def delete_spending_limit_notification(request, notif_id: str):
  """
  Deletes a spending limit notification. Fails silently if notification doesn't exist.
  """
  SpendingLimitNotificationService.delete(str(request.user.id), notif_id)
  return {"details": "Spending limit rule deleted successfully", "success": True}
