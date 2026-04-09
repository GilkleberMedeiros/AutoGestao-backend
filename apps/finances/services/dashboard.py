from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from decimal import Decimal
from typing import List

from apps.finances.models import Finance, FinGroup
from apps.projects_and_clients.models import Project
from apps.finances.schemas.dashboard import (
  MetricSummarySchema,
  DashboardRankingsSchema,
  ProjectRankingItemSchema,
  IncomeCompositionItemSchema,
  ProfitabilityHistoryItemSchema,
  DashboardFiltersSchema,
)


class DashboardService:
  @staticmethod
  def _get_base_filters(user, filters: DashboardFiltersSchema):
    # RN05: Excluir projetos CANCELLED
    cancelled_project_ids = list(
      Project.objects.filter(user=user, status="CANCELLED").values_list("id", flat=True)
    )

    group_q = Q(user=user)
    if not filters.include_personal:
      group_q &= Q(relation="PROJECT")

    # Exclude cancelled projects groups
    group_q &= ~(Q(relation="PROJECT") & Q(related_to__in=cancelled_project_ids))

    valid_group_ids = FinGroup.objects.filter(group_q).values_list("id", flat=True)

    fin_q = Q(fingroup_id__in=valid_group_ids)
    if filters.start_date:
      fin_q &= Q(movemented_at__date__gte=filters.start_date)
    if filters.end_date:
      fin_q &= Q(movemented_at__date__lte=filters.end_date)

    return fin_q

  @staticmethod
  def get_metric_summary(user, filters: DashboardFiltersSchema) -> MetricSummarySchema:
    """
    RF13: Indicadores Totais
    Calcúla as métricas gerais do dashboard (total de ganhos, despesas e lucro).
    """
    fin_q = DashboardService._get_base_filters(user, filters)

    # Financial records metrics
    metrics = Finance.objects.filter(fin_q).aggregate(
      total_gain=Sum("amount", filter=Q(balance="POSITIVE")),
      total_expense=Sum("amount", filter=Q(balance="NEGATIVE")),
    )

    # Project actual_cost as gain (contract value)
    project_q = Q(user=user)
    if filters.start_date:
      project_q &= Q(closed_at__date__gte=filters.start_date)
    if filters.end_date:
      project_q &= Q(closed_at__date__lte=filters.end_date)

    # Exclude cancelled projects from gains/profit summary if appropriate?
    # Usually contract value from concluded/partially projects.
    project_q &= ~Q(status="CANCELLED")

    project_base_gain = Project.objects.filter(project_q).aggregate(
      total=Sum("actual_cost")
    )["total"] or Decimal("0.00")

    gain = (metrics["total_gain"] or Decimal("0.00")) + project_base_gain
    expense = metrics["total_expense"] or Decimal("0.00")

    return MetricSummarySchema(
      total_gain=gain,
      total_expense=expense,
      total_profit=gain - expense,
    )

  @staticmethod
  def get_rankings(user, filters: DashboardFiltersSchema) -> DashboardRankingsSchema:
    """
    RF14: Ranking de Projetos
    Cálcula o ranking de projetos por ganho, despesa, lucratividade e lucro por hora.
    """
    # Get all projects (not cancelled)
    projects = Project.objects.filter(user=user).exclude(status="CANCELLED")

    project_metrics = []
    for p in projects:
      # Use cached values if they represent the project state.
      # If filters are NOT present, use the model fields.
      # If filters ARE present, we MUST recalculate based on the period.

      if not filters.start_date and not filters.end_date:
        gain = p.actual_cost or Decimal("0.00")
        # We still need Tasks.finance gains/expenses since Project model fields
        # combine them into profitability, but not separated into gain/expense fields.

        # Actually, let's just recalculate to stay accurate to the filter even if empty.
        pass

      # Find FinGroup for this project
      group = FinGroup.objects.filter(
        user=user, related_to=p.id, relation="PROJECT"
      ).first()

      fin_q = Q(fingroup=group)
      if filters.start_date:
        fin_q &= Q(movemented_at__date__gte=filters.start_date)
      if filters.end_date:
        fin_q &= Q(movemented_at__date__lte=filters.end_date)

      stats = Finance.objects.filter(fin_q).aggregate(
        gain_tasks=Sum("amount", filter=Q(balance="POSITIVE")),
        expense_tasks=Sum("amount", filter=Q(balance="NEGATIVE")),
      )

      # Include actual_cost only if the project closed in this period
      include_base = True
      if filters.start_date and (
        not p.closed_at or p.closed_at.date() < filters.start_date
      ):
        include_base = False
      if filters.end_date and (
        not p.closed_at or p.closed_at.date() > filters.end_date
      ):
        include_base = False

      base_gain = p.actual_cost if include_base else Decimal("0.00")
      base_gain = base_gain or Decimal("0.00")

      gain = base_gain + (stats["gain_tasks"] or Decimal("0.00"))
      expense = stats["expense_tasks"] or Decimal("0.00")
      profit = gain - expense

      # Use p.hour_profitability if NO filters, else calculate
      if not filters.start_date and not filters.end_date and p.hour_profitability:
        profit_per_hour = p.hour_profitability
      else:
        hours = Decimal("1.0")
        if p.spent_time:
          total_seconds = Decimal(str(p.spent_time.total_seconds()))
          hours = total_seconds / Decimal("3600")
          if hours == 0:
            hours = Decimal("1.0")
        profit_per_hour = profit / hours

      project_metrics.append(
        {
          "project_id": p.id,
          "project_name": p.name,
          "gain": gain,
          "expense": expense,
          "profit": profit,
          "profit_time": profit_per_hour,
        }
      )

    def get_top_5(key):
      sorted_list = sorted(project_metrics, key=lambda x: x[key], reverse=True)[:5]
      return [
        ProjectRankingItemSchema(
          project_id=item["project_id"],
          project_name=item["project_name"],
          value=item[key],
        )
        for item in sorted_list
      ]

    return DashboardRankingsSchema(
      highest_gain=get_top_5("gain"),
      highest_expense=get_top_5("expense"),
      highest_profitability=get_top_5("profit"),
      highest_profit_time=get_top_5("profit_time"),
    )

  @staticmethod
  def get_income_composition(
    user, filters: DashboardFiltersSchema
  ) -> List[IncomeCompositionItemSchema]:
    """
    RF15: Composição de Receitas
    Calcula a composição de receitas por projeto em porcentagem.
    """
    summary = DashboardService.get_metric_summary(user, filters)
    total_gain = summary.total_gain

    if total_gain == 0:
      return []

    # Get non-cancelled projects
    projects = Project.objects.filter(user=user).exclude(status="CANCELLED")
    result_map = {}

    for p in projects:
      # 1. Base Gain (actual_cost) if in period
      include_base = True
      if filters.start_date and (
        not p.closed_at or p.closed_at.date() < filters.start_date
      ):
        include_base = False
      if filters.end_date and (
        not p.closed_at or p.closed_at.date() > filters.end_date
      ):
        include_base = False

      base_gain = p.actual_cost if include_base else Decimal("0.00")
      base_gain = base_gain or Decimal("0.00")

      # 2. Tasks Gains in period
      group = FinGroup.objects.filter(
        user=user, related_to=p.id, relation="PROJECT"
      ).first()
      task_gains = Decimal("0.00")
      if group:
        fin_q = Q(fingroup=group, balance="POSITIVE")
        if filters.start_date:
          fin_q &= Q(movemented_at__date__gte=filters.start_date)
        if filters.end_date:
          fin_q &= Q(movemented_at__date__lte=filters.end_date)

        task_gains = Finance.objects.filter(fin_q).aggregate(total=Sum("amount"))[
          "total"
        ] or Decimal("0.00")

      project_total = base_gain + task_gains
      if project_total > 0:
        result_map[p.name] = result_map.get(p.name, Decimal("0.00")) + project_total

    # Also handle personal groups if include_personal
    if filters.include_personal:
      personal_groups = FinGroup.objects.filter(user=user, relation="PERSONAL")
      for g in personal_groups:
        fin_q = Q(fingroup=g, balance="POSITIVE")
        if filters.start_date:
          fin_q &= Q(movemented_at__date__gte=filters.start_date)
        if filters.end_date:
          fin_q &= Q(movemented_at__date__lte=filters.end_date)

        g_gain = Finance.objects.filter(fin_q).aggregate(total=Sum("amount"))[
          "total"
        ] or Decimal("0.00")
        if g_gain > 0:
          result_map[g.name] = result_map.get(g.name, Decimal("0.00")) + g_gain

    result = []
    for name, amount in result_map.items():
      percentage = float((amount / total_gain) * 100)
      result.append(
        IncomeCompositionItemSchema(project_name=name, percentage=round(percentage, 2))
      )

    return result

  @staticmethod
  def get_profitability_history(
    user, filters: DashboardFiltersSchema
  ) -> List[ProfitabilityHistoryItemSchema]:
    """
    RF16: Histórico de Lucratividade
    Calcula o histórico de lucratividade por mês.
    """
    fin_q = DashboardService._get_base_filters(user, filters)

    # 1. Monthly totals from Finance records
    history = (
      Finance.objects.filter(fin_q)
      .annotate(month=TruncMonth("movemented_at"))
      .values("month")
      .annotate(
        gain=Sum("amount", filter=Q(balance="POSITIVE")),
        expense=Sum("amount", filter=Q(balance="NEGATIVE")),
      )
      .order_by("month")
    )

    result_map = {}
    for h in history:
      month = h["month"]
      if month:
        gain = h["gain"] or Decimal("0.00")
        expense = h["expense"] or Decimal("0.00")
        result_map[month] = gain - expense

    # 2. Add Project actual_cost to the respective months (based on closed_at)
    project_q = Q(user=user, status__in=["CONCLUDED", "PARTIALLY_CONCLUDED"])
    if filters.start_date:
      project_q &= Q(closed_at__date__gte=filters.start_date)
    if filters.end_date:
      project_q &= Q(closed_at__date__lte=filters.end_date)

    projects = (
      Project.objects.filter(project_q)
      .annotate(month=TruncMonth("closed_at"))
      .values("month")
      .annotate(total=Sum("actual_cost"))
    )

    for p in projects:
      month = p["month"]
      if month:
        result_map[month] = result_map.get(month, Decimal("0.00")) + (
          p["total"] or Decimal("0.00")
        )

    # Convert map to sorted list
    result = []
    for month in sorted(result_map.keys()):
      label = month.strftime("%b %Y")
      result.append(
        ProfitabilityHistoryItemSchema(period_label=label, value=result_map[month])
      )

    return result
