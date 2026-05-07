from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import HttpRequest

from urllib.parse import urlsplit, parse_qs
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


def paginate_route(func: Callable = None, /, *, per_page_default: int = 250):
  """
  Decorator to paginate the result of a Django Ninja route.

  It applies the paginate function to the result of the decorated function.
  The paginate function should return a list of items to be paginated.

  Args:
      func: The function to paginate.
      per_page_default: The default number of items per page. The decorator also
      attempts to get the per_page and page parameters from the request object
      accessing in args[0], if args[0] is a HttpRequest instance.

  Returns:
      A dict with pagination metadata and the page data.

  Example:
      from ninja import Router
      from core.utils.paginate import paginate_route

      router = Router()

      @router.get("", response={200: PaginatedAPIResponse[ItemSchema]})
      @paginate_route(per_page_default=20)
      def list_items(request, **kwargs):
          return Item.objects.all()
  """

  def decorator(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      per_page = per_page_default
      page = 1

      request: HttpRequest = args[0]
      if isinstance(request, HttpRequest):
        path = request.get_full_path()
        qs_string = urlsplit(path).query
        qs_dict = parse_qs(qs_string)
        per_page = int(qs_dict.get("per_page", [per_page_default])[0])
        page = int(qs_dict.get("page", [1])[0])

      result = func(*args, **kwargs)

      # If the result is a tuple (status, data), we only paginate if status is 2xx
      if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], int):
        status_code, data = result
        if not (200 <= status_code < 300):
          return result
        # If it is 2xx, we paginate the data part and return it with the status
        return status_code, paginate(data, page, per_page)

      return paginate(result, page, per_page)

    return wrapper

  return decorator if func is None else decorator(func)
