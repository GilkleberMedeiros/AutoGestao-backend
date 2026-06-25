from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ninja import Schema, ModelSchema, Field
from pydantic import field_validator

from apps.notifications.models import Notification


class RelationSchema(Schema):
  """Represents optional domain entity association for a notification."""

  relation_type: Optional[str] = None
  project_id: Optional[UUID] = None
  client_id: Optional[UUID] = None
  task_id: Optional[UUID] = None


class RelationInputSchema(Schema):
  """Input payload for notification entity association on create/update."""

  relation_type: str
  project_id: Optional[UUID] = None
  client_id: Optional[UUID] = None
  task_id: Optional[UUID] = None


class CreateNotificationReq(Schema):
  """Request model for creating a notification via NotificationService."""

  title: str
  deliver_at: datetime
  type: str
  message: Optional[str] = None
  read: bool = False
  extra_fields: Optional[dict] = None
  relation: Optional[RelationInputSchema] = None


class PartialUpdateNotificationReq(Schema):
  """Request model for partially updating a notification."""

  title: Optional[str] = None
  message: Optional[str] = None
  read: Optional[bool] = None
  deliver_at: Optional[datetime] = None
  type: Optional[str] = None
  extra_fields: Optional[dict] = None
  relation: Optional[RelationInputSchema] = None


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
      except (ValueError, TypeError):
        raise ValueError(f"Invalid UUID in known_notification_ids: {id_str}")
    return value
