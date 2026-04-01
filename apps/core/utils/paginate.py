from django.core.paginator import Paginator
from django.db.models import QuerySet

from typing import Any, Dict, Union, Iterable, Callable
import functools


def paginate(
  items: Union[QuerySet, Iterable], page: int = 1, per_page: int = 10
) -> Dict[str, Any]:
  """
  Paginates a queryset or a simple list of items.

  Args:
      items: The queryset or list to paginate.
      page: The current page number.
      per_page: Number of elements per page.

  Returns:
      A dict with pagination metadata and the page data.
  """
  paginator = Paginator(items, per_page)

  # get_page handles out of range pages gracefully
  page_obj = paginator.get_page(page)

  return {
    "items": list(page_obj.object_list),
    "current_page": page_obj.number,
    "total_pages": paginator.num_pages,
    "has_next": page_obj.has_next(),
    "has_prev": page_obj.has_previous(),
    "total_count": paginator.count,
  }


def paginate_route(func: Callable = None, /, *, per_page: int = 10):
  def decorator(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      page = kwargs.get("page", 1)

      return paginate(func(*args, **kwargs), page, per_page)

    return wrapper

  return decorator if func is None else decorator(func)
