from django.utils import timezone
from apps.projects_and_clients.models import Project, Client
from apps.projects_and_clients.schemas.project import (
  CreateProjectReq,
  UpdateProjectReq,
  PartialUpdateProjectReq,
  ProjectFilterSchema,
  ProjectCloseSchema,
)
from apps.core.exceptions import ResourceNotFoundError
from datetime import timedelta


class BussinessRuleError(Exception):
  pass


class ProjectClosedForEditError(BussinessRuleError):
  pass


class InvalidCloseStatusError(BussinessRuleError):
  pass


class ProjectAlreadyOpenError(BussinessRuleError):
  pass


class ProjectNeverClosedError(BussinessRuleError):
  pass


class ReopenPeriodExpiredError(BussinessRuleError):
  pass


class ProjectService:
  @staticmethod
  def create(user, data: CreateProjectReq) -> Project:
    client = Client.objects.filter(id=data.client_id, user=user).first()
    if not client:
      raise ResourceNotFoundError("Client not found.")
    project = Project.objects.create(
      user=user,
      client=client,
      name=data.name,
      description=data.description,
      estimated_deadline=data.estimated_deadline,
      estimated_cost=data.estimated_cost,
      colortag=data.colortag,
    )
    return project

  @staticmethod
  def get(user, project_id: str) -> Project:
    project = Project.objects.filter(id=project_id, user=user).first()
    if not project:
      raise ResourceNotFoundError("Project not found.")
    return project

  @staticmethod
  def list(user, filters: ProjectFilterSchema):
    queryset = Project.objects.filter(user=user)
    if filters.client_id:
      queryset = queryset.filter(client_id=filters.client_id)
    if filters.status:
      queryset = queryset.filter(status=filters.status)
    if filters.colortag:
      queryset = queryset.filter(colortag=filters.colortag)
    return queryset

  @staticmethod
  def validate_open_status_for_edit(project: Project):
    """RN01: Um projeto só pode ser editado caso este esteja aberto."""
    if project.status != "OPEN":
      raise ProjectClosedForEditError(
        "The project cannot be edited because it is not open."
      )

  @staticmethod
  def update(user, project_id: str, data: UpdateProjectReq) -> Project:
    project = ProjectService.get(user, project_id)
    ProjectService.validate_open_status_for_edit(project)

    for attr, value in data.dict().items():
      setattr(project, attr, value)

    project.save()
    return project

  @staticmethod
  def partial_update(user, project_id: str, data: PartialUpdateProjectReq) -> Project:
    project = ProjectService.get(user, project_id)
    ProjectService.validate_open_status_for_edit(project)

    for attr, value in data.dict(exclude_unset=True).items():
      setattr(project, attr, value)

    project.save()
    return project

  @staticmethod
  def update_financials(project: Project) -> Project:
    """
    Calcula profitability e hour_profitability do projeto através dos registros de finanças e actual_cost.
    Sendo profitability = actual_cost + gains - expenses
    E hour_profitability = profitability / hours
    """
    from apps.finances.models import Finance, FinGroup
    from django.db.models import Sum, Q
    from decimal import Decimal

    # Resolve gains/expenses from Task.finance (FinGroup PROJECT)
    group = FinGroup.objects.filter(related_to=project.id, relation="PROJECT").first()

    gains = Decimal("0.00")
    expenses = Decimal("0.00")

    if group:
      stats = Finance.objects.filter(fingroup=group).aggregate(
        total_gain=Sum("amount", filter=Q(balance="POSITIVE")),
        total_expense=Sum("amount", filter=Q(balance="NEGATIVE")),
      )
      gains = stats["total_gain"] or Decimal("0.00")
      expenses = stats["total_expense"] or Decimal("0.00")

    # actual_cost is the base value received for the project
    base_gain = project.actual_cost or Decimal("0.00")
    project.profitability = base_gain + gains - expenses

    if project.spent_time:
      total_seconds = Decimal(str(project.spent_time.total_seconds()))
      hours = total_seconds / Decimal("3600")
      if hours > 0:
        project.hour_profitability = project.profitability / hours
      else:
        project.hour_profitability = project.profitability

    project.save()
    return project

  @staticmethod
  def close(user, project_id: str, data: ProjectCloseSchema) -> Project:
    project = ProjectService.get(user, project_id)
    if data.status not in ["CONCLUDED", "PARTIALLY_CONCLUDED", "CANCELLED"]:
      raise InvalidCloseStatusError("Invalid close status.")

    # RN03/RN04: Atualizar indicadores financeiros ao fechar
    project.actual_cost = data.actual_cost
    project.actual_deadline = data.actual_deadline
    project.spent_time = data.spent_time
    ProjectService.update_financials(project)

    project.status = data.status
    project.closed_at = timezone.now()
    project.save()
    return project

  @staticmethod
  def reopen(user, project_id: str) -> Project:
    project = ProjectService.get(user, project_id)
    if project.status == "OPEN":
      raise ProjectAlreadyOpenError("The project is already open.")

    if not project.closed_at:
      raise ProjectNeverClosedError("The project was never closed.")

    # RN02: Um projeto fechado só pode ser reaberto em até 7 dias após a data de fechamento.
    if timezone.now() - project.closed_at > timedelta(days=7):
      raise ReopenPeriodExpiredError(
        "The project cannot be reopened because it was closed more than 7 days ago."
      )

    project.status = "OPEN"
    # Não altere nenhum outro valor além do status do projeto.
    project.save()
    return project

  @staticmethod
  def delete(user, project_id: str):
    project = ProjectService.get(user, project_id)
    project.delete()
    return {"success": True}
