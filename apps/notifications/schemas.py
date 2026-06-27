from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ninja import Schema, ModelSchema, Field
from pydantic import field_validator

from apps.notifications.models import Notification, NotificationRelation


class RelationSchema(ModelSchema):
  """Representation of a notification relation, used in request and response models."""

  class Meta:
    model = NotificationRelation
    fields = ["relation_type"]

  project_id: Optional[UUID] = None
  client_id: Optional[UUID] = None
  task_id: Optional[UUID] = None


class CreateNotificationReq(Schema):
  """Request model for creating a notification via NotificationService."""

  title: str
  deliver_at: datetime
  message: Optional[str] = None
  relation: Optional[RelationSchema] = None


class PartialUpdateNotificationReq(Schema):
  """Request model for partially updating a notification."""

  title: Optional[str] = None
  message: Optional[str] = None
  deliver_at: Optional[datetime] = None


class NotificationSchema(ModelSchema):
  """Response model for individual notification in sync response."""

  class Meta:
    model = Notification
    fields = [
      "id",
      "title",
      "message",
      "read",
      "deliver_at",
      "type",
      "extra_fields",
    ]

  relation: Optional[RelationSchema] = None


class SyncResponseSchema(Schema):
  """Response wrapper for notification synchronization endpoint."""

  notifications: list[NotificationSchema]


class SyncRequestSchema(Schema):
  """Request model for notification synchronization endpoint."""

  known_notification_ids: List[str] = Field(default_factory=list)

  @field_validator("known_notification_ids", mode="before")
  @classmethod
  def default_empty_list(cls, value):
    return value if value is not None else []

  @field_validator("known_notification_ids")
  @classmethod
  def validate_uuid_format(cls, value):
    for id_str in value:
      try:
        UUID(id_str)
      except ValueError, TypeError:
        raise ValueError(f"Invalid UUID in known_notification_ids: {id_str}")
    return value
