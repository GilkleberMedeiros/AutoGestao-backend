from django.test import TestCase
from unittest.mock import MagicMock
from apps.core.utils.paginate import paginate


class TestPaginate(TestCase):
  def test_paginate_with_list(self):
    items = list(range(1, 26))

    # Test first page
    result = paginate(items, page=1, per_page=10)
    self.assertEqual(result["items"], list(range(1, 11)))
    self.assertEqual(result["current_page"], 1)
    self.assertEqual(result["total_pages"], 3)
    self.assertTrue(result["has_next"])
    self.assertFalse(result["has_prev"])
    self.assertEqual(result["total_count"], 25)

    # Test middle page
    result = paginate(items, page=2, per_page=10)
    self.assertEqual(result["items"], list(range(11, 21)))
    self.assertEqual(result["current_page"], 2)
    self.assertTrue(result["has_next"])
    self.assertTrue(result["has_prev"])

    # Test last page
    result = paginate(items, page=3, per_page=10)
    self.assertEqual(result["items"], list(range(21, 26)))
    self.assertEqual(result["current_page"], 3)
    self.assertFalse(result["has_next"])
    self.assertTrue(result["has_prev"])

  def test_paginate_empty_list(self):
    items = []
    result = paginate(items, page=1, per_page=10)
    self.assertEqual(result["items"], [])
    self.assertEqual(result["current_page"], 1)
    self.assertEqual(result["total_pages"], 1)
    self.assertFalse(result["has_next"])
    self.assertFalse(result["has_prev"])
    self.assertEqual(result["total_count"], 0)

  def test_paginate_out_of_range_page(self):
    items = list(range(1, 11))

    result = paginate(items, page=5, per_page=5)
    self.assertEqual(result["current_page"], 2)
    self.assertEqual(result["items"], list(range(6, 11)))

  def test_paginate_with_queryset_mock(self):
    from django.db.models import QuerySet

    qs = MagicMock(spec=QuerySet)
    qs.count.return_value = 20
    qs.__len__.return_value = 20

    qs.__getitem__.side_effect = lambda s: list(range(1, 21))[s]

    result = paginate(qs, page=1, per_page=5)
    self.assertEqual(result["total_count"], 20)
    self.assertEqual(result["items"], [1, 2, 3, 4, 5])
    self.assertEqual(result["total_pages"], 4)
