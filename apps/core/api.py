from django.conf import settings
from ninja import NinjaAPI

from apps.core.exceptions import ResourceNotFoundError


api = NinjaAPI()


@api.get("/hello")
def hello(request):
  return {"message": "Hello, World!"}


# Exception Handlers
@api.exception_handler(ResourceNotFoundError)
def resource_not_found_handler(request, exc: ResourceNotFoundError):
  return api.create_response(
    request, {"details": exc.message, "success": False}, status=404
  )


@api.exception_handler(Exception)
def unknown_exception_handler(request, exc: Exception):
  # In production, return a generic error message without the exception details
  details = str(exc) if settings.DEBUG else "An unknown error occurred"
  res = {"details": details, "success": False}
  return api.create_response(request, res, status=500)


# Add test routes for testing purposes
if settings.DEBUG or settings.TESTING:
  api.add_router(
    "test-routes/middlewares/", router="apps.core.test_routes.middlewares.router"
  )

api.add_router("users", router="apps.users.routes.router")
api.add_router("users/auth/", router="apps.authentication.routes.auth.router")
api.add_router("users/validate/", router="apps.authentication.routes.validate.router")

api.add_router("clients", router="apps.projects_and_clients.routes.client.router")
api.add_router("clients", router="apps.projects_and_clients.routes.emails.router")
api.add_router("clients", router="apps.projects_and_clients.routes.phones.router")
api.add_router("projects", router="apps.projects_and_clients.routes.project.router")
api.add_router("projects", router="apps.projects_and_clients.routes.task.router")
api.add_router("fingroups", router="apps.finances.routes.fingroup.router")
api.add_router("fingroups", router="apps.finances.routes.finance.router")
api.add_router("dashboard", router="apps.finances.routes.dashboard.router")

# Specific prefixes must come before general ones to avoid shadowing
api.add_router(
  "notifications/spending-limits",
  router="apps.notifications.routes.spending_limit_notification.router",
)
api.add_router("notifications", router="apps.notifications.routes.notification.router")
