from uuid import UUID
from datetime import datetime
from typing import Optional, List
from ninja import Schema

from apps.notifications.schemas.base import (
  BaseNotificationSchema,
  BaseNotificationCreateReq,
  BaseUpdateNotificationReq,
)


class NotificationSchema(BaseNotificationSchema):
  deliver_at: datetime


class NotificationCreateReq(BaseNotificationCreateReq):
  deliver_at: datetime


class UpdateNotificationReq(BaseUpdateNotificationReq):
  deliver_at: Optional[datetime] = None


class SyncNotificationReq(Schema):
  already_synced_ids: List[UUID]


class SyncNotificationSchema(BaseNotificationSchema):
  deliver_at: Optional[datetime] = None
  threshold: Optional[float] = None
  period: Optional[str] = None
