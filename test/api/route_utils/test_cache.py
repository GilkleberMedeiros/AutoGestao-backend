"""
API tests for cache utilities.
"""

from test.api.conftest import AuthenticatedTestCase
from apps.users.models import User
import time


class CacheRouteAPITestCase(AuthenticatedTestCase):
  """
  API test case for the cache_route decorator.
  Uses a real test route defined in apps.core.test_routes.route_utils.
  """

  URL = "/api/test-routes/utils/cache-route"

  user_create_data = {
    "name": "cachetestuser",
    "email": "cachetest@example.com",
    "password": "testpassword",
    "phone": "5584000000001",
  }
  user_create_model = User
  login_data = {"email": "cachetest@example.com", "password": "testpassword"}

  def test_cache_route_caching(self):
    """Test that the route is cached on subsequent requests."""
    access_token = self.credentials["access"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # First request - should hit view and cache the result
    response1 = self.client.get("", data={"value": "same"}, headers=headers)
    self.assertEqual(response1.status_code, 200)
    data1 = response1.json()
    ts1 = data1["timestamp"]
    self.assertEqual(data1["value"], "same")

    # Small delay to ensure that if it wasn't cached, the timestamp would definitely change
    time.sleep(0.01)

    # Second request - should hit cache and return the same timestamp
    response2 = self.client.get("", data={"value": "same"}, headers=headers)
    self.assertEqual(response2.status_code, 200)
    data2 = response2.json()
    ts2 = data2["timestamp"]

    self.assertEqual(ts1, ts2, "Timestamp should be identical due to caching")

  def test_cache_route_no_cache_header(self):
    """Test that Cache-Control: no-cache bypasses the cache."""
    access_token = self.credentials["access"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # First request
    response1 = self.client.get("", data={"value": "nocache"}, headers=headers)
    ts1 = response1.json()["timestamp"]

    # Second request with no-cache - should bypass cache and update
    time.sleep(0.01)
    response2 = self.client.get(
      "", data={"value": "nocache"}, headers={**headers, "Cache-Control": "no-cache"}
    )
    ts2 = response2.json()["timestamp"]

    self.assertNotEqual(ts1, ts2, "Timestamp should change with no-cache header")

  def test_cache_route_different_users(self):
    """Test that cache is unique per user."""
    # User 1 (already set up by setUpClassAuth)
    access_token1 = self.credentials["access"]
    response1 = self.client.get(
      "", data={"value": "user-test"}, headers={"Authorization": f"Bearer {access_token1}"}
    )
    ts1 = response1.json()["timestamp"]

    # Create and login User 2
    user2_data = {
      "name": "cachetestuser2",
      "email": "cachetest2@example.com",
      "password": "testpassword",
      "phone": "5584000000002",
    }
    User.objects.create_user(**user2_data)
    client2 = self.client_class()
    login_response = client2.post(
      "/api/users/auth/login",
      {"email": "cachetest2@example.com", "password": "testpassword"},
    )
    access_token2 = login_response.json()["access"]

    # Request from User 2 - should NOT get User 1's cached response
    response2 = self.client.get(
      "", data={"value": "user-test"}, headers={"Authorization": f"Bearer {access_token2}"}
    )
    data2 = response2.json()
    ts2 = data2["timestamp"]
    
    user2 = User.objects.get(email="cachetest2@example.com")
    self.assertNotEqual(ts1, ts2, f"Different users should have different cache keys. User1: {self.user.id}, User2: {user2.id}")

  def test_cache_route_different_params(self):
    """Test that cache is unique per query parameters."""
    access_token = self.credentials["access"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Request with value A
    response1 = self.client.get("", data={"value": "A"}, headers=headers)
    ts1 = response1.json()["timestamp"]

    # Request with value B - should NOT hit cache for A
    response2 = self.client.get("", data={"value": "B"}, headers=headers)
    ts2 = response2.json()["timestamp"]

    self.assertNotEqual(ts1, ts2, "Different parameters should have different cache keys")
