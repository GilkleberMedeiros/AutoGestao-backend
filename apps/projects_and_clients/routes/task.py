from ninja import Router

from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.schemas.task import (
  TaskSchema,
  CreateTaskReq,
  UpdateTaskReq,
  PartialUpdateTaskReq,
)
from apps.projects_and_clients.services.task import (
  TaskService,
  ProjectNotFoundError,
  MovGroupNotFoundError,
)
from apps.core.utils.paginate import paginate_route
from apps.core.schemas.response import BaseAPIResponse, PaginatedAPIResponse


router = Router()


@router.post("/{project_id}/tasks", response={201: TaskSchema, 404: BaseAPIResponse})
def create_task(request, project_id: str, data: CreateTaskReq):
  # request.user comes authenticated by JWTAuthenticationMiddlware

  try:
    created = TaskService.create(request.user, project_id, data)
  except ProjectNotFoundError:
    return 404, {
      "details": "Project associated with task wasn't found",
      "success": False,
    }
  except MovGroupNotFoundError:
    return 404, {
      "details": "Movimentation group associated with movimentation, associated with Task wasn't found",
      "success": False,
    }

  return 201, created


@router.get(
  "/{project_id}/tasks",
  response={
    200: PaginatedAPIResponse[TaskSchema],
    404: BaseAPIResponse,
  },
)
@paginate_route
def list_tasks(request, project_id: str):
  tasks = TaskService.list(request.user, project_id)

  return 200, tasks.order_by("-created_at")


@router.get(
  "/{project_id}/tasks/{task_id}",
  response={
    200: TaskSchema,
    404: BaseAPIResponse,
  },
)
def get_task(request, task_id: str, project_id: str):
  try:
    task = TaskService.get(request.user, task_id, project_id)
  except ResourceNotFoundError:
    return 404, {
      "details": "Task associated with project wasn't found",
      "success": False,
    }

  return 200, task


@router.put(
  "/{project_id}/tasks/{task_id}",
  response={200: TaskSchema, 404: BaseAPIResponse},
)
def update_task(request, task_id: str, project_id: str, data: UpdateTaskReq):
  try:
    updated = TaskService.update(request.user, task_id, project_id, data)
  except ResourceNotFoundError:
    return 404, {
      "details": "Task associated with project wasn't found",
      "success": False,
    }

  return 200, updated


@router.patch(
  "/{project_id}/tasks/{task_id}",
  response={200: TaskSchema, 404: BaseAPIResponse},
)
def partial_update_task(
  request, task_id: str, project_id: str, data: PartialUpdateTaskReq
):
  try:
    updated = TaskService.partial_update(request.user, task_id, project_id, data)
  except ResourceNotFoundError:
    return 404, {
      "details": "Task associated with project wasn't found",
      "success": False,
    }

  return 200, updated


@router.delete(
  "/{project_id}/tasks/{task_id}", response={200: BaseAPIResponse, 404: BaseAPIResponse}
)
def delete_task(request, task_id: str, project_id: str):
  try:
    TaskService.delete(request.user, task_id, project_id)
  except ResourceNotFoundError:
    return 404, {
      "details": "Either Task associated with project or Movimentation associated with Task wasn't found",
      "success": False,
    }

  return 200, {"success": True, "details": "Task deleted successfully."}
