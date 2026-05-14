from typing import TypedDict

from django.db.models import QuerySet

from apps.finances.schemas.dashboard import DashboardPeriodFilter
from apps.projects_and_clients.models import Project
from apps.users.models import User


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


class DashboardService:
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
      total_gains=total_gains,
      total_costs=total_costs,
      profitability=total_profitability,
    )

  @staticmethod
  def projects_rankings(
    user: User,
    period: DashboardPeriodFilter,
    rankings_count: int = 5,
    projects_qs: QuerySet[Project] | None = None,
  ) -> RankingsDTO:
    """
    Returns project rankins for given period, where each rank is
    a list of a dict with project and value keys, sorted by value in
    value key.

    Args:
      user: The user to get the projects for.
      period: The period to get the projects for.
      rankings_count: The number of projects to return for each rank.
      projects_qs: The queryset of projects to get the projects for.
    """
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

    # Sort and pick top N (rankings_count=5) for each category
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

    # Format ranks with Project and value.
    total_gain_rank = [
      {"project": item["project"], "value": item["gain"]} for item in bigger_gain
    ]
    total_cost_rank = [
      {"project": item["project"], "value": item["cost"]} for item in bigger_cost
    ]
    total_profitability_rank = [
      {"project": item["project"], "value": item["profit"]} for item in bigger_profit
    ]
    total_hour_profitability_rank = [
      {"project": item["project"], "value": item["hour_profit"]}
      for item in bigger_hour_profit
    ]

    return RankingsDTO(
      total_gain=total_gain_rank,
      total_cost=total_cost_rank,
      profitability=total_profitability_rank,
      hour_profitability=total_hour_profitability_rank,
    )

  @staticmethod
  def _projects_qs(user: User, period: DashboardPeriodFilter) -> QuerySet[Project]:
    """
    Return a queryset of projects filtered by user and period range.
    The returned queryset is optimized for most of DashboardService methods.
    """

    return Project.objects.filter(
      user=user, created_at__date__range=(period.start_date, period.end_date)
    ).prefetch_related("task_set__movimentation")
