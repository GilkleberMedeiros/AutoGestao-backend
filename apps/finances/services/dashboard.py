from typing import TypedDict

from django.db.models import QuerySet

from apps.finances.schemas.dashboard import DashboardPeriodFilter
from apps.projects_and_clients.models import Project
from apps.users.models import User


class FastViewsDTO(TypedDict):
  projects_total_gains: float
  projects_total_costs: float
  project_profitability: float


class RankingsDTO(TypedDict):
  total_gain: list[Project]
  total_cost: list[Project]
  profitability: list[Project]
  hour_profitability: list[Project]


class Dashboard(TypedDict):
  fast_views: FastViewsDTO
  projects_rankings: RankingsDTO
  income_projects_composition: dict


class DashboardService:
  cached_projects_qs: QuerySet[Project] | None = None

  @staticmethod
  def dashboard(
    user: User, period: DashboardPeriodFilter, include_personal_finances: bool
  ) -> Dashboard:
    qs = DashboardService._projects_qs(user, period)

    return Dashboard(
      fast_views=DashboardService.fast_views(user, period, projects_qs=qs),
      projects_rankings=DashboardService.projects_rankings(
        user, period, projects_qs=qs
      ),
      income_projects_composition=DashboardService.income_projects_composition(
        user, period, projects_qs=qs
      ),
    )

  @staticmethod
  def fast_views(
    user: User,
    period: DashboardPeriodFilter,
    projects_qs: QuerySet[Project] | None = None,
  ) -> FastViewsDTO:
    projects = projects_qs

    if projects_qs is None:
      projects = DashboardService._projects_qs(user, period)

    total_gains = 0.0
    total_costs = 0.0
    total_profitability = 0.0

    for project in projects:
      tasks = project.task_set.all()
      total_gains += project.calc_project_total_gain(tasks)
      total_costs += project.calc_project_total_cost(tasks)
      total_profitability += project.calc_project_profitability(tasks)

    return FastViewsDTO(
      projects_total_gains=total_gains,
      projects_total_costs=total_costs,
      project_profitability=total_profitability,
    )

  @staticmethod
  def projects_rankings(
    user: User,
    period: DashboardPeriodFilter,
    rankings_count: int = 5,
    projects_qs: QuerySet[Project] | None = None,
  ) -> RankingsDTO:
    projects = projects_qs

    if projects_qs is None:
      projects = DashboardService._projects_qs(user, period)

    # We'll store projects with their calculated values for sorting
    project_data = []
    for project in projects:
      tasks = project.task_set.all()
      gain = project.calc_project_total_gain(tasks)
      cost = project.calc_project_total_cost(tasks)
      profit = project.calc_project_profitability(tasks)
      hour_profit = project.calc_project_hour_profitability(profit)

      project_data.append(
        {
          "project": project,
          "gain": gain,
          "cost": cost,
          "profit": profit,
          "hour_profit": hour_profit,
        }
      )

    # Sort and pick top 5 for each category
    # Note: cost is usually negative, so "bigger cost" means most negative (lowest value)
    bigger_gain = sorted(project_data, key=lambda x: x["gain"], reverse=True)[
      :rankings_count
    ]
    bigger_cost = sorted(project_data, key=lambda x: x["cost"])[:rankings_count]
    bigger_profit = sorted(project_data, key=lambda x: x["profit"], reverse=True)[
      :rankings_count
    ]
    bigger_hour_profit = sorted(
      project_data, key=lambda x: x["hour_profit"], reverse=True
    )[:rankings_count]

    return RankingsDTO(
      total_gain=[item["project"] for item in bigger_gain],
      total_cost=[item["project"] for item in bigger_cost],
      profitability=[item["project"] for item in bigger_profit],
      hour_profitability=[item["project"] for item in bigger_hour_profit],
    )

  @classmethod
  def income_projects_composition(
    cls,
    user: User,
    period: DashboardPeriodFilter,
    projects_qs: QuerySet[Project] | None = None,
  ) -> dict:
    projects = projects_qs

    if projects_qs is None:
      projects = cls._projects_qs(user, period)

    total_profitability = 0.0
    project_data = []

    for project in projects:
      tasks = project.task_set.all()
      profit = project.calc_project_profitability(tasks)
      project_data.append({"name": project.name, "profit": profit})
      total_profitability += profit

    if total_profitability == 0:
      return {item["name"]: 0.0 for item in project_data}

    return {
      item["name"]: round((item["profit"] / total_profitability) * 100, 2)
      for item in project_data
    }

  @staticmethod
  def _projects_qs(user: User, period: DashboardPeriodFilter) -> QuerySet[Project]:
    """
    Return a queryset of projects filtered by user and period range.
    The returned queryset is optimized for most of DashboardService methods.
    """

    return Project.objects.filter(
      user=user, created_at__date__range=(period.start_date, period.end_date)
    ).prefetch_related("task_set__movimentation")
