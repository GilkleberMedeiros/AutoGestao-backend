from unittest import TestCase
from unittest.mock import MagicMock, patch

from apps.users.service import (
  UserService,
  UserEmailAlreadyExistsError,
  UserPhoneAlreadyExistsError,
)
from apps.users.schemas import UpdateUserReq, PartialUpdateUserReq


class BaseUserServiceTestCase(TestCase):
  @staticmethod
  def _make_user_mock(
    name: str, email: str, phone: str | None = None, is_email_valid: bool = True
  ) -> MagicMock:
    import uuid

    user_mock = MagicMock()
    user_mock.id = uuid.uuid4()
    user_mock.name = name
    user_mock.email = email
    user_mock.is_email_valid = is_email_valid
    user_mock.phone = phone

    return user_mock


class UserServiceTestCase__update(BaseUserServiceTestCase):
  def test_returns_updated_user(self):
    phone = "5584900000000"
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", phone)
    body = UpdateUserReq(name="Jhon Foe", email="jhonf@example.com", phone=phone)

    updated_user = UserService.update_user(user_mock, body)

    self.assertIsNotNone(updated_user)
    self.assertEqual(updated_user.name, "Jhon Foe")
    self.assertEqual(updated_user.email, "jhonf@example.com")
    # Assert phone didn't change
    self.assertEqual(updated_user.phone, phone)

  def test_invalidate_user_email_if_changed(self):
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", "5584900000000")
    body = UpdateUserReq(
      name="Jhon Foe", email="jhonf@example.com", phone="5584900000000"
    )

    updated_user = UserService.update_user(user_mock, body)

    self.assertEqual(updated_user.is_email_valid, False)

  def test_email_remains_valid_if_not_changed(self):
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", "5584900000000")
    body = UpdateUserReq(
      name="Jhon Foe", email="jhond@example.com", phone="5584911110000"
    )

    updated_user = UserService.update_user(user_mock, body)

    self.assertEqual(updated_user.is_email_valid, True)

  def test_update_called_save(self):
    """Test if user.save() is called to update."""
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", "5584900000000")
    body = UpdateUserReq(
      name="Jhon Foe", email="jhonf@example.com", phone="5584900000000"
    )

    UserService.update_user(user_mock, body)

    user_mock.save.assert_called_once()

  def test_update_donot_change_phone_if_not_provided(self):
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", "5584900000000")
    body = UpdateUserReq(name="Jhon Foe", email="jhonf@example.com")

    UserService.update_user(user_mock, body)

    self.assertIsNotNone(user_mock.phone)
    self.assertEqual(user_mock.phone, "5584900000000")

  @patch("apps.users.service.UserService.check_unique_constraints")
  def test_partial_update_calls_check_unique_constraints_before_update(
    self, check_mock
  ):
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", "5584900000000")
    check_mock.side_effect = UserPhoneAlreadyExistsError(
      "Provided phone is already in use."
    )
    body = PartialUpdateUserReq(
      name="Jhon Foe", email="jhonf@example.com", phone="5584900000000"
    )

    with self.assertRaises(UserPhoneAlreadyExistsError):
      UserService.partial_update_user(user_mock, body)

    check_mock.assert_called_once()
    user_mock.save.assert_not_called()


class UserServiceTestCase__partial_update(BaseUserServiceTestCase):
  def test_returns_updated_user(self):
    phone = "5584900000000"
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", phone)
    body = PartialUpdateUserReq(name="Jhon Foe", email="jhonf@example.com", phone=phone)

    updated_user = UserService.partial_update_user(user_mock, body)

    self.assertIsNotNone(updated_user)
    self.assertEqual(updated_user.name, "Jhon Foe")
    self.assertEqual(updated_user.email, "jhonf@example.com")
    # Assert phone didn't change
    self.assertEqual(updated_user.phone, phone)

  def test_invalidate_user_email_if_changed(self):
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", "5584900000000")
    body = PartialUpdateUserReq(
      name="Jhon Foe", email="jhonf@example.com", phone="5584900000000"
    )

    updated_user = UserService.partial_update_user(user_mock, body)

    self.assertEqual(updated_user.is_email_valid, False)

  def test_email_remains_valid_if_not_changed(self):
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", "5584900000000")
    body = PartialUpdateUserReq(
      name="Jhon Foe", email="jhond@example.com", phone="5584911110000"
    )

    updated_user = UserService.partial_update_user(user_mock, body)

    self.assertEqual(updated_user.is_email_valid, True)

  def test_partial_update_fields(self):
    """Test if only provided fields are updated and others remain unchanged."""
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", "5584900000000")
    body = PartialUpdateUserReq(name="Jhon Foe")

    updated_user = UserService.partial_update_user(user_mock, body)

    self.assertIsNotNone(updated_user)
    self.assertEqual(updated_user.name, "Jhon Foe")
    # Assert email and phone didn't change
    self.assertEqual(updated_user.email, "jhond@example.com")
    self.assertEqual(updated_user.phone, "5584900000000")

  def test_partial_update_called_save(self):
    """Test if user.save() is called to update."""
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", "5584900000000")
    body = PartialUpdateUserReq(
      name="Jhon Foe", email="jhonf@example.com", phone="5584900000000"
    )

    UserService.partial_update_user(user_mock, body)

    user_mock.save.assert_called_once()

  def test_partial_update_sets_phone_to_none(self):
    """Test if phone can be set to None with partial update if explicitly set."""
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", "5584900000000")
    body = PartialUpdateUserReq(phone=None)

    updated_user = UserService.partial_update_user(user_mock, body)

    self.assertIsNotNone(updated_user)
    self.assertIsNone(updated_user.phone)

  @patch("apps.users.service.UserService.check_unique_constraints")
  def test_partial_update_calls_check_unique_constraints_before_update(
    self, check_mock
  ):
    user_mock = self._make_user_mock("Jhon Doe", "jhond@example.com", "5584900000000")
    check_mock.side_effect = UserEmailAlreadyExistsError(
      "Provided email is already in use."
    )
    body = PartialUpdateUserReq(
      name="Jhon Foe", email="jhonf@example.com", phone="5584900000000"
    )

    with self.assertRaises(UserEmailAlreadyExistsError):
      UserService.partial_update_user(user_mock, body)

    check_mock.assert_called_once()
    user_mock.save.assert_not_called()


class UserServiceTestCase__check_unique_constraints(BaseUserServiceTestCase):
  @patch("apps.users.service.User")
  def test_raises_user_email_already_exists_error_if_email_already_exists(
    self, model_mock
  ):
    user_mock = self._make_user_mock("Test", "test.email@example.com", "558400110011")

    def mock_filter(**kwargs):
      qs_mock = MagicMock()
      if "email" in kwargs:
        qs_mock.exclude.return_value.count.return_value = 1
      else:
        qs_mock.exclude.return_value.count.return_value = 0
      return qs_mock

    model_mock.objects.filter.side_effect = mock_filter

    data = UpdateUserReq(
      name="Test", email="test.email@example.com", phone="5584900110011"
    )

    with self.assertRaises(UserEmailAlreadyExistsError):
      UserService.check_unique_constraints(user_mock, data)

  @patch("apps.users.service.User")
  def test_raises_user_phone_already_exists_error_if_phone_already_exists(
    self, model_mock
  ):
    user_mock = self._make_user_mock("Test", "test.email@example.com", "558400110011")

    def mock_filter(**kwargs):
      qs_mock = MagicMock()
      if "phone" in kwargs:
        qs_mock.exclude.return_value.count.return_value = 1
      else:
        qs_mock.exclude.return_value.count.return_value = 0
      return qs_mock

    model_mock.objects.filter.side_effect = mock_filter

    data = UpdateUserReq(
      name="Test", email="test.email@example.com", phone="5584900110011"
    )

    with self.assertRaises(UserPhoneAlreadyExistsError):
      UserService.check_unique_constraints(user_mock, data)

  @patch("apps.users.service.User")
  def test_excludes_request_user_by_user_id(self, model_mock):
    user_mock = self._make_user_mock("Test", "test.email@example.com", "558400110011")

    qs_mock = MagicMock()
    qs_mock.exclude.return_value.count.return_value = 0
    model_mock.objects.filter.return_value = qs_mock

    data = UpdateUserReq(
      name="Test", email="test.email@example.com", phone="5584900110011"
    )

    UserService.check_unique_constraints(user_mock, data)

    qs_mock.exclude.assert_any_call(id=user_mock.id)
    self.assertEqual(qs_mock.exclude.call_count, 2)
