from typing import TypedDict

from django.db.models import QuerySet

from apps.finances.schemas.dashboard import DashboardPeriodFilter
from apps.projects_and_clients.models import Project
from apps.finances.models import Movimentation
from apps.users.models import User


class FastViewsDTO(TypedDict):
  projects_total_gains: float
  projects_total_costs: float
  project_profitability: float


class RankingsDTO(TypedDict):
  total_gain: list[dict]
  total_cost: list[dict]
  profitability: list[dict]
  hour_profitability: list[dict]


class Dashboard(TypedDict):
  fast_views: FastViewsDTO
  projects_rankings: RankingsDTO
  income_projects_composition: dict
  income_history: dict[str, float]


class DashboardService:
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

  @classmethod
  def income_projects_composition(
    cls,
    user: User,
    period: DashboardPeriodFilter,
    projects_qs: QuerySet[Project] | None = None,
  ) -> tuple[list[dict], float]:
    """
    Calculate the composition of total profit for
    each project excluding projects with zero or less profit.
    """

    projects = projects_qs

    if projects_qs is None:
      projects = cls._projects_qs(user, period)

    total_profitability = 0.0
    project_data = []

    # Calc total profit
    for project in projects:
      tasks = project.task_set.all()
      profit = project.calc_project_profitability(tasks)
      # Exclude projects with zero or less profit.
      if profit > 0:
        project_data.append(
          {"name": project.name, "profit": profit, "project": project}
        )
        total_profitability += profit

    # Returns empty list and zero if total_profitability is zero.
    if total_profitability == 0:
      return [], 0.0

    # Calculate composition of total profit for each project.
    composition: list[dict] = []
    for item in project_data:
      composition.append(
        {
          "project": item["project"],
          "profit": item["profit"],
          "percentage": round((item["profit"] / total_profitability) * 100, 2),
        }
      )

    return composition, total_profitability

  @staticmethod
  def income_history(
    user: User,
    period: DashboardPeriodFilter,
    includes_personal_finances: bool,
    projects_qs: QuerySet[Project] | None = None,
  ) -> dict[str, float]:
    """
    Returns a history graph data with the income over time.
    The data is grouped by days.

    Args:
      user: User who owns the data.
      period: Period to filter the data.
      includes_personal_finances: Whether to include personal finances data.
      projects_qs: Queryset of projects.

    Returns:
      Dict of profits in days, where each key is a full date (YYYY-MM-DD)
      and value is the profit in that day.
    """
    projects = projects_qs

    if projects_qs is None:
      projects = DashboardService._projects_qs(user, period)

    profits_in_days = {}
    # Get projects profit in the period range separated by full date (YYYY-MM-DD).
    for project in projects:
      if project.closed_at:
        date = project.closed_at.date().isoformat()
        profits_in_days[date] = profits_in_days.get(date, 0.0) + project.labor_fee

      for task in project.task_set.all():
        if task.movimentation is None:
          continue

        date = task.movimentation.movemented_at.date().isoformat()
        profits_in_days[date] = profits_in_days.get(date, 0.0) + (
          task.movimentation.value
        )

    if includes_personal_finances:
      # Get personal finances profit in the period range separated by full date (YYYY-MM-DD).
      movimentations = Movimentation.objects.filter(
        mov_group__user=user,
        mov_group__relation="NORELATION",
        movemented_at__date__range=(period.start_date, period.end_date),
      )

      for movimentation in movimentations:
        date = movimentation.movemented_at.date().isoformat()
        profits_in_days[date] = profits_in_days.get(date, 0.0) + movimentation.value

    return profits_in_days

  @staticmethod
  def _projects_qs(user: User, period: DashboardPeriodFilter) -> QuerySet[Project]:
    """
    Return a queryset of projects filtered by user and period range.
    The returned queryset is optimized for most of DashboardService methods.
    """

    return Project.objects.filter(
      user=user, created_at__date__range=(period.start_date, period.end_date)
    ).prefetch_related("task_set__movimentation")
