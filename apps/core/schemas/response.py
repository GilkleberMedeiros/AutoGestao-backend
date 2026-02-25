from ninja import Schema


class BaseAPIResponse(Schema):
  details: str
  success: bool
