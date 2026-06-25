from django.db import models

import uuid


class Notification(models.Model):
  class NotificationType:
    SIMPLE = "SIMPLE"  # Simple Generic Purpose Notification
    ASSOCIATED = "ASSOCIATED"  # Simple Notification associated with a specific entity (Project, Client, etc.)
    DEADLINE = "DEADLINE"  # Specific purpose notification for Project deadlines
    SPENT_LIMIT = "SPENT_LIMIT"  # Specific purpose notification for User personal finance spent limit

  NOTIFICATION_TYPE_CHOICES = [
    (NotificationType.SIMPLE, "Simple"),
    (NotificationType.ASSOCIATED, "Associated"),
    (NotificationType.DEADLINE, "Deadline"),
    (NotificationType.SPENT_LIMIT, "Spent Limit"),
  ]

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey("users.User", on_delete=models.CASCADE)
  title = models.CharField(max_length=255)
  message = models.TextField(null=True, blank=True)
  read = models.BooleanField(default=False)
  deliver_at = models.DateTimeField()
  type = models.CharField(
    max_length=50, default=NotificationType.SIMPLE, choices=NOTIFICATION_TYPE_CHOICES
  )
  extra_fields = models.JSONField(null=True, blank=True)


class NotificationRelation(models.Model):
  class RelationType:
    PROJECT = "PROJECT"
    CLIENT = "CLIENT"
    TASK = "TASK"

  RELATION_TYPE_CHOICES = [
    (RelationType.PROJECT, "Project"),
    (RelationType.CLIENT, "Client"),
    (RelationType.TASK, "Task"),
  ]

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  notification = models.ForeignKey(Notification, on_delete=models.CASCADE)

  project = models.ForeignKey(
    "projects_and_clients.Project", on_delete=models.CASCADE, null=True, blank=True
  )
  client = models.ForeignKey(
    "projects_and_clients.Client", on_delete=models.CASCADE, null=True, blank=True
  )
  task = models.ForeignKey(
    "projects_and_clients.Task", on_delete=models.CASCADE, null=True, blank=True
  )
  relation_type = models.CharField(
    max_length=50, choices=RELATION_TYPE_CHOICES, null=True, blank=True
  )
