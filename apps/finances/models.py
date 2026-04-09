from django.db import models

import uuid

from apps.users.models import User


class FinGroup(models.Model):
  """
  Grupo de Finanças - pode estar relacionado a um Projeto ou ser pessoal/avulso.
  """
  RELATION_CHOICES = [
    ("PROJECT", "Project"),
    ("PERSONAL", "Personal"),
  ]

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  name = models.CharField(max_length=255)
  related_to = models.UUIDField(null=True, blank=True)  # Generic FK reference
  relation = models.CharField(
    max_length=20, choices=RELATION_CHOICES, default="PERSONAL"
  )

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.name


class Finance(models.Model):
  """
  Movimentação financeira pertencente a um grupo de finanças.
  """
  BALANCE_CHOICES = [
    ("POSITIVE", "Positive"),
    ("NEGATIVE", "Negative"),
  ]

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  fingroup = models.ForeignKey(
    FinGroup, on_delete=models.CASCADE, related_name="finances", related_query_name="finance"
  )
  amount = models.DecimalField(max_digits=20, decimal_places=2)
  balance = models.CharField(max_length=10, choices=BALANCE_CHOICES)
  reason = models.CharField(max_length=255)
  movemented_at = models.DateTimeField()

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f"{self.reason} ({self.balance}: {self.amount})"
