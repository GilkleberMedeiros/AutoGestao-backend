"""
User data caching utils.
"""

from django.core.cache import caches, CacheKeyWarning
from django.http import HttpRequest

from apps.users.models import User

from typing import Any, Callable
from functools import wraps
import warnings


def _make_cache_key(user: User, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
  """Make a unique identifier for a user and view args and kwargs."""
  return f"cache_USERID:{user.id}_ARGS:{args}_KWARGS:{kwargs}"


def cache(ttl: int, cache_key: str, value: Any = None):
  """
  Args:
    ttl: time to live in seconds
    cache_key: cache key
    value: value to cache
  """
  cache_db = caches["default"]

  # Verify if value is in cache
  with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=CacheKeyWarning)
    cached_value = cache_db.get(cache_key, None)
  if cached_value is not None:
    return cached_value

  # Return None if no value to cache.
  if value is None:
    return None

  with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=CacheKeyWarning)
    cache_db.set(cache_key, value, ttl)
  return value


def cache_route(func: Callable[[Any], Any] = None, ttl: int = 60 * 5):
  """
  Decorator to cache a route. It caches responses for a specific user.
  Requires the request object to have a user attribute with id attribute.

  Args:
    func: The function to cache
    ttl: The time to live in seconds

  Returns:
    The cached value or the function response value.
  """

  def decorator(f: Callable[[Any], Any]):
    @wraps(f)
    def wrapper(request: HttpRequest, *args, **kwargs):
      # Don't use cache if the request has "no-cache".
      if "no-cache" in request.headers.get("Cache-Control", ""):
        response = f(request, *args, **kwargs)
        return response

      cache_key = _make_cache_key(request.user, args, kwargs)
      # Verify if value is in cache (don't cache if not found).
      cached_response = cache(ttl, cache_key)
      if cached_response is not None:
        return cached_response

      response = f(request, *args, **kwargs)

      # Don't cache if the response has "no-store".
      if "no-store" in response.headers.get("Cache-Control", ""):
        return response

      cached_value = cache(ttl, cache_key, response)
      return cached_value if cached_value is not None else response

    return wrapper

  if func is None:
    return decorator
  if callable(func):
    return decorator(func)
  return decorator
