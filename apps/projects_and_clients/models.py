from django.db import models
from django.db.models.query import QuerySet

import uuid

from apps.users.models import User
from apps.finances.models import Movimentation
from apps.users.field_validators.phone import PhoneValidator


class Client(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  name = models.CharField(max_length=255)
  # TODO: Add CPF validator to valid CPF format
  cpf = models.CharField(max_length=14, null=True, blank=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=["user", "cpf"], name="user_client_cpf_unique")
    ]

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
  # For queries, control and separation/filters.
  OPEN_STATUS = "OPEN"
  CONCLUDED_STATUS = "CONCLUDED"
  PARTIALLY_CONCLUDED_STATUS = "PARTIALLY_CONCLUDED"
  CANCELLED_STATUS = "CANCELLED"

  # For choices
  STATUS_CHOICES = [
    (OPEN_STATUS, "Open"),
    (CONCLUDED_STATUS, "Concluded"),
    (PARTIALLY_CONCLUDED_STATUS, "Partially Concluded"),
    (CANCELLED_STATUS, "Cancelled"),
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
  labor_fee = models.DecimalField(max_digits=20, decimal_places=2)

  status = models.CharField(choices=STATUS_CHOICES, default="OPEN")

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  closed_at = models.DateTimeField(null=True, blank=True)

  # TODO: Add validator to valid the hexadecimal color (format: #000000)
  colortag = models.CharField(max_length=7, null=True, blank=True)
  cover_photo = models.ImageField(
    upload_to="projects/cover-photos", null=True, blank=True
  )

  def __str__(self):
    return self.name

  def calc_project_total_gain(self, tasks_qs: QuerySet[Task] | None = None) -> float:
    """
    Calculate the project total gain (Movimentation values + labor_fee).
    Doesn't include the costs (negative values).

    Args:
      :tasks_qs: QuerySet[Task] | None: default None, if it's None,
      the method will create a new QuerySet and query the database to
      get all tasks. The given queryset must filter the tasks by
      the project itself and prefetch the movimentation for
      performance purposes.
    """
    total_gain = float(self.labor_fee)

    if tasks_qs is None:
      tasks_qs = Task.objects.filter(project=self).prefetch_related("movimentation")

    for task in tasks_qs:
      if task.movimentation is not None and task.movimentation.value > 0:
        total_gain += task.movimentation.value

    return total_gain

  def calc_project_total_cost(self, tasks_qs: QuerySet[Task] | None = None) -> float:
    """
    Calculate the project total cost.
    Doesn't include the gains (positive values).

    Args:
      :tasks_qs: QuerySet[Task] | None: default None, if it's None,
      the method will create a new QuerySet and query the database to
      get all tasks. The given queryset must filter the tasks by
      the project itself and prefetch the movimentation for
      performance purposes.
    """
    total_costs = 0.0

    if tasks_qs is None:
      tasks_qs = Task.objects.filter(project=self).prefetch_related("movimentation")

    for task in tasks_qs:
      if task.movimentation is not None and task.movimentation.value < 0:
        total_costs += task.movimentation.value

    return total_costs

  def calc_project_profitability(self, tasks_qs: QuerySet[Task] | None = None) -> float:
    """
    Calculate the project profitability. The project profitability is
    the sum of the project total gain, Project.labor_fee and the
    project total cost.

    Args:
      :tasks_qs: QuerySet[Task] | None: default None, if it's None,
      the method will create a new QuerySet and query the database to
      get all tasks. The given queryset must filter the tasks by
      the project itself and prefetch the movimentation for
      performance purposes.
    """
    profitability = 0.0

    if tasks_qs is None:
      tasks_qs = Task.objects.filter(project=self).prefetch_related("movimentation")

    # total_gains already includes the labor_fee.
    total_gains = self.calc_project_total_gain(tasks_qs)
    total_costs = self.calc_project_total_cost(tasks_qs)
    # Use '+' instead of '-', otherwise python will sum gains and costs.
    profitability = total_gains + total_costs

    return profitability

  def calc_project_hour_profitability(self, profitability: float = None) -> float:
    """
    Calculate the project hour profitability (profitability per hour).

    Args:
      :profitability: float | None: default None, if it's None, the
      method calls calc_project_profitability().
    """
    if profitability is None:
      profitability = self.calc_project_profitability()

    if self.spent_time is None:
      return 0.0

    # Use / instead of // to allow float results (e.g. 0.15).
    hour_profitability = profitability / (self.spent_time.total_seconds() / 3600)
    return hour_profitability


class Task(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  project = models.ForeignKey(Project, on_delete=models.CASCADE)
  movimentation = models.OneToOneField(
    Movimentation,
    on_delete=models.CASCADE,
    related_name="task",
    related_query_name="task",
    null=True,
    blank=True,
  )
  name = models.CharField(max_length=128)

  do_at = models.DateTimeField()
  is_done = models.BooleanField(default=False)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.name
