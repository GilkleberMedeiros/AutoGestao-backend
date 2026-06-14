from ninja import Router, Query
from django.http import HttpRequest, HttpResponse

from apps.core.schemas.response import BaseAPIResponse
from apps.core.utils.cache import cache_route
from apps.finances.schemas.dashboard import (
  DashboardFilter,
  ProjectsRankingsFilter,
  ProjectsRankingsRes,
  IncomeProjectsCompositionRes,
  IncomeHistoryFilter,
  DashboardRouteFilter,
  DashboardRes,
)
from apps.finances.services.dashboard.service import DashboardService
from apps.finances.services.dashboard.dto import (
  FastViewsDTO,
  IncomeHistoryDTO,
)

router = Router()


@cache_route(ttl=60 * 15)  # 15 minutes
@router.get(
  "/fast-views",
  response={200: FastViewsDTO, 401: BaseAPIResponse},
)
def fast_views(
  request: HttpRequest, response: HttpResponse, filters: DashboardFilter = Query(...)
):
  if not request.user.is_authenticated:
    response.headers["Cache-Control"] = "no-store"  # Don't cache error responses
    return 401, {"details": "Unauthenticated", "success": False}

  service = DashboardService(
    user=request.user,
    period=filters,
    includes_open_projects=filters.includes_open_projects,
  )

  return 200, service.fast_views()


@cache_route(ttl=60 * 15)
@router.get(
  "/projects-rankings",
  response={200: ProjectsRankingsRes, 401: BaseAPIResponse},
)
def projects_rankings(
  request: HttpRequest,
  response: HttpResponse,
  filters: ProjectsRankingsFilter = Query(...),
):
  if not request.user.is_authenticated:
    response.headers["Cache-Control"] = "no-store"
    return 401, {"details": "Unauthenticated", "success": False}

  service = DashboardService(
    user=request.user,
    period=filters,
    includes_open_projects=filters.includes_open_projects,
  )

  return 200, service.projects_rankings(rankings_count=filters.rankings_count)


@cache_route(ttl=60 * 15)
@router.get(
  "/income-projects-composition",
  response={200: IncomeProjectsCompositionRes, 401: BaseAPIResponse},
)
def income_projects_composition(
  request: HttpRequest, response: HttpResponse, filters: DashboardFilter = Query(...)
):
  if not request.user.is_authenticated:
    response.headers["Cache-Control"] = "no-store"
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


@cache_route(ttl=60 * 15)
@router.get(
  "/income-history",
  response={200: IncomeHistoryDTO, 401: BaseAPIResponse},
)
def income_history(
  request: HttpRequest,
  response: HttpResponse,
  filters: IncomeHistoryFilter = Query(...),
):
  if not request.user.is_authenticated:
    response.headers["Cache-Control"] = "no-store"
    return 401, {"details": "Unauthenticated", "success": False}

  service = DashboardService(
    user=request.user,
    period=filters,
    includes_open_projects=filters.includes_open_projects,
  )

  return 200, service.income_history(
    includes_personal_finances=filters.includes_personal_finances
  )


@cache_route(ttl=60 * 15)
@router.get(
  "/",
  response={200: DashboardRes, 401: BaseAPIResponse},
)
def dashboard(
  request: HttpRequest,
  response: HttpResponse,
  filters: DashboardRouteFilter = Query(...),
):
  if not request.user.is_authenticated:
    response.headers["Cache-Control"] = "no-store"
    return 401, {"details": "Unauthenticated", "success": False}

  service = DashboardService(
    user=request.user,
    period=filters,
    includes_open_projects=filters.includes_open_projects,
  )
  metrics = filters.include_metric

  dashboard_data = service.dashboard(
    includes_personal_finances=filters.includes_personal_finances,
    rankings_count=filters.rankings_count,
    metrics=metrics,
  )

  if dashboard_data.get("income_projects_composition") is not None:
    comp, total = dashboard_data["income_projects_composition"]
    dashboard_data["income_projects_composition"] = {
      "composition": comp,
      "total_profitability": total,
    }

  return 200, dashboard_data
