from apps.projects_and_clients.schemas.task import (
  CreateTaskReq,
  UpdateTaskReq,
  PartialUpdateTaskReq,
)
from apps.projects_and_clients.models import Task, Project
from apps.finances.services.movimentation import MovimentationService
from apps.finances.schemas.movimentation import CreateMovimentationReq
from apps.finances.models import MovGroup
from apps.users.models import User

from apps.core.exceptions import ResourceNotFoundError


class ProjectNotFoundError(ResourceNotFoundError):
  pass


class MovGroupNotFoundError(ResourceNotFoundError):
  pass


class TaskService:
  @staticmethod
  def create(user: User, project_id: str, data: CreateTaskReq) -> Task:
    data = data.model_dump(exclude_unset=True)

    project = Project.objects.filter(id=project_id, user=user).first()

    if not project:
      raise ProjectNotFoundError("Project not found.")

    # if data comes with movimentation create data.
    if data.get("movimentation", None):
      movgroup = MovGroup.objects.filter(related_to=project_id, user=user).first()
      if not movgroup:
        raise MovGroupNotFoundError(
          "Movimentation Group not found for create Movimentation associated Task."
        )

      reason = f"Valor referente a atividade: {data['name']}."
      movdata = CreateMovimentationReq(**data["movimentation"], reason=reason)

      movimentation = MovimentationService.create(
        user=user, mov_group_id=movgroup.id, data=movdata
      )
      data["movimentation"] = movimentation

    # Create task
    task = Task.objects.create(project=project, **data)
    task.save()

    return task

  @staticmethod
  def list(
    user: User,
    project_id: str,
  ):
    tasks = Task.objects.filter(project=project_id, project__user=user)

    return tasks

  @staticmethod
  def get(user: User, task_id: str, project_id: str) -> Task:
    task = Task.objects.filter(id=task_id, project__user=user).first()
    if not task:
      raise ResourceNotFoundError("Task not found.")
    if str(task.project.id) != project_id:
      raise ResourceNotFoundError("Task not found in the given project.")

    return task

  @staticmethod
  def update(user: User, task_id: str, project_id: str, data: UpdateTaskReq) -> Task:
    task = TaskService.get(user, task_id, project_id)
    for attr, value in data.model_dump(exclude_unset=True).items():
      setattr(task, attr, value)
    task.save()
    return task

  @staticmethod
  def partial_update(
    user: User, task_id: str, project_id: str, data: PartialUpdateTaskReq
  ) -> Task:
    task = TaskService.get(user, task_id, project_id)
    for attr, value in data.model_dump(exclude_unset=True).items():
      setattr(task, attr, value)
    task.save()
    return task

  @staticmethod
  def delete(user: User, task_id: str, project_id: str):
    task = TaskService.get(user, task_id, project_id)
    if task.movimentation:
      task.movimentation.delete()
    task.delete()
    return {"success": True}
