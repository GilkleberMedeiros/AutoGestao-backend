from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date

from ninja import Schema


class MetricSummarySchema(Schema):
  total_gain: Decimal
  total_expense: Decimal
  total_profit: Decimal


class ProjectRankingItemSchema(Schema):
  project_id: UUID
  project_name: str
  value: Decimal


class DashboardRankingsSchema(Schema):
  highest_gain: List[ProjectRankingItemSchema]
  highest_expense: List[ProjectRankingItemSchema]
  highest_profitability: List[ProjectRankingItemSchema]
  highest_profit_time: List[ProjectRankingItemSchema]


class IncomeCompositionItemSchema(Schema):
  project_name: str
  percentage: float


class ProfitabilityHistoryItemSchema(Schema):
  period_label: str  # e.g., "Jan 2026"
  value: Decimal


class DashboardFiltersSchema(Schema):
  # Frontend can define the period type (static, varaible) by parssing the start and end dates.
  start_date: Optional[date] = None
  end_date: Optional[date] = None
  include_personal: bool = True
