from ninja import Router

from apps.core.schemas.response import BaseAPIResponse, PaginatedAPIResponse
from apps.core.exceptions import ResourceNotFoundError
from apps.core.utils.paginate import paginate_route
from apps.projects_and_clients.schemas.task import (
  TaskSchema,
  CreateTaskReq,
  UpdateTaskReq,
  PartialUpdateTaskReq,
)
from apps.projects_and_clients.services.task import TaskService
from apps.projects_and_clients.services.project import ProjectClosedForEditError

router = Router()


@router.post(
  "/{project_id}/tasks",
  response={201: TaskSchema, 401: BaseAPIResponse, 403: BaseAPIResponse, 404: BaseAPIResponse},
)
def create_task(request, project_id: str, data: CreateTaskReq):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    task = TaskService.create(request.user, project_id, data)
  except ResourceNotFoundError:
    return 404, {"details": "Project not found.", "success": False}
  except ProjectClosedForEditError as e:
    return 403, {"details": str(e), "success": False}

  return 201, task


@router.get(
  "/{project_id}/tasks",
  response={200: PaginatedAPIResponse[TaskSchema], 401: BaseAPIResponse, 404: BaseAPIResponse},
)
@paginate_route(per_page=250)
def list_tasks(request, project_id: str):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    tasks = TaskService.list(request.user, project_id)
  except ResourceNotFoundError:
    return 404, {"details": "Project not found.", "success": False}

  return tasks.order_by("-created_at")


@router.get(
  "/{project_id}/tasks/{task_id}",
  response={200: TaskSchema, 401: BaseAPIResponse, 404: BaseAPIResponse},
)
def get_task(request, project_id: str, task_id: str):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    task = TaskService.get(request.user, project_id, task_id)
  except ResourceNotFoundError:
    return 404, {"details": "Task not found.", "success": False}

  return 200, task


@router.put(
  "/{project_id}/tasks/{task_id}",
  response={200: TaskSchema, 401: BaseAPIResponse, 403: BaseAPIResponse, 404: BaseAPIResponse},
)
def update_task(request, project_id: str, task_id: str, data: UpdateTaskReq):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = TaskService.update(request.user, project_id, task_id, data)
  except ResourceNotFoundError:
    return 404, {"details": "Task not found.", "success": False}
  except ProjectClosedForEditError as e:
    return 403, {"details": str(e), "success": False}

  return 200, updated


@router.patch(
  "/{project_id}/tasks/{task_id}",
  response={200: TaskSchema, 401: BaseAPIResponse, 403: BaseAPIResponse, 404: BaseAPIResponse},
)
def partial_update_task(request, project_id: str, task_id: str, data: PartialUpdateTaskReq):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    updated = TaskService.partial_update(request.user, project_id, task_id, data)
  except ResourceNotFoundError:
    return 404, {"details": "Task not found.", "success": False}
  except ProjectClosedForEditError as e:
    return 403, {"details": str(e), "success": False}

  return 200, updated


@router.delete(
  "/{project_id}/tasks/{task_id}",
  response={200: BaseAPIResponse, 401: BaseAPIResponse, 403: BaseAPIResponse, 404: BaseAPIResponse},
)
def delete_task(request, project_id: str, task_id: str):
  if not request.user.is_authenticated:
    return 401, {"details": "Unauthenticated", "success": False}

  try:
    TaskService.delete(request.user, project_id, task_id)
  except ResourceNotFoundError:
    return 404, {"details": "Task not found.", "success": False}
  except ProjectClosedForEditError as e:
    return 403, {"details": str(e), "success": False}

  return 200, {"details": "Task deleted.", "success": True}
