from ninja import Router, Query
from apps.core.exceptions import ResourceNotFoundError


from apps.core.schemas.response import BaseAPIResponse, PaginatedAPIResponse
from apps.core.utils.paginate import paginate_route
from apps.projects_and_clients.schemas.project import (
    ProjectSchema,
    CreateProjectReq,
    UpdateProjectReq,
    PartialUpdateProjectReq,
    ProjectFilterSchema,
    ProjectCloseSchema
)
from apps.projects_and_clients.services.project import (
    ProjectService,
    ProjectClosedForEditError,
    InvalidCloseStatusError,
    ProjectAlreadyOpenError,
    ProjectNeverClosedError,
    ReopenPeriodExpiredError
)

router = Router()


@router.post("", response={201: ProjectSchema, 401: BaseAPIResponse, 404: BaseAPIResponse})
def create_project(request, data: CreateProjectReq):
    if not request.user.is_authenticated:
        return 401, {"details": "Unauthenticated", "success": False}

    try:
        created = ProjectService.create(request.user, data)
    except ResourceNotFoundError:
        return 404, {"details": "Client not found.", "success": False}

    return 201, created


@router.get("", response={200: PaginatedAPIResponse[ProjectSchema], 401: BaseAPIResponse})
@paginate_route(per_page=250)
def list_projects(request, filters: ProjectFilterSchema = Query(...)):
    if not request.user.is_authenticated:
        return 401, {"details": "Unauthenticated", "success": False}

    projects = ProjectService.list(request.user, filters)
    return projects.order_by("-created_at")


@router.get("/{project_id}", response={200: ProjectSchema, 401: BaseAPIResponse, 404: BaseAPIResponse})
def get_project(request, project_id: str):
    if not request.user.is_authenticated:
        return 401, {"details": "Unauthenticated", "success": False}

    try:
        project = ProjectService.get(request.user, project_id)
    except ResourceNotFoundError:
        return 404, {"details": f"Project with id {project_id} not found.", "success": False}

    return 200, project


@router.put("/{project_id}", response={200: ProjectSchema, 401: BaseAPIResponse, 403: BaseAPIResponse, 404: BaseAPIResponse})
def update_project(request, project_id: str, data: UpdateProjectReq):
    if not request.user.is_authenticated:
        return 401, {"details": "Unauthenticated", "success": False}

    try:
        updated = ProjectService.update(request.user, project_id, data)
    except ResourceNotFoundError:
        return 404, {"details": f"Project with id {project_id} not found.", "success": False}
    except ProjectClosedForEditError as e:
        return 403, {"details": str(e), "success": False}

    return 200, updated


@router.patch("/{project_id}", response={200: ProjectSchema, 401: BaseAPIResponse, 403: BaseAPIResponse, 404: BaseAPIResponse})
def partial_update_project(request, project_id: str, data: PartialUpdateProjectReq):
    if not request.user.is_authenticated:
        return 401, {"details": "Unauthenticated", "success": False}

    try:
        updated = ProjectService.partial_update(request.user, project_id, data)
    except ResourceNotFoundError:
        return 404, {"details": f"Project with id {project_id} not found.", "success": False}
    except ProjectClosedForEditError as e:
        return 403, {"details": str(e), "success": False}

    return 200, updated


@router.delete("/{project_id}", response={200: BaseAPIResponse, 401: BaseAPIResponse, 404: BaseAPIResponse})
def delete_project(request, project_id: str):
    if not request.user.is_authenticated:
        return 401, {"details": "Unauthenticated", "success": False}

    try:
        ProjectService.delete(request.user, project_id)
    except ResourceNotFoundError:
        return 404, {"details": f"Project with id {project_id} not found.", "success": False}

    return 200, {"details": f"Project with id {project_id} deleted.", "success": True}


@router.patch("/{project_id}/close", response={200: ProjectSchema, 400: BaseAPIResponse, 401: BaseAPIResponse, 404: BaseAPIResponse})
def close_project(request, project_id: str, data: ProjectCloseSchema):
    if not request.user.is_authenticated:
        return 401, {"details": "Unauthenticated", "success": False}

    try:
        closed = ProjectService.close(request.user, project_id, data)
    except ResourceNotFoundError:
        return 404, {"details": f"Project with id {project_id} not found.", "success": False}
    except InvalidCloseStatusError as e:
        return 400, {"details": str(e), "success": False}

    return 200, closed


@router.post("/{project_id}/reopen", response={200: ProjectSchema, 400: BaseAPIResponse, 401: BaseAPIResponse, 403: BaseAPIResponse, 404: BaseAPIResponse})
def reopen_project(request, project_id: str):
    if not request.user.is_authenticated:
        return 401, {"details": "Unauthenticated", "success": False}

    try:
        reopened = ProjectService.reopen(request.user, project_id)
    except ResourceNotFoundError:
        return 404, {"details": f"Project with id {project_id} not found.", "success": False}
    except ReopenPeriodExpiredError as e:
        return 403, {"details": str(e), "success": False}
    except (ProjectAlreadyOpenError, ProjectNeverClosedError) as e:
        return 400, {"details": str(e), "success": False}

    return 200, reopened
