from django.utils import timezone

from apps.projects_and_clients.schemas.task import (
  CreateTaskReq,
  UpdateTaskReq,
  PartialUpdateTaskReq,
)
from apps.projects_and_clients.models import Task, Project
from apps.users.models import User

from apps.core.exceptions import ResourceNotFoundError


class TaskService:
  @staticmethod
  def create(user: User, project_id: str, data: CreateTaskReq) -> Task:
    data = data.model_dump(exclude_unset=True)
    if data.get("done_at") is None or not data["done_at"]:
      data["done_at"] = timezone.now()

    project = Project.objects.filter(id=project_id, user=user).first()

    if not project:
      raise ResourceNotFoundError("Project not found.")

    # TODO: add creation of movimentation model here
    # if data comes with movimentation create data (later).
    task = Task.objects.create(project=project, **data)
    task.save()

    return task

  @staticmethod
  def list(
    user: User,
    project_id: str,
  ):
    tasks = Task.objects.filter(project__user=user)
    if project_id:
      tasks = tasks.filter(project_id=project_id)

    return tasks

  @staticmethod
  def get(user: User, task_id: str, project_id: str) -> Task:
    task = Task.objects.filter(id=task_id, project__user=user).first()
    if not task:
      raise ResourceNotFoundError("Task not found.")
    if task.project.id != project_id:
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
    task.delete()
    return {"success": True}
