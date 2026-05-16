from typing import TypedDict
from copy import copy
from datetime import date, timedelta

from django.db.models import QuerySet

from apps.core.exceptions import AppError
from apps.finances.schemas.dashboard import DashboardPeriodFilter
from apps.finances.models import Movimentation
from apps.projects_and_clients.models import Project
from apps.users.models import User


class InvalidRankingsCountError(AppError):
  def __init__(
    self, message: str = "Invalid rankings count. Must be greater than 0."
  ) -> None:
    super().__init__(message)


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


class DashboardMetricsParam(TypedDict):
  projects_fast_views: bool
  projects_rankings: bool
  income_projects_composition: bool
  income_history: bool


class DashboardService:
  def __init__(
    self, user: User, period: DashboardPeriodFilter, includes_open_projects: bool
  ) -> None:
    """
    Initialize the DashboardService.

    Args:
      user: The user to get the projects for.
      period: The period to get the projects for.
      includes_open_projects: Whether to include projects that are still open.
    """
    self.user = user
    self.period = period
    self.includes_open_projects = includes_open_projects
    self._qs = self._projects_qs(user, period, includes_open_projects)
    self._projects_data = None

  def dashboard(
    self,
    includes_personal_finances: bool,
    rankings_count: int = 5,
    metrics: DashboardMetricsParam | None = None,
  ):
    """
    Return the entire dashboard with the dashboard metrics.

    Args:
      includes_personal_finances: Whether to include personal
      finances in the dashboard income history metric.
      rankings_count: The number of projects to include in the rankings metric.
      metrics: The metrics to include in the dashboard.
    """

    if metrics is None:
      return DashboardDTO(
        projects_fast_views=self.fast_views(),
        projects_rankings=self.projects_rankings(rankings_count),
        income_projects_composition=self.income_projects_composition(),
        income_history=self.income_history(includes_personal_finances),
      )

    dashboard = DashboardDTO(
      projects_fast_views=None,
      projects_rankings=None,
      income_projects_composition=None,
      income_history=None,
    )

    if metrics.get("projects_fast_views", False):
      dashboard["projects_fast_views"] = self.fast_views()

    if metrics.get("projects_rankings", False):
      dashboard["projects_rankings"] = self.projects_rankings(rankings_count)

    if metrics.get("income_projects_composition", False):
      dashboard["income_projects_composition"] = self.income_projects_composition()

    if metrics.get("income_history", False):
      dashboard["income_history"] = self.income_history(includes_personal_finances)

    return dashboard

  def fast_views(self) -> FastViewsDTO:
    """
    Calculate the fast visualizations metrics for the dashboard.
    """
    # Get projects and calc base metrics for each project.
    projects = self._calc_projects_base_metrics()

    total_gains = 0.0
    total_costs = 0.0
    total_profitability = 0.0

    for project in projects:
      total_gains += project["gain"]
      total_costs += project["cost"]
      total_profitability += project["profit"]

    return FastViewsDTO(
      total_gains=total_gains,
      total_costs=total_costs,
      profitability=total_profitability,
    )

  def projects_rankings(self, rankings_count: int = 5) -> RankingsDTO:
    """
    Returns project rankings metrics, where each rank is
    a list of a dict with project and value keys, sorted by value in
    value key.

    Args:
      rankings_count: The number of projects to return for each rank.
    """
    if rankings_count <= 0:
      raise InvalidRankingsCountError()

    # Calc base metrics for each project.
    project_data = self._calc_projects_base_metrics()

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

  def income_projects_composition(self) -> IncomeProjectsCompositionDTO:
    """
    Calculate the composition of total profit for
    each project excluding projects with zero or less profit.
    Returns a tuple of (composition, total_profitability).
    """
    # Get and calc projects base metrics (including profit).
    projects = self._calc_projects_base_metrics()
    total_profitability = 0.0
    projects_data = []

    # Calc total profit
    for project in projects:
      profit = project["profit"]
      project = project["project"]
      # Exclude projects with zero or less profit.
      if profit > 0:
        projects_data.append({"profit": profit, "project": project})
        total_profitability += profit

    # Returns empty list and zero if total_profitability is zero.
    if total_profitability <= 0:
      return [], 0.0

    # Calculate composition of total profit for each project.
    composition: list[dict] = []
    for item in projects_data:
      composition.append(
        {
          "project": item["project"],
          "profit": item["profit"],
          "percentage": round((item["profit"] / total_profitability) * 100, 2),
        }
      )

    return composition, total_profitability

  def income_history(self, includes_personal_finances: bool) -> IncomeHistoryDTO:
    """
    Returns a history graph data with the income over time.
    The data is grouped by days.

    Args:
      includes_personal_finances: Whether to include personal finances data.

    Returns:
      A list of dicts sorted by date (ascending). Each dict contains the date and the
      profit made in that date. Each list pos is a day (date) in the
      period range (inclusive), even some pos have 0.0 profit.
    """
    projects = self._qs
    user = self.user
    period = self.period
    profits_in_days = {}

    # Get projects profit in the period range separated by full date (YYYY-MM-DD).
    for project in projects:
      # Add labor_fee income if project was closed in the period range.
      if project.closed_at and period.end_date >= project.closed_at.date():
        d = project.closed_at.date().isoformat()
        profits_in_days[d] = profits_in_days.get(d, 0.0) + project.labor_fee

      for task in project.task_set.all():
        if task.movimentation is None:
          continue
        if task.movimentation.movemented_at.date() > period.end_date:
          continue

        d = task.movimentation.movemented_at.date().isoformat()
        profits_in_days[d] = profits_in_days.get(d, 0.0) + (task.movimentation.value)

    if includes_personal_finances:
      # Get personal finances profit in the period range separated by full date (YYYY-MM-DD).
      movimentations = Movimentation.objects.filter(
        mov_group__user=user,
        mov_group__relation="NORELATION",
        movemented_at__date__range=(period.start_date, period.end_date),
      )

      for movimentation in movimentations:
        d = movimentation.movemented_at.date().isoformat()
        profits_in_days[d] = profits_in_days.get(d, 0.0) + movimentation.value

    # Sort and Format output data.
    history = []
    for d in self._date_range(period.start_date, period.end_date):
      key = d.isoformat()
      profit = profits_in_days.get(key, 0.0)
      history.append({"date": key, "profit": profit})

    history = sorted(history, key=lambda x: date.fromisoformat(x["date"]))

    return history

  @staticmethod
  def _projects_qs(
    user: User, period: DashboardPeriodFilter, includes_open_projects: bool
  ) -> QuerySet[Project]:
    """
    Return a queryset of projects filtered by user, period range and
    if projects that are still open should be included.
    The returned queryset is optimized for most of DashboardService methods.
    """
    project_qs = Project.objects.filter(
      user=user, created_at__date__range=(period.start_date, period.end_date)
    ).prefetch_related("task_set__movimentation")

    if not includes_open_projects:
      project_qs = project_qs.exclude(status=Project.OPEN_STATUS)

    return project_qs

  def _calc_projects_base_metrics(self):
    """
    Calculate base metrics for all projects and cache them in the
    _projects_data attribute. Using this method avoids the need to
    recalculate metrics for the same projects multiple times.

    Returns:
      list[dict[str, Project | float]]: list of dicts where each dict
      contains the following keys: "project", "gain", "cost", "profit",
      "hour_profit" (original project and its metrics).
    """

    if self._projects_data:
      return self._projects_data

    self._projects_data = []
    for project in self._qs:
      tasks = project.task_set.all()
      gain = project.calc_project_total_gain(tasks)
      cost = project.calc_project_total_cost(tasks)
      profit = project.calc_project_profitability(tasks)
      hour_profit = project.calc_project_hour_profitability(profit)

      self._projects_data.append(
        {
          "project": project,
          "gain": gain,
          "cost": cost,
          "profit": profit,
          "hour_profit": hour_profit,
        }
      )

    return self._projects_data

  @staticmethod
  def _date_range(start_date: date, end_date: date):
    """
    Generator that yields dates from start_date to end_date
    (inclusive-inclusive).
    """

    # Copy date objects to avoid modifying the originals.
    sdate = copy(start_date)
    edate = copy(end_date)

    while sdate <= edate:
      yield sdate
      sdate += timedelta(days=1)
