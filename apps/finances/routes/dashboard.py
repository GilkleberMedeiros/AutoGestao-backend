from typing import List
from ninja import Router, Query

from apps.core.schemas.response import BaseAPIResponse
from apps.finances.schemas.dashboard import (
  MetricSummarySchema,
  DashboardRankingsSchema,
  IncomeCompositionItemSchema,
  ProfitabilityHistoryItemSchema,
  DashboardFiltersSchema,
)
from apps.finances.services.dashboard import DashboardService

router = Router()


@router.get("/summary", response={200: MetricSummarySchema, 401: BaseAPIResponse})
def get_dashboard_summary(request, filters: DashboardFiltersSchema = Query(...)):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  return DashboardService.get_metric_summary(request.user, filters)


@router.get("/rankings", response={200: DashboardRankingsSchema, 401: BaseAPIResponse})
def get_dashboard_rankings(request, filters: DashboardFiltersSchema = Query(...)):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  return DashboardService.get_rankings(request.user, filters)


@router.get("/income-composition", response={200: List[IncomeCompositionItemSchema], 401: BaseAPIResponse})
def get_income_composition(request, filters: DashboardFiltersSchema = Query(...)):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  return DashboardService.get_income_composition(request.user, filters)


@router.get("/profitability-history", response={200: List[ProfitabilityHistoryItemSchema], 401: BaseAPIResponse})
def get_profitability_history(request, filters: DashboardFiltersSchema = Query(...)):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  return DashboardService.get_profitability_history(request.user, filters)
