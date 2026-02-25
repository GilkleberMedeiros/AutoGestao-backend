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
  exc = exc.with_traceback()

  # In production, return a generic error message without the exception details
  return api.create_response(request, res if not settings.DEBUG else exc, status=500)


api.add_router("users/auth/", router="apps.authentication.routes.router")
