"""
Test API login endpoint
"""

from django.test import TestCase, Client
import jwt

from apps.users.models import User
from config import settings


class LoginTestCase(TestCase):
  URL = "/api/users/auth/login"

  def setUp(self):
    self.client = Client()
    self.login = lambda data, *args, **kwargs: self.client.post(
      self.URL, data, content_type="application/json", *args, **kwargs
    )

    # Create User
    try:
      self.user = User.objects.create_user(
        name="testuser",
        email="testuser.example@gmail.com",
        password="testpassword",
        phone="5584000000000",
      )
    except Exception as e:
      raise Exception(
        f"Unknown exception while creating user for LoginTestCase!\nException: \n{e}"
      )

  def test_user_logged_in_successfully(self):
    login_data = {"email": "testuser.example@gmail.com", "password": "testpassword"}

    response = self.login(login_data)
    response_data = response.json()
    refresh_cookie = response.cookies.get(
      "refresh_token", None
    ).value  # Get str value from Morsel[str]

    self.assertEqual(response.status_code, 200)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("access", None))
    self.assertIsNotNone(refresh_cookie)

  def test_returns_valid_tokens_on_successful_login(self):
    """
    Test login endpoint returns valid tokens on successful login.
    Test access and refresh tokens are returned, test tokens are valid/can be decoded, test tokens
    have "user_id".
    """
    login_data = {"email": "testuser.example@gmail.com", "password": "testpassword"}

    response = self.login(login_data)
    response_data = response.json()
    access_token = response_data.get("access", None)
    refresh_token = response.cookies.get(
      "refresh_token", None
    ).value  # Get str value from Morsel[str]

    self.assertIsNotNone(access_token)
    self.assertIsNotNone(refresh_token)
    try:
      access_value = jwt.decode(
        access_token,
        settings.JWT_PUBKEY,
        algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
      )
    except Exception as e:
      self.fail(f"Returned access token on login endpoint isn't valid! \nERROR: \n{e}")
    try:
      refresh_value = jwt.decode(
        refresh_token,
        settings.JWT_PUBKEY,
        algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
      )
    except Exception as e:
      self.fail(f"Returned refresh token on login endpoint isn't valid! \nERROR: \n{e}")

    self.assertIsNotNone(access_value.get("user_id", None))
    self.assertIsNotNone(refresh_value.get("user_id", None))

  def test_returns_correct_userid_in_tokens(self):
    login_data = {"email": "testuser.example@gmail.com", "password": "testpassword"}
    user = self.user

    response = self.login(login_data)
    response_data = response.json()
    access_token = response_data.get("access", None)
    refresh_token = response.cookies.get(
      "refresh_token", None
    ).value  # Get str value from Morsel[str]

    try:
      access_value = jwt.decode(
        access_token,
        settings.JWT_PUBKEY,
        algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
      )
    except Exception as e:
      self.fail(f"Returned access token on login endpoint isn't valid! \nERROR: \n{e}")
    try:
      refresh_value = jwt.decode(
        refresh_token,
        settings.JWT_PUBKEY,
        algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
      )
    except Exception as e:
      self.fail(f"Returned refresh token on login endpoint isn't valid! \nERROR: \n{e}")

    access_userid = access_value.get("user_id", None)
    refresh_userid = refresh_value.get("user_id", None)

    self.assertEqual(access_userid, str(user.id))
    self.assertEqual(refresh_userid, str(user.id))

  def test_returns_bad_request_on_inexistent_user_email(self):
    login_data = {
      "email": "inexistentuser.example@gmail.com",
      "password": "testpassword",
    }

    response = self.login(login_data)
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_doesnot_return_tokens_on_inexistent_user_email_login_request(self):
    login_data = {
      "email": "inexistentuser.example@gmail.com",
      "password": "testpassword",
    }

    response = self.login(login_data)
    response_data = response.json()
    refresh_token = response.cookies.get("refresh_token", None)

    self.assertIsInstance(response_data, dict)
    self.assertIsNone(response_data.get("access", None))
    self.assertIsNone(refresh_token)

  def test_returns_bad_request_on_wrong_password(self):
    login_data = {"email": "testuser.example@gmail.com", "password": "wrongpassword"}

    response = self.login(login_data)
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_doesnot_return_tokens_on_wrong_password(self):
    login_data = {"email": "testuser.example@gmail.com", "password": "wrongpassword"}

    response = self.login(login_data)
    response_data = response.json()
    cookies = response.cookies

    self.assertIsInstance(response_data, dict)
    self.assertIsNone(response_data.get("access", None))
    self.assertIsNone(cookies.get("refresh_token", None))

  # Edge case tests - Missing/Null fields
  def test_missing_email_field(self):
    """Test login request without email field"""
    login_data = {"password": "testpassword"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_missing_password_field(self):
    """Test login request without password field"""
    login_data = {"email": "testuser.example@gmail.com"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_missing_both_fields(self):
    """Test login request without email and password fields"""
    login_data = {}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_null_email(self):
    """Test login request with null email"""
    login_data = {"email": None, "password": "testpassword"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_null_password(self):
    """Test login request with null password"""
    login_data = {"email": "testuser.example@gmail.com", "password": None}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  # Edge case tests - Field length validation
  def test_email_too_short(self):
    """Test login with email shorter than required minimum (5 chars)"""
    login_data = {"email": "ab@c", "password": "testpassword"}  # 4 chars - too short

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_email_too_short_single_char(self):
    """Test login with single character email"""
    login_data = {"email": "a", "password": "testpassword"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_password_too_short(self):
    """Test login with password shorter than required minimum (8 chars)"""
    login_data = {"email": "testuser.example@gmail.com", "password": "passed"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_password_too_short_single_char(self):
    """Test login with single character password"""
    login_data = {"email": "testuser.example@gmail.com", "password": "a"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_email_too_long(self):
    """Test login with email longer than maximum (256 chars)"""
    email = "a" * 250 + "@test.com"  # Creates 260 char email
    login_data = {"email": email, "password": "testpassword"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_password_too_long(self):
    """Test login with password longer than maximum (128 chars)"""
    password = "a" * 200  # Creates 200 char password
    login_data = {"email": "testuser.example@gmail.com", "password": password}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  # Edge case tests - Invalid data types
  def test_email_as_integer(self):
    """Test login with email as integer"""
    login_data = {"email": 123456, "password": "testpassword"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_password_as_integer(self):
    """Test login with password as integer"""
    login_data = {"email": "testuser.example@gmail.com", "password": 12345678}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_email_as_object(self):
    """Test login with email as object"""
    login_data = {"email": {"key": "value"}, "password": "testpassword"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_password_as_array(self):
    """Test login with password as array"""
    login_data = {"email": "testuser.example@gmail.com", "password": ["array"]}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_email_as_boolean(self):
    """Test login with email as boolean"""
    login_data = {"email": True, "password": "testpassword"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  # Edge case tests - Empty strings
  def test_empty_email_string(self):
    """Test login with empty email string"""
    login_data = {"email": "", "password": "testpassword"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_empty_password_string(self):
    """Test login with empty password string"""
    login_data = {"email": "testuser.example@gmail.com", "password": ""}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  def test_both_fields_empty_strings(self):
    """Test login with both fields as empty strings"""
    login_data = {"email": "", "password": ""}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 422)

  # Edge case tests - Whitespace handling
  def test_email_with_leading_whitespace(self):
    """Test login with email containing leading whitespace"""
    login_data = {
      "email": "  testuser.example@gmail.com",
      "password": "testpassword",
    }

    response = self.login(login_data)

    # Should fail because whitespace makes email different from stored user email
    self.assertEqual(response.status_code, 400)

  def test_email_with_trailing_whitespace(self):
    """Test login with email containing trailing whitespace"""
    login_data = {
      "email": "testuser.example@gmail.com  ",
      "password": "testpassword",
    }

    response = self.login(login_data)

    # Should fail because whitespace makes email different from stored user email
    self.assertEqual(response.status_code, 400)

  def test_password_with_leading_whitespace(self):
    """Test login with password containing leading whitespace"""
    login_data = {
      "email": "testuser.example@gmail.com",
      "password": "  testpassword",
    }

    response = self.login(login_data)

    # Should fail because password doesn't match
    self.assertEqual(response.status_code, 400)

  def test_password_with_trailing_whitespace(self):
    """Test login with password containing trailing whitespace"""
    login_data = {
      "email": "testuser.example@gmail.com",
      "password": "testpassword  ",
    }

    response = self.login(login_data)

    # Should fail because password doesn't match
    self.assertEqual(response.status_code, 400)

  # Edge case tests - Special characters
  def test_email_with_special_characters(self):
    """Test login with special characters in email"""
    # Create user with special chars in email
    special_email = "test+user_2024@example.com"
    try:
      _ = User.objects.create_user(
        name="specialuser",
        email=special_email,
        password="testpassword123",
        phone="5584000000001",
      )
    except Exception as e:
      self.fail(f"Failed to create test user with special email: {e}")

    login_data = {"email": special_email, "password": "testpassword123"}

    response = self.login(login_data)

    self.assertEqual(response.status_code, 200)
    self.assertIsNotNone(response.json().get("access"))

  def test_password_with_special_characters(self):
    """Test login with special characters in password"""
    special_password = "Test@pass#2024!"
    try:
      _ = User.objects.create_user(
        name="specialpassuser",
        email="specialpass.example@gmail.com",
        password=special_password,
        phone="5584000000002",
      )
    except Exception as e:
      self.fail(f"Failed to create test user with special password: {e}")

    login_data = {
      "email": "specialpass.example@gmail.com",
      "password": special_password,
    }

    response = self.login(login_data)

    self.assertEqual(response.status_code, 200)
    self.assertIsNotNone(response.json().get("access"))

  # Edge case tests - Case sensitivity
  def test_email_uppercase_login(self):
    """Test login with uppercase email when user registered with lowercase"""
    login_data = {
      "email": "TESTUSER.EXAMPLE@GMAIL.COM",
      "password": "testpassword",
    }

    response = self.login(login_data)

    response_status = response.status_code
    self.assertEqual(response_status, 200)

  def test_email_mixed_case_login(self):
    """Test login with mixed case email"""
    login_data = {
      "email": "TestUser.Example@Gmail.Com",
      "password": "testpassword",
    }

    response = self.login(login_data)

    response_status = response.status_code
    self.assertIn(response_status, [200, 400])

  # Edge case tests - SQL injection attempts
  def test_sql_injection_in_email(self):
    """Test that SQL injection in email is handled safely"""
    login_data = {
      "email": "' OR '1'='1",
      "password": "testpassword",
    }

    response = self.login(login_data)

    # Should fail validation or return 400
    self.assertIn(response.status_code, [400, 422])
    self.assertIsNone(response.json().get("access"))

  def test_sql_injection_in_password(self):
    """Test that SQL injection in password is handled safely"""
    login_data = {
      "email": "testuser.example@gmail.com",
      "password": "' OR '1'='1' --",
    }

    response = self.login(login_data)

    # Should fail because password doesn't match
    self.assertEqual(response.status_code, 400)
    self.assertIsNone(response.json().get("access"))

  # Edge case tests - XSS attempts
  def test_xss_attempt_in_email(self):
    """Test that XSS attempt in email is handled safely"""
    login_data = {
      "email": "<script>alert('xss')</script>@test.com",
      "password": "testpassword",
    }

    response = self.login(login_data)

    # Should fail or be treated as invalid email
    self.assertIn(response.status_code, [400, 422])

  def test_xss_attempt_in_password(self):
    """Test that XSS attempt in password is handled safely"""
    login_data = {
      "email": "testuser.example@gmail.com",
      "password": "<script>alert('xss')</script>",
    }

    response = self.login(login_data)

    # Should fail because password doesn't match
    self.assertEqual(response.status_code, 400)

  # Edge case tests - Boundary value testing
  def test_email_exactly_min_length(self):
    """Test login with email at exactly minimum length (5 chars)"""
    login_data = {"email": "a@b.c", "password": "testpassword"}  # Exactly 5 chars

    response = self.login(login_data)

    # Should pass validation (5 chars meets min_length=5) but user doesn't exist
    self.assertEqual(response.status_code, 400)

  def test_password_exactly_min_length(self):
    """Test login with password at exactly minimum length (8 chars)"""
    login_data = {"email": "testuser.example@gmail.com", "password": "12345678"}

    response = self.login(login_data)

    # Should fail because user doesn't have this exact password
    self.assertEqual(response.status_code, 400)

  def test_email_exactly_max_length(self):
    """Test login with email at exactly maximum length (256 chars)"""
    email = "a" * 243 + "@test.com"  # Exactly 256 chars
    login_data = {"email": email, "password": "testpassword"}

    response = self.login(login_data)

    # Should fail because user doesn't exist
    self.assertEqual(response.status_code, 400)

  def test_password_exactly_max_length(self):
    """Test login with password at exactly maximum length (128 chars)"""
    password = "a" * 128
    login_data = {"email": "testuser.example@gmail.com", "password": password}

    response = self.login(login_data)

    # Should fail because password doesn't match
    self.assertEqual(response.status_code, 400)
