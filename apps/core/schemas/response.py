from ninja import Schema

from typing import TypeVar, Generic

T = TypeVar("T")


class BaseAPIResponse(Schema):
  details: str
  success: bool


class PaginatedAPIResponse(Schema, Generic[T]):
  items: list[T]
  current_page: int
  total_pages: int
  has_next: bool
  has_prev: bool
  total_count: int
