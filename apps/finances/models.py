from django.db import models
from django.utils import timezone

from apps.users.models import User

import uuid


# Create your models here.
class MovGroup(models.Model):
  RELATION_CHOICES = [
    ("NORELATION", "No relation, personal only"),  # Means personal finances data
    ("PROJECT", "Project Related"),  # Means project related finances data
  ]

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  name = models.CharField(max_length=127)
  description = models.TextField(max_length=512, blank=True, null=True)

  related_to = models.UUIDField(null=True, blank=True, db_index=True)
  relation = models.CharField(
    max_length=22, choices=RELATION_CHOICES, default="NORELATION", editable=False
  )

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=["user", "name"], name="user_movgroup_name_unique")
    ]

  def __str__(self):
    return self.name


class Movimentation(models.Model):
  BALANCE_CHOICES = [
    ("+", "Positive - Money is comming in"),
    ("-", "Negative - Money is going out"),
  ]

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  mov_group = models.ForeignKey(MovGroup, on_delete=models.CASCADE)

  amount = models.DecimalField(max_digits=20, decimal_places=2)
  balance = models.CharField(max_length=1, choices=BALANCE_CHOICES)
  reason = models.CharField(max_length=255)

  movemented_at = models.DateTimeField(default=timezone.now)

  def __str__(self):
    return self.reason

  @property
  def value(self) -> float:
    """Return the value of the movimentation (considering the movimentation balance)."""
    if self.balance == "+":
      return float(self.amount)
    return -float(self.amount)
