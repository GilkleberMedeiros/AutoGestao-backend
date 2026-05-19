from ninja import Router, Query

from apps.core.schemas.response import BaseAPIResponse
from apps.finances.schemas.dashboard import (
  DashboardFilter,
  ProjectsRankingsFilter,
  ProjectsRankingsRes,
  IncomeProjectsCompositionRes,
)
from apps.finances.services.dashboard import DashboardService, FastViewsDTO

router = Router()


@router.get(
  "/fast-views",
  response={200: FastViewsDTO, 401: BaseAPIResponse},
)
def fast_views(request, filters: DashboardFilter = Query(...)):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  service = DashboardService(
    user=request.user,
    period=filters,
    includes_open_projects=filters.includes_open_projects,
  )

  return 200, service.fast_views()


@router.get(
  "/projects-rankings",
  response={200: ProjectsRankingsRes, 401: BaseAPIResponse},
)
def projects_rankings(request, filters: ProjectsRankingsFilter = Query(...)):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  service = DashboardService(
    user=request.user,
    period=filters,
    includes_open_projects=filters.includes_open_projects,
  )

  return 200, service.projects_rankings(rankings_count=filters.rankings_count)


@router.get(
  "/income-projects-composition",
  response={200: IncomeProjectsCompositionRes, 401: BaseAPIResponse},
)
def income_projects_composition(request, filters: DashboardFilter = Query(...)):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  service = DashboardService(
    user=request.user,
    period=filters,
    includes_open_projects=filters.includes_open_projects,
  )

  composition, total_profitability = service.income_projects_composition()

  return 200, {
    "composition": composition,
    "total_profitability": total_profitability,
  }
