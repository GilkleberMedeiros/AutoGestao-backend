from django.db import models

import uuid

from apps.users.models import User
from apps.users.field_validators.phone import PhoneValidator


class Client(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  name = models.CharField(max_length=255)
  # TODO: Add CPF validator to valid CPF format
  cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)

  def __str__(self):
    return self.name


class ClientPhone(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  client = models.ForeignKey(
    Client, on_delete=models.CASCADE, related_name="phones", related_query_name="phone"
  )
  phone = models.CharField(max_length=24, validators=[PhoneValidator])


class ClientEmail(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  client = models.ForeignKey(
    Client, on_delete=models.CASCADE, related_name="emails", related_query_name="email"
  )
  email = models.EmailField(max_length=256)


class ClientRating(models.Model):
  RATING_CHOICES = [
    (0.0, "0.0"),
    (0.5, "0.5"),
    (1.0, "1.0"),
    (1.5, "1.5"),
    (2.0, "2.0"),
    (2.5, "2.5"),
    (3.0, "3.0"),
    (3.5, "3.5"),
    (4.0, "4.0"),
    (4.5, "4.5"),
    (5.0, "5.0"),
  ]

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  client = models.OneToOneField(
    Client, on_delete=models.CASCADE, related_name="rating", related_query_name="rating"
  )
  score = models.FloatField(choices=RATING_CHOICES)
  comment = models.TextField(max_length=255, null=True, blank=True)


class ClientAddress(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  client = models.OneToOneField(
    Client,
    on_delete=models.CASCADE,
    related_name="address",
    related_query_name="address",
  )
  state = models.CharField(max_length=2)
  city = models.CharField(max_length=255)
  neighborhood = models.CharField(max_length=255)
  street = models.CharField(max_length=255)
  house_number = models.CharField(max_length=10)
  complement = models.CharField(max_length=255, null=True, blank=True)


class Project(models.Model):
  STATUS_CHOICES = [
    ("OPEN", "Open"),
    ("CONCLUDED", "Concluded"),
    ("PARTIALLY_CONCLUDED", "Partially Concluded"),
    ("CANCELLED", "Cancelled"),
  ]

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  client = models.ForeignKey(Client, on_delete=models.CASCADE)
  name = models.CharField(max_length=255)
  description = models.TextField(max_length=512, null=True, blank=True)

  estimated_deadline = models.DateField()
  estimated_cost = models.DecimalField(max_digits=20, decimal_places=2)
  actual_deadline = models.DateField(null=True, blank=True)
  actual_cost = models.DecimalField(
    max_digits=20, decimal_places=2, null=True, blank=True
  )
  profitability = models.DecimalField(
    max_digits=20, decimal_places=2, null=True, blank=True
  )
  hour_profitability = models.DecimalField(
    max_digits=20, decimal_places=2, null=True, blank=True
  )
  spent_time = models.DurationField(null=True, blank=True)

  status = models.CharField(choices=STATUS_CHOICES, default="OPEN")

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  closed_at = models.DateTimeField(null=True, blank=True)

  # TODO: Add validator to valid the hexadecimal color (format: #000000)
  colortag = models.CharField(max_length=7, null=True, blank=True)

  def __str__(self):
    return self.name


class Task(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  project = models.ForeignKey(
    Project, on_delete=models.CASCADE, related_name="tasks", related_query_name="task"
  )
  finance = models.OneToOneField(
    "finances.Finance",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="task",
    related_query_name="task",
  )
  name = models.CharField(max_length=128)
  description = models.TextField(max_length=512, null=True, blank=True)

  done_at = models.DateTimeField(null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.name
