from typing import Optional
from uuid import UUID

from ninja import ModelSchema, FilterSchema

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


class ProjectCloseSchema(ModelSchema):
  class Meta:
    model = Project
    fields = [
      "actual_deadline",
      "actual_cost",
      "spent_time",
      "status",
    ]
