"""
Routes for testing utility functions.
"""

from ninja import Router
from django.http import HttpRequest, JsonResponse
from apps.core.utils.cache import cache_route
import time

router = Router()


@router.get("cache-route")
@cache_route
def test_cache_route(request: HttpRequest, value: str):
  """A simple route to test the cache_route decorator."""
  return JsonResponse({"timestamp": time.time(), "value": value})
