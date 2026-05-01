from ninja import ModelSchema

from apps.projects_and_clients.models import Task


class TaskSchema(ModelSchema):
  class Meta:
    model = Task
    fields = [
      "id",
      "name",
      "done_at",
      "created_at",
      "updated_at",
    ]


class CreateTaskReq(ModelSchema):
  class Meta:
    model = Task
    fields = ["name", "done_at"]
    fields_optional = ["done_at"]


class UpdateTaskReq(ModelSchema):
  class Meta:
    model = Task
    fields = ["name", "done_at"]


class PartialUpdateTaskReq(ModelSchema):
  class Meta:
    model = Task
    fields = ["name", "done_at"]
    fields_optional = "__all__"
