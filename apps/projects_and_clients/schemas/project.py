from typing import Optional, Literal
from uuid import UUID
from datetime import date

from ninja import Schema, ModelSchema, FilterSchema
from pydantic import field_validator
from django.utils import timezone

from apps.projects_and_clients.models import Project


class ProjectSchema(ModelSchema):
  class Meta:
    model = Project
    fields = [
      "id",
      "name",
      "description",
      "estimated_deadline",
      "estimated_cost",
      "actual_deadline",
      "actual_cost",
      "profitability",
      "hour_profitability",
      "spent_time",
      "labor_fee",
      "status",
      "created_at",
      "updated_at",
      "closed_at",
      "colortag",
      "cover_photo",
    ]

  client_id: UUID


class CreateProjectReq(ModelSchema):
  class Meta:
    model = Project
    fields = [
      "name",
      "description",
      "estimated_deadline",
      "estimated_cost",
      "labor_fee",
      "colortag",
    ]

  client_id: str


class UpdateProjectReq(ModelSchema):
  class Meta:
    model = Project
    fields = [
      "name",
      "description",
      "estimated_deadline",
      "estimated_cost",
      "labor_fee",
      "colortag",
    ]


class PartialUpdateProjectReq(ModelSchema):
  class Meta:
    model = Project
    fields = [
      "name",
      "description",
      "estimated_deadline",
      "estimated_cost",
      "labor_fee",
      "colortag",
    ]
    fields_optional = "__all__"


class ProjectFilterSchema(FilterSchema):
  client_id: Optional[str] = None
  status: Optional[str] = None
  colortag: Optional[str] = None


class ProjectCloseSchema(Schema):
  actual_deadline: date
  actual_cost: float
  spent_time: timezone.timedelta
  status: Literal[
    Project.CONCLUDED_STATUS,
    Project.PARTIALLY_CONCLUDED_STATUS,
    Project.CANCELLED_STATUS,
  ]

  @field_validator("spent_time", mode="before", check_fields=False)
  def spent_time_as_hours(cls, v: str) -> str:
    # Try convert to float (allows .00) and then to int to remove decimal part (.00).
    try:
      hours = float(v)
      return timezone.timedelta(hours=int(hours))
    except Exception:
      pass

    # If convert fails, it means that v can be a full time string, like "HH:MM:SS".
    return v
