from django.utils import timezone
from apps.projects_and_clients.models import Project, Client, Task
from apps.projects_and_clients.schemas.project import (
  CreateProjectReq,
  UpdateProjectReq,
  PartialUpdateProjectReq,
  ProjectFilterSchema,
  ProjectCloseSchema,
)
from apps.core.exceptions import ResourceNotFoundError, BusinessRuleError
from datetime import timedelta


class ProjectClosedForEditError(BusinessRuleError):
  pass


class InvalidCloseStatusError(BusinessRuleError):
  pass


class ProjectAlreadyOpenError(BusinessRuleError):
  pass


class ProjectAlreadyClosedError(BusinessRuleError):
  pass


class ProjectNeverClosedError(BusinessRuleError):
  pass


class ReopenPeriodExpiredError(BusinessRuleError):
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
      labor_fee=data.labor_fee,
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

    for attr, value in data.model_dump(exclude_unset=True).items():
      setattr(project, attr, value)

    project.save()
    return project

  @staticmethod
  def partial_update(user, project_id: str, data: PartialUpdateProjectReq) -> Project:
    project = ProjectService.get(user, project_id)
    ProjectService.validate_open_status_for_edit(project)

    for attr, value in data.model_dump(exclude_unset=True).items():
      setattr(project, attr, value)

    project.save()
    return project

  @staticmethod
  def calculate_profitability(project: Project) -> Project:
    # project.labor_fee + (sum(Task.gains) - sum(Task.costs))
    tasks = Task.objects.filter(project=project).prefetch_related("movimentation")
    # if task has movimentation, sum its value calling Movimentation.get_movimentation_value()
    tasks_value = sum(
      [
        task.movimentation.get_movimentation_value()
        for task in tasks
        if task.movimentation
      ]
    )
    project.profitability = float(project.labor_fee) + tasks_value
    return project

  @staticmethod
  def calculate_hour_profitability(project: Project) -> Project:
    """
    Gives hour_profitability per hour.
    """
    # project.profitability / project.spent_time
    project.hour_profitability = float(project.profitability) / (
      project.spent_time.total_seconds() / 3600  # Convert seconds to hours
    )
    return project

  @staticmethod
  def close(user, project_id: str, data: ProjectCloseSchema) -> Project:
    project = ProjectService.get(user, project_id)
    if project.status != "OPEN":
      raise ProjectAlreadyClosedError("The project is already closed.")

    if data.status not in ["CONCLUDED", "PARTIALLY_CONCLUDED", "CANCELLED"]:
      raise InvalidCloseStatusError("Invalid close status.")

    project.actual_cost = float(data.actual_cost)
    project.actual_deadline = data.actual_deadline
    project.spent_time = data.spent_time

    ProjectService.calculate_profitability(project)
    ProjectService.calculate_hour_profitability(project)

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
