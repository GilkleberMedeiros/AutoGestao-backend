from typing import List
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from apps.core.exceptions import BusinessRuleError, ResourceNotFoundError
from apps.notifications.models import Notification, NotificationRelation
from apps.notifications.services.dtos import (
  NotificationRelationDTO,
  CreateNotificationDTO,
  PartialUpdateNotificationDTO,
)
from apps.projects_and_clients.models import Client, Project, Task
from apps.users.models import User

_VALID_NOTIFICATION_TYPES = {
  choice[0] for choice in Notification.NOTIFICATION_TYPE_CHOICES
}
_VALID_RELATION_TYPES = {
  choice[0] for choice in NotificationRelation.RELATION_TYPE_CHOICES
}
_TYPES_REQUIRING_RELATION = {
  Notification.NotificationType.ASSOCIATED,
  Notification.NotificationType.DEADLINE,
}


class NotificationService:
  """
  Service class for Notification operations.
  """

  SYNC_MAX_KNOWN_IDS = 10_000

  @staticmethod
  def _validate_and_resolve_relation(
    user: User, relation: NotificationRelationDTO
  ) -> dict:
    if relation["relation_type"] not in _VALID_RELATION_TYPES:
      raise BusinessRuleError("Invalid relation type.")

    relation_type = relation["relation_type"]
    resolved_rel = {
      "relation_type": relation_type,
      "project": None,
      "client": None,
      "task": None,
    }

    REL_TYPE_ID_MAP = {
      NotificationRelation.RelationType.PROJECT: {
        "id_field": "project_id",
        "model": Project,
      },
      NotificationRelation.RelationType.CLIENT: {
        "id_field": "client_id",
        "model": Client,
      },
      NotificationRelation.RelationType.TASK: {"id_field": "task_id", "model": Task},
    }

    related_map = REL_TYPE_ID_MAP[relation_type]
    id_field = related_map["id_field"]
    model = related_map["model"]

    related_id = relation.get(id_field, None)
    if related_id is None:
      raise BusinessRuleError(f"relation_type {relation_type} requires {id_field}.")
    related_instance = model.objects.filter(id=related_id, user=user).first()
    related_name = model.__name__.lower()
    if not related_instance:
      raise ResourceNotFoundError(f"Related {related_name} not found.")
    resolved_rel[related_name] = related_instance

    return resolved_rel

  @staticmethod
  def _create_relation(
    notification: Notification, relation: NotificationRelationDTO, user: User
  ) -> None:
    resolved = NotificationService._validate_and_resolve_relation(user, relation)
    NotificationRelation.objects.create(notification=notification, **resolved)

  @staticmethod
  @transaction.atomic
  def create(user: User, data: CreateNotificationDTO) -> Notification:
    notif_types = Notification.NotificationType
    relation = data.pop("relation", None)

    if not data.get("type", None):
      data["type"] = notif_types.SIMPLE if not relation else notif_types.ASSOCIATED

    if data["type"] not in _VALID_NOTIFICATION_TYPES:
      raise BusinessRuleError("Invalid notification type.")

    if data["type"] in _TYPES_REQUIRING_RELATION and not relation:
      raise BusinessRuleError("Notification type requires relation details.")

    notification = Notification.objects.create(
      user=user,
      title=data["title"],
      message=data.get("message", None),
      read=False,
      deliver_at=data["deliver_at"],
      type=data["type"],
      extra_fields=data.get("extra_fields", None),
    )

    if relation:
      NotificationService._create_relation(notification, relation, user)

    return Notification.objects.prefetch_related("notificationrelation_set").get(
      pk=notification.pk
    )

  @staticmethod
  def get(user: User, notification_id: str) -> Notification:
    notification = Notification.objects.filter(id=notification_id, user=user).first()
    if not notification:
      raise ResourceNotFoundError("Notification not found.")
    return notification

  @staticmethod
  @transaction.atomic
  def partial_update(
    user: User, notification_id: str, data: PartialUpdateNotificationDTO
  ) -> Notification:
    notification = NotificationService.get(user, notification_id)
    update_data = data

    # Clean data from fields that shouldn't be updated
    update_data.pop("type", None)
    update_data.pop("read", None)
    update_data.pop("relation", None)
    update_data.pop("extraa_fields", None)

    if not update_data:
      return notification

    for field, value in update_data.items():
      setattr(notification, field, value)

    if update_data:
      notification.save()

    notification.refresh_from_db()
    return notification

  @staticmethod
  def delete(user: User, notification_id: str) -> dict:
    notification = NotificationService.get(user, notification_id)
    notification.delete()
    return {"success": True}

  @staticmethod
  def read(user: User, notification_id: str) -> Notification:
    notification = NotificationService.get(user, notification_id)
    notification.read = True
    notification.save()

    notification.refresh_from_db()
    return notification

  @staticmethod
  def sync(user: User, known_ids: List[UUID] = []) -> QuerySet:
    """
    Synchronize notifications for a client by filtering out already-known IDs.
    """
    if len(known_ids) > NotificationService.SYNC_MAX_KNOWN_IDS:
      raise ValueError(
        f"known_notification_ids size exceeds maximum ({NotificationService.SYNC_MAX_KNOWN_IDS})"
      )

    queryset = Notification.objects.filter(user=user)

    if known_ids:
      queryset = queryset.exclude(id__in=known_ids)

    queryset = queryset.prefetch_related("notificationrelation_set").order_by(
      "-deliver_at", "id"
    )

    return queryset
