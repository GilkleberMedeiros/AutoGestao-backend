from typing import List
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from apps.core.exceptions import BusinessRuleError, ResourceNotFoundError
from apps.notifications.models import Notification, NotificationRelation
from apps.notifications.schemas import (
  CreateNotificationReq,
  PartialUpdateNotificationReq,
  RelationInputSchema,
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
  def _validate_notification_type(notification_type: str) -> None:
    if notification_type not in _VALID_NOTIFICATION_TYPES:
      raise BusinessRuleError("Invalid notification type.")

  @staticmethod
  def _validate_and_resolve_relation(
    user: User, relation: RelationInputSchema
  ) -> dict:
    if relation.relation_type not in _VALID_RELATION_TYPES:
      raise BusinessRuleError("Invalid relation type.")

    relation_type = relation.relation_type
    project = None
    client = None
    task = None

    if relation_type == NotificationRelation.RelationType.PROJECT:
      if not relation.project_id:
        raise BusinessRuleError("relation_type PROJECT requires project_id.")
      project = Project.objects.filter(id=relation.project_id, user=user).first()
      if not project:
        raise ResourceNotFoundError("Related project not found.")
    elif relation_type == NotificationRelation.RelationType.CLIENT:
      if not relation.client_id:
        raise BusinessRuleError("relation_type CLIENT requires client_id.")
      client = Client.objects.filter(id=relation.client_id, user=user).first()
      if not client:
        raise ResourceNotFoundError("Related client not found.")
    elif relation_type == NotificationRelation.RelationType.TASK:
      if not relation.task_id:
        raise BusinessRuleError("relation_type TASK requires task_id.")
      task = Task.objects.filter(id=relation.task_id, project__user=user).first()
      if not task:
        raise ResourceNotFoundError("Related task not found.")

    return {
      "relation_type": relation_type,
      "project": project,
      "client": client,
      "task": task,
    }

  @staticmethod
  def _create_relation(
    notification: Notification, relation: RelationInputSchema, user: User
  ) -> None:
    resolved = NotificationService._validate_and_resolve_relation(user, relation)
    NotificationRelation.objects.create(notification=notification, **resolved)

  @staticmethod
  def _update_relation(
    notification: Notification, relation: RelationInputSchema, user: User
  ) -> None:
    resolved = NotificationService._validate_and_resolve_relation(user, relation)
    NotificationRelation.objects.update_or_create(
      notification=notification,
      defaults=resolved,
    )

  @staticmethod
  @transaction.atomic
  def create(user: User, data: CreateNotificationReq) -> Notification:
    NotificationService._validate_notification_type(data.type)

    if data.type in _TYPES_REQUIRING_RELATION and not data.relation:
      raise BusinessRuleError("Notification type requires relation details.")

    notification = Notification.objects.create(
      user=user,
      title=data.title,
      message=data.message,
      read=data.read,
      deliver_at=data.deliver_at,
      type=data.type,
      extra_fields=data.extra_fields,
    )

    if data.relation:
      NotificationService._create_relation(notification, data.relation, user)

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
  def list(user: User) -> QuerySet:
    return (
      Notification.objects.filter(user=user)
      .prefetch_related("notificationrelation_set")
      .order_by("-deliver_at", "id")
    )

  @staticmethod
  @transaction.atomic
  def partial_update(
    user: User, notification_id: str, data: PartialUpdateNotificationReq
  ) -> Notification:
    notification = NotificationService.get(user, notification_id)
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
      return notification

    relation_provided = "relation" in update_data
    update_data.pop("relation", None)

    if "type" in update_data:
      NotificationService._validate_notification_type(update_data["type"])

    for field, value in update_data.items():
      setattr(notification, field, value)

    if update_data:
      notification.save()

    if relation_provided:
      if data.relation is None:
        notification.notificationrelation_set.all().delete()
      else:
        NotificationService._update_relation(notification, data.relation, user)

    notification.refresh_from_db()
    return notification

  @staticmethod
  def delete(user: User, notification_id: str) -> dict:
    notification = NotificationService.get(user, notification_id)
    notification.delete()
    return {"success": True}

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
