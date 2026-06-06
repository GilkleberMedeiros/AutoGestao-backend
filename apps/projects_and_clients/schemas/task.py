from ninja import ModelSchema

from apps.projects_and_clients.models import Task
from apps.finances.models import Movimentation


class MovimentationInTaskSchema(ModelSchema):
  class Meta:
    model = Movimentation
    fields = ["id", "amount", "balance", "reason", "movemented_at"]


class TaskSchema(ModelSchema):
  class Meta:
    model = Task
    fields = [
      "id",
      "name",
      "do_at",
      "is_done",
      "created_at",
      "updated_at",
    ]

  movimentation: MovimentationInTaskSchema | None = None


class MovimentationInTaskCreate(ModelSchema):
  class Meta:
    model = Movimentation
    fields = ["amount", "balance"]


class CreateTaskReq(ModelSchema):
  class Meta:
    model = Task
    fields = ["name", "do_at"]

  movimentation: MovimentationInTaskCreate | None = None


class UpdateTaskReq(ModelSchema):
  class Meta:
    model = Task
    fields = ["name", "do_at"]


class PartialUpdateTaskReq(ModelSchema):
  class Meta:
    model = Task
    fields = ["name", "do_at"]
    fields_optional = "__all__"
