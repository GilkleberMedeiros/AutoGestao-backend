from typing import TypedDict


class NotificationRelationDTO(TypedDict):
  relation_type: str
  project_id: str | None
  client_id: str | None
  task_id: str | None


class NotificationDTO(TypedDict):
  id: str
  title: str
  message: str | None
  read: bool
  deliver_at: str
  type: str
  extra_fields: dict | None
  relation: NotificationRelationDTO | None


class CreateNotificationDTO(TypedDict):
  title: str
  message: str | None
  deliver_at: str
  type: str | None
  extra_fields: dict | None
  relation: NotificationRelationDTO | None


class PartialUpdateNotificationDTO(TypedDict):
  title: str | None
  message: str | None
  deliver_at: str | None
