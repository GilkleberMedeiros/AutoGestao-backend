from typing import Literal, TypedDict

from apps.projects_and_clients.models import Project


class FastViewsDTO(TypedDict):
  total_gains: float
  total_costs: float
  profitability: float


class _ProjectRankingDTO(TypedDict):
  project: Project
  value: float


class RankingsDTO(TypedDict):
  total_gain: list[_ProjectRankingDTO]
  total_cost: list[_ProjectRankingDTO]
  profitability: list[_ProjectRankingDTO]
  hour_profitability: list[_ProjectRankingDTO]


class ProjectProfitCompositionDTO(TypedDict):
  project: Project
  profit: float
  percentage: float


IncomeProjectsCompositionDTO = tuple[list[ProjectProfitCompositionDTO], float]


class IncomeRegisterDTO(TypedDict):
  date: str
  profit: float


IncomeHistoryDTO = list[IncomeRegisterDTO]


class DashboardDTO(TypedDict):
  projects_fast_views: FastViewsDTO | None
  projects_rankings: RankingsDTO | None
  income_projects_composition: IncomeProjectsCompositionDTO | None
  income_history: IncomeHistoryDTO | None


DashboardMetricsParamT = Literal[
  "projects_fast_views",
  "projects_rankings",
  "income_projects_composition",
  "income_history",
]
