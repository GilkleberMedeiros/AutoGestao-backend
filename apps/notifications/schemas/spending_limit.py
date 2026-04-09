from typing import Optional

from apps.notifications.schemas.base import (
  BaseNotificationSchema,
  BaseNotificationCreateReq,
  BaseUpdateNotificationReq,
)


class SpendingLimitNotificationSchema(BaseNotificationSchema):
  threshold: float
  period: str


class SpendingLimitNotificationCreateReq(BaseNotificationCreateReq):
  threshold: float
  period: str


class UpdateSpendingLimitNotificationReq(BaseUpdateNotificationReq):
  threshold: Optional[float] = None
  period: Optional[str] = None
