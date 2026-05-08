from unittest.mock import MagicMock, patch, ANY
from django.test import SimpleTestCase
from django.http import HttpRequest, HttpResponse
from apps.core.utils.cache import cache, cache_route, _make_cache_key
from apps.users.models import User

class CacheBaseTestCase(SimpleTestCase):
    """Base test class for cache utilities."""
    def setUp(self):
        self.user = MagicMock(spec=User)
        self.user.id = 123
        
        self.request = MagicMock(spec=HttpRequest)
        self.request.user = self.user
        self.request.headers = {}
        
        self.mock_response = MagicMock(spec=HttpResponse)
        self.mock_response.headers = {}
        self.mock_response.status_code = 200


class TestMakeCacheKey(CacheBaseTestCase):
    """Tests for the _make_cache_key utility function."""
    
    def test_make_cache_key(self):
        """Test cache key generation."""
        key = _make_cache_key(self.user, (1,), {"a": 2})
        self.assertIn("USERID:123", key)
        self.assertIn("ARGS:(1,)", key)
        self.assertIn("KWARGS:{'a': 2}", key)


class TestCacheFunction(CacheBaseTestCase):
    """Tests for the cache utility function."""

    @patch("apps.core.utils.cache.caches")
    def test_cache_function_hit(self, mock_caches):
        """Test that cache function returns cached value on hit."""
        mock_cache_db = MagicMock()
        mock_caches.__getitem__.return_value = mock_cache_db
        mock_cache_db.get.return_value = "hit"
        
        result = cache(60, "test_key")
        
        self.assertEqual(result, "hit")
        mock_cache_db.get.assert_called_with("test_key", None)
        mock_cache_db.set.assert_not_called()

    @patch("apps.core.utils.cache.caches")
    def test_cache_function_miss_and_set(self, mock_caches):
        """Test that cache function sets and returns value on miss if value provided."""
        mock_cache_db = MagicMock()
        mock_caches.__getitem__.return_value = mock_cache_db
        mock_cache_db.get.return_value = None
        
        result = cache(60, "test_key", "new_value")
        
        self.assertEqual(result, "new_value")
        mock_cache_db.set.assert_called_with("test_key", "new_value", 60)

    @patch("apps.core.utils.cache.caches")
    def test_cache_function_miss_no_value(self, mock_caches):
        """Test that cache function returns None on miss if no value provided."""
        mock_cache_db = MagicMock()
        mock_caches.__getitem__.return_value = mock_cache_db
        mock_cache_db.get.return_value = None
        
        result = cache(60, "test_key")
        
        self.assertIsNone(result)


class TestCacheRouteDecorator(CacheBaseTestCase):
    """Tests for the cache_route decorator."""

    @patch("apps.core.utils.cache.cache")
    def test_cache_route_decorator_hit(self, mock_cache):
        """Test that cache_route returns cached response on hit."""
        mock_cache.return_value = self.mock_response
        
        @cache_route
        def my_view(request):
            return "should not be called"
            
        result = my_view(self.request)
        
        self.assertEqual(result, self.mock_response)
        mock_cache.assert_called()

    @patch("apps.core.utils.cache.cache")
    def test_cache_route_decorator_miss_and_cache(self, mock_cache):
        """Test that cache_route calls function and caches result on miss."""
        # First call to cache (check) returns None
        # Second call to cache (set) returns the value
        mock_cache.side_effect = [None, self.mock_response]
        
        @cache_route
        def my_view(request):
            return self.mock_response
            
        result = my_view(self.request)
        
        self.assertEqual(result, self.mock_response)
        # Verify it was called twice (once for check, once for set)
        self.assertEqual(mock_cache.call_count, 2)

    @patch("apps.core.utils.cache.cache")
    def test_cache_route_no_cache_request_header(self, mock_cache):
        """Test that cache_route respects Cache-Control: no-cache in request."""
        self.request.headers = {"Cache-Control": "no-cache"}
        
        @cache_route
        def my_view(request):
            return self.mock_response
            
        result = my_view(self.request)
        
        self.assertEqual(result, self.mock_response)
        # Should NOT call cache at all because of early return
        mock_cache.assert_not_called()

    @patch("apps.core.utils.cache.cache")
    def test_cache_route_no_store_response_header(self, mock_cache):
        """Test that cache_route respects Cache-Control: no-store in response."""
        mock_cache.return_value = None
        self.mock_response.headers = {"Cache-Control": "no-store"}
        
        @cache_route
        def my_view(request):
            return self.mock_response
            
        result = my_view(self.request)
        
        self.assertEqual(result, self.mock_response)
        # Should call cache once to check, but NOT call it to set because of no-store response
        self.assertEqual(mock_cache.call_count, 1)

    @patch("apps.core.utils.cache.cache")
    def test_cache_route_with_ttl_argument(self, mock_cache):
        """Test cache_route with custom TTL."""
        mock_cache.return_value = self.mock_response
        
        @cache_route(ttl=120)
        def my_view(request):
            return self.mock_response
            
        my_view(self.request)
        
        # Check that cache was called with the custom TTL
        mock_cache.assert_called_with(120, ANY)
