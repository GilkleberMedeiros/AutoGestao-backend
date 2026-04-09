from typing import Optional
from datetime import datetime
from uuid import UUID

from decimal import Decimal
from ninja import ModelSchema, Schema

from apps.projects_and_clients.models import Task


class TaskSchema(ModelSchema):
  class Meta:
    model = Task
    fields = [
      "id",
      "name",
      "description",
      "done_at",
      "created_at",
      "updated_at",
    ]

  project_id: UUID
  finance_id: Optional[UUID] = None


class TaskFinanceInputSchema(Schema):
  amount: Decimal
  balance: str  # POSITIVE / NEGATIVE
  reason: Optional[str] = None
  movemented_at: Optional[datetime] = None


class CreateTaskReq(ModelSchema):
  class Meta:
    model = Task
    fields = [
      "name",
      "description",
      "done_at",
      "finance",
    ]

  description: Optional[str] = None
  done_at: Optional[datetime] = None
  finance_id: Optional[UUID] = None
  finance_entry: Optional[TaskFinanceInputSchema] = None


class UpdateTaskReq(ModelSchema):
  class Meta:
    model = Task
    fields = [
      "name",
      "description",
      "done_at",
      "finance",
    ]

  description: Optional[str] = None
  done_at: Optional[datetime] = None
  finance_id: Optional[UUID] = None


class PartialUpdateTaskReq(ModelSchema):
  class Meta:
    model = Task
    fields = [
      "name",
      "description",
      "done_at",
      "finance",
    ]
    fields_optional = "__all__"

  finance_id: Optional[UUID] = None
