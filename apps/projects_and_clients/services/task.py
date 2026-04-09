from django.utils import timezone
from apps.projects_and_clients.models import Project, Task
from apps.finances.models import Finance, FinGroup
from apps.projects_and_clients.schemas.task import (
  CreateTaskReq,
  UpdateTaskReq,
  PartialUpdateTaskReq,
)
from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.services.project import (
  ProjectService,
)


class TaskService:
  @staticmethod
  def _get_project(user, project_id: str) -> Project:
    """Get and validate project belongs to user."""
    return ProjectService.get(user, project_id)

  @staticmethod
  def create(user, project_id: str, data: CreateTaskReq) -> Task:
    project = TaskService._get_project(user, project_id)
    ProjectService.validate_open_status_for_edit(project)

    # Use finance_id if finance already created by the frontend, otherwise
    # use finance_entry to create a new finance
    finance_id = data.finance_id

    if data.finance_entry:
      # Resolve FinGroup for the project (Signal ensures it exists)
      fingroup = FinGroup.objects.filter(
        user=user, related_to=project.id, relation="PROJECT"
      ).first()

      if not fingroup:
        # Fallback if signal failed or project existed before signal
        fingroup = FinGroup.objects.create(
          user=user,
          related_to=project.id,
          relation="PROJECT",
          name=f"Finanças: {project.name}",
        )

      finance = Finance.objects.create(
        fingroup=fingroup,
        amount=data.finance_entry.amount,
        balance=data.finance_entry.balance,
        reason=data.finance_entry.reason or f"Atividade: {data.name}",
        movemented_at=data.finance_entry.movemented_at or timezone.now(),
      )
      finance_id = finance.id

    task = Task.objects.create(
      project=project,
      name=data.name,
      description=data.description,
      done_at=data.done_at,
      finance_id=finance_id,
    )
    return task

  @staticmethod
  def get(user, project_id: str, task_id: str) -> Task:
    project = TaskService._get_project(user, project_id)
    task = Task.objects.filter(id=task_id, project=project).first()
    if not task:
      raise ResourceNotFoundError("Task not found.")
    return task

  @staticmethod
  def list(user, project_id: str):
    project = TaskService._get_project(user, project_id)
    return Task.objects.filter(project=project)

  @staticmethod
  def update(user, project_id: str, task_id: str, data: UpdateTaskReq) -> Task:
    project = TaskService._get_project(user, project_id)
    ProjectService.validate_open_status_for_edit(project)

    task = TaskService.get(user, project_id, task_id)
    for attr, value in data.dict(exclude={"finance_id"}).items():
      setattr(task, attr, value)

    if data.finance_id:
      task.finance_id = data.finance_id

    task.save()
    return task

  @staticmethod
  def partial_update(
    user, project_id: str, task_id: str, data: PartialUpdateTaskReq
  ) -> Task:
    project = TaskService._get_project(user, project_id)
    ProjectService.validate_open_status_for_edit(project)

    task = TaskService.get(user, project_id, task_id)
    for attr, value in data.dict(exclude_unset=True, exclude={"finance_id"}).items():
      setattr(task, attr, value)

    if data.finance_id:
      task.finance_id = data.finance_id

    task.save()
    return task

  @staticmethod
  def delete(user, project_id: str, task_id: str):
    project = TaskService._get_project(user, project_id)
    ProjectService.validate_open_status_for_edit(project)

    task = TaskService.get(user, project_id, task_id)
    task.delete()
    return {"success": True}
