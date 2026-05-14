from typing import TypedDict

from django.db.models import QuerySet

from apps.finances.schemas.dashboard import DashboardPeriodFilter
from apps.projects_and_clients.models import Project
from apps.users.models import User


class FastViewsDTO(TypedDict):
  total_gains: float
  total_costs: float
  profitability: float


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
  def _projects_qs(user: User, period: DashboardPeriodFilter) -> QuerySet[Project]:
    """
    Return a queryset of projects filtered by user and period range.
    The returned queryset is optimized for most of DashboardService methods.
    """

    return Project.objects.filter(
      user=user, created_at__date__range=(period.start_date, period.end_date)
    ).prefetch_related("task_set__movimentation")
