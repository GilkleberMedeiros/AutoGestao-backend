from typing import TypedDict, NotRequired


class NotificationRelationDTO(TypedDict):
  relation_type: str
  project_id: NotRequired[str | None]
  client_id: NotRequired[str | None]
  task_id: NotRequired[str | None]


class NotificationDTO(TypedDict):
  id: str
  title: str
  message: NotRequired[str | None]
  read: bool
  deliver_at: str
  type: str
  extra_fields: NotRequired[dict | None]
  relation: NotRequired[NotificationRelationDTO | None]


class CreateNotificationDTO(TypedDict):
  title: str
  message: NotRequired[str | None]
  deliver_at: str
  type: NotRequired[str | None]
  extra_fields: NotRequired[dict | None]
  relation: NotRequired[NotificationRelationDTO | None]


class PartialUpdateNotificationDTO(TypedDict):
  title: NotRequired[str | None]
  message: NotRequired[str | None]
  deliver_at: NotRequired[str | None]
