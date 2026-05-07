from django.test import TestCase
from unittest.mock import MagicMock
from django.http import HttpRequest

from apps.core.utils.paginate import paginate_route


class TestPaginateDecorator(TestCase):
  def test_paginate_route_simple(self):
    request = HttpRequest()

    @paginate_route
    def my_view(request, page=1):
      return list(range(1, 21))

    # Test first page (default per_page=10)
    result = my_view(request, page=1)
    self.assertEqual(result["items"], list(range(1, 21)))
    self.assertEqual(result["current_page"], 1)
    self.assertEqual(result["total_count"], 20)

  def test_paginate_route_with_custom_per_page(self):
    request = HttpRequest()

    @paginate_route(per_page_default=5)
    def my_view(request, page=1):
      return list(range(1, 21))

    result = my_view(request, page=1)
    self.assertEqual(result["items"], list(range(1, 6)))
    self.assertEqual(result["total_pages"], 4)

  def test_paginate_route_captures_page_from_request(self):
    request = HttpRequest()
    request.get_full_path = MagicMock(return_value="/items?page=2")

    @paginate_route(per_page_default=5)
    def my_view(request):
      return list(range(1, 21))

    result = my_view(request)
    self.assertEqual(result["current_page"], 2)
    self.assertEqual(result["items"], list(range(6, 11)))

  def test_paginate_route_captures_per_page_from_request(self):
    request = HttpRequest()
    request.get_full_path = MagicMock(return_value="/items?per_page=100")

    @paginate_route(per_page_default=5)
    def my_view(request):
      return list(range(1, 21))

    result = my_view(request)
    self.assertEqual(result["total_count"], 20)
    self.assertEqual(result["items"], list(range(1, 21)))

  def test_paginate_route_without_parentheses(self):
    request = HttpRequest()

    @paginate_route
    def my_view(request, page=1):
      return [1, 2, 3]

    result = my_view(request, page=1)
    self.assertEqual(result["total_count"], 3)
    self.assertEqual(result["items"], [1, 2, 3])

  def test_paginate_route_with_parentheses_empty(self):
    request = HttpRequest()

    @paginate_route()
    def my_view(request, page=1):
      return [1, 2, 3]

    result = my_view(request, page=1)
    self.assertEqual(result["total_count"], 3)
