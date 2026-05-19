from datetime import date

from ninja import Schema
from pydantic import model_validator

from apps.projects_and_clients.schemas.project import ProjectSchema


class DashboardPeriodFilter(Schema):
  start_date: date
  end_date: date

  @model_validator(mode="after")
  def validate_date_range(self):
    if self.start_date > self.end_date:
      raise ValueError("start_date cannot be greater than end_date")
    return self


class DashboardFilter(DashboardPeriodFilter):
  includes_open_projects: bool


class ProjectsRankingsFilter(DashboardFilter):
  rankings_count: int = 5

  @model_validator(mode="after")
  def validate_rankings_count(self):
    if self.rankings_count <= 0:
      raise ValueError("rankings_count must be greater than 0")
    return self


class ProjectRanking(Schema):
  project: ProjectSchema
  value: float


class ProjectsRankingsRes(Schema):
  total_gain: list[ProjectRanking]
  total_cost: list[ProjectRanking]
  profitability: list[ProjectRanking]
  hour_profitability: list[ProjectRanking]


class ProjectProfitComposition(Schema):
  project: ProjectSchema
  profit: float
  percentage: float


class IncomeProjectsCompositionRes(Schema):
  composition: list[ProjectProfitComposition]
  total_profitability: float


class IncomeHistoryFilter(DashboardFilter):
  includes_personal_finances: bool
