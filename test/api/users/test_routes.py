from test.api.base import AuthenticatedTestCase, APIClient
from apps.users.models import User
import json


class UserUpdateRoutesTestCase(AuthenticatedTestCase):
  URL = "/api/users"

  user_create_data = {
    "name": "testuser",
    "email": "testuser@example.com",
    "password": "testpassword",
    "phone": "5584000000000",
  }
  user_create_model = User
  login_data = {"email": "testuser@example.com", "password": "testpassword"}

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.setUpClassUser()

  def setUp(self):
    super().setUp()
    self.client = APIClient(path_prefix=self.URL)
    self.setUpAuth()

    # Set user email as valid for tests.
    self.user.is_email_valid = True
    self.user.save()

  def tearDown(self):
    self.tearDownAuth()
    super().tearDown()

  @classmethod
  def tearDownClass(cls):
    cls.tearDownClassUser()
    super().tearDownClass()

  def _get_valid_token(self):
    return self.credentials["access"]

  def _make_put_request(self, data, headers=None):
    if headers is None:
      headers = {}
    return self.client.put(
      "", data=json.dumps(data), headers=headers, content_type="application/json"
    )

  def _make_patch_request(self, data, headers=None):
    if headers is None:
      headers = {}
    return self.client.patch(
      "", data=json.dumps(data), headers=headers, content_type="application/json"
    )

  # --- PUT TESTS ---

  def test_put_success_updates_user(self):
    token = self._get_valid_token()
    data = {
      "name": "updated name",
      "email": "updated@example.com",
      "phone": "5584999999999",
    }
    res = self._make_put_request(data, {"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200)

    # Verify in DB
    self.user.refresh_from_db()
    self.assertEqual(self.user.name, "updated name")
    self.assertEqual(self.user.email, "updated@example.com")
    self.assertEqual(self.user.phone, "5584999999999")

  def test_put_success_updates_user_email_to_invalid(self):
    token = self._get_valid_token()
    data = {
      "name": "updated name",
      "email": "[EMAIL_ADDRESS]",
      "phone": "5584999999999",
    }

    res = self._make_put_request(data, {"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200)

    # Verify in DB
    self.user.refresh_from_db()
    self.assertEqual(self.user.name, "updated name")
    self.assertEqual(self.user.email, "[email_address]")
    self.assertEqual(self.user.phone, "5584999999999")
    self.assertEqual(self.user.is_email_valid, False)

  def test_put_unauthenticated_returns_401(self):
    data = {
      "name": "updated name",
      "email": "updated@example.com",
      "phone": "5584999999999",
    }
    res = self._make_put_request(data)
    self.assertEqual(res.status_code, 401)

  def test_put_donot_update_user_email_to_invalid_when_email_is_equal(self):
    self.user.is_email_valid = True
    self.user.save()
    token = self._get_valid_token()
    data = {
      "name": "updated name",
      "email": self.user.email,
      "phone": "5584999999999",
    }
    res = self._make_put_request(data, {"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200)

    self.user.refresh_from_db()
    self.assertEqual(self.user.is_email_valid, True)

  def test_put_missing_fields_validation_error(self):
    token = self._get_valid_token()
    data = {"name": "missing email and phone"}
    res = self._make_put_request(data, {"Authorization": f"Bearer {token}"})
    # Django Ninja throws 422 for pydantic schema validation errors
    self.assertEqual(res.status_code, 422)

  # --- PATCH TESTS ---

  def test_patch_success_partial_update(self):
    token = self._get_valid_token()
    old_email = self.user.email
    old_phone = self.user.phone
    data = {"name": "patched name"}
    res = self._make_patch_request(data, {"Authorization": f"Bearer {token}"})
    self.assertEqual(res.status_code, 200)

    self.user.refresh_from_db()
    self.assertEqual(self.user.name, "patched name")
    self.assertEqual(self.user.email, old_email)
    self.assertEqual(self.user.phone, old_phone)

  def test_patch_unauthenticated_returns_401(self):
    data = {"name": "u"}
    res = self._make_patch_request(data)
    self.assertEqual(res.status_code, 401)

  def test_patch_updates_user_email_to_invalid_when_email_is_different(self):
    token = self._get_valid_token()
    data = {"email": "new_patched@example.com"}

    res = self._make_patch_request(data, {"Authorization": f"Bearer {token}"})

    self.assertEqual(res.status_code, 200)
    self.user.refresh_from_db()
    self.assertEqual(self.user.email, "new_patched@example.com")
    self.assertEqual(self.user.is_email_valid, False)

  def test_patch_donot_update_user_email_to_invalid_when_email_is_equal(self):
    token = self._get_valid_token()
    data = {"email": self.user.email}
    old_email = self.user.email

    res = self._make_patch_request(data, {"Authorization": f"Bearer {token}"})

    self.assertEqual(res.status_code, 200)
    self.user.refresh_from_db()
    self.assertEqual(self.user.email, old_email)
    self.assertEqual(self.user.is_email_valid, True)

  def test_patch_donot_update_user_email_to_invalid_when_email_not_specified(self):
    token = self._get_valid_token()
    data = {"name": "just a new name"}

    res = self._make_patch_request(data, {"Authorization": f"Bearer {token}"})

    self.assertEqual(res.status_code, 200)
    self.user.refresh_from_db()
    self.assertEqual(self.user.is_email_valid, True)

  def test_patch_donot_update_user_email_to_invalid_when_email_is_empty_or_blank(self):
    token = self._get_valid_token()
    data = {"email": "   "}

    res = self._make_patch_request(data, {"Authorization": f"Bearer {token}"})

    self.assertEqual(res.status_code, 200)
    self.user.refresh_from_db()
    self.assertEqual(self.user.is_email_valid, True)
