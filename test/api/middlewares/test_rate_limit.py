from django.core.cache import caches

from test.api.base import AuthenticatedTestCase
from apps.users.models import User

class TestRateLimitMiddleware(AuthenticatedTestCase):
  TEST_URL = "/api/test-routes/middlewares/rate-limit-middleware/"
  
  user_create_data = {
    "name": "ratelimit_user",
    "email": "ratelimit@example.com",
    "password": "testpassword",
    "phone": "5511911111111",
  }
  user_create_model = User
  login_data = {"email": "ratelimit@example.com", "password": "testpassword"}

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()
    cls.setUpClassAuth()

  @classmethod
  def tearDownClass(cls):
    cls.tearDownClassAuth()
    cls.tearDownClassUser()
    super().tearDownClass()

  def setUp(self):
    self.cache = caches["default"]
    self.cache.clear()

  def test_rate_limit_success_then_fail(self):
    # First request should pass
    response = self.client.get(
      self.TEST_URL, HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}"
    )
    self.assertEqual(response.status_code, 200)
    
    # Immediate second request should fail due to rate limit
    response2 = self.client.get(
      self.TEST_URL, HTTP_AUTHORIZATION=f"Bearer {self.credentials['access']}"
    )
    self.assertEqual(response2.status_code, 429)
    self.assertIn("Too Many Requests", response2.json().get("details", ""))

  def test_rate_limit_unauthenticated(self):
    self.cache.clear()
    
    # First request using IP
    response = self.client.get(self.TEST_URL, REMOTE_ADDR='1.2.3.4')
    self.assertEqual(response.status_code, 200)
    
    # Second request from same IP should fail
    response2 = self.client.get(self.TEST_URL, REMOTE_ADDR='1.2.3.4')
    self.assertEqual(response2.status_code, 429)

    # Request from different IP should pass
    response3 = self.client.get(self.TEST_URL, REMOTE_ADDR='5.6.7.8')
    self.assertEqual(response3.status_code, 200)
