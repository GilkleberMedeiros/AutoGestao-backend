from django.test import TestCase
from apps.core.utils.paginate import paginate_route


class TestPaginateDecorator(TestCase):
  def test_paginate_route_simple(self):
    @paginate_route
    def my_view(page=1):
      return list(range(1, 21))

    # Test first page (default per_page=10)
    result = my_view(page=1)
    self.assertEqual(result["items"], list(range(1, 11)))
    self.assertEqual(result["current_page"], 1)
    self.assertEqual(result["total_count"], 20)

  def test_paginate_route_with_custom_per_page(self):
    @paginate_route(per_page=5)
    def my_view(page=1):
      return list(range(1, 21))

    result = my_view(page=1)
    self.assertEqual(result["items"], list(range(1, 6)))
    self.assertEqual(result["total_pages"], 4)

  def test_paginate_route_captures_page_from_kwargs(self):
    @paginate_route(per_page=5)
    def my_view(**kwargs):
      return list(range(1, 21))

    result = my_view(page=2)
    self.assertEqual(result["current_page"], 2)
    self.assertEqual(result["items"], list(range(6, 11)))

  def test_paginate_route_without_parentheses(self):
    @paginate_route
    def my_view(page=1):
      return [1, 2, 3]

    result = my_view(page=1)
    self.assertEqual(result["total_count"], 3)
    self.assertEqual(result["items"], [1, 2, 3])

  def test_paginate_route_with_parentheses_empty(self):
    @paginate_route()
    def my_view(page=1):
      return [1, 2, 3]

    result = my_view(page=1)
    self.assertEqual(result["total_count"], 3)
