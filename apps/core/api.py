from config import settings

from ninja import NinjaAPI


api = NinjaAPI()


@api.get("/hello")
def hello(request):
  return {"message": "Hello, World!"}


# Exception Handlers
@api.exception_handler(Exception)
def unknown_exception_handler(request, exc: Exception):
  res = {"details": "An unknown error occurred", "success": False}

  # In production, return a generic error message without the exception details
  return api.create_response(request, res if not settings.DEBUG else exc, status=500)


# Add test routes for testing purposes
if settings.TESTING:
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
