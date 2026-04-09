from uuid import UUID
from ninja import Schema
from typing import Optional


class BaseNotificationSchema(Schema):
  id: UUID
  user_id: UUID
  title: str
  message: str
  type: str


class BaseNotificationCreateReq(Schema):
  title: str
  message: str


class BaseUpdateNotificationReq(Schema):
  title: Optional[str] = None
  message: Optional[str] = None
