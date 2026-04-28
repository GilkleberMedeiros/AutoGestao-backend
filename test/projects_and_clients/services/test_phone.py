from unittest import TestCase
from unittest.mock import MagicMock, patch
import uuid

from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.services.phones import ClientPhoneService


class TestClientPhoneService_Create(TestCase):
  @patch("apps.projects_and_clients.services.phones.ClientPhone")
  @patch("apps.projects_and_clients.services.phones.Client")
  def test_create_phone_success(self, MockClient, MockClientPhone):
    """create method successfully adds a phone to a client."""
    user_mock = MagicMock()
    client_mock = MagicMock()
    MockClient.objects.filter.return_value.first.return_value = client_mock

    created_phone_mock = MagicMock()
    created_phone_mock.phone = "5511999999999"
    created_phone_mock.client = client_mock
    MockClientPhone.objects.create.return_value = created_phone_mock

    data = {"phone": "11999999999"}
    phone = ClientPhoneService.create("test-client-id", data, user_mock)

    self.assertEqual(phone.phone, "+55 (11) 9 9999-9999")
    self.assertEqual(phone.client, client_mock)
    MockClient.objects.filter.assert_called_once_with(id="test-client-id", user=user_mock)
    MockClientPhone.objects.create.assert_called_once_with(
        client=client_mock, phone="5511999999999"
    )

  @patch("apps.projects_and_clients.services.phones.Client")
  def test_create_phone_fails_invalid_client(self, MockClient):
    """create method fails when client_id is invalid."""
    user_mock = MagicMock()
    MockClient.objects.filter.return_value.first.return_value = None

    invalid_id = str(uuid.uuid4())
    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.create(invalid_id, {"phone": "11999999999"}, user_mock)
    MockClient.objects.filter.assert_called_once_with(id=invalid_id, user=user_mock)

  @patch("apps.projects_and_clients.services.phones.Client")
  def test_create_phone_fails_unauthorized(self, MockClient):
    """create method fails when client does not belong to the user."""
    user_mock = MagicMock()
    MockClient.objects.filter.return_value.first.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.create("test-client-id", {"phone": "11999999999"}, user_mock)
    MockClient.objects.filter.assert_called_once_with(id="test-client-id", user=user_mock)


class TestClientPhoneService_List(TestCase):
  @patch("apps.projects_and_clients.services.phones.Client")
  def test_list_phones_success(self, MockClient):
    """list method successfully returns all phones for a specific client."""
    user_mock = MagicMock()
    client_mock = MagicMock()

    mock_phone1 = MagicMock()
    mock_phone1.phone = "5511911111111"
    mock_phone2 = MagicMock()
    mock_phone2.phone = "5511922222222"

    mock_qs = MagicMock()
    mock_qs.order_by.return_value = [mock_phone1, mock_phone2]
    client_mock.phones.all.return_value = mock_qs

    MockClient.objects.filter.return_value.first.return_value = client_mock

    results = ClientPhoneService.list("test-client-id", user_mock)

    self.assertEqual(len(results), 2)
    phones = [p.phone for p in results]
    self.assertIn("+55 (11) 9 1111-1111", phones)
    self.assertIn("+55 (11) 9 2222-2222", phones)
    MockClient.objects.filter.assert_called_once_with(id="test-client-id", user=user_mock)
    client_mock.phones.all.assert_called_once()

  @patch("apps.projects_and_clients.services.phones.Client")
  def test_list_phones_fails_invalid_client(self, MockClient):
    """list method fails when client_id is invalid."""
    user_mock = MagicMock()
    MockClient.objects.filter.return_value.first.return_value = None

    invalid_id = str(uuid.uuid4())
    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.list(invalid_id, user_mock)

  @patch("apps.projects_and_clients.services.phones.Client")
  def test_list_phones_fails_unauthorized(self, MockClient):
    """list method fails when client does not belong to the user."""
    user_mock = MagicMock()
    MockClient.objects.filter.return_value.first.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.list("test-client-id", user_mock)


class TestClientPhoneService_Update(TestCase):
  @patch("apps.projects_and_clients.services.phones.ClientPhone")
  def test_update_phone_success(self, MockClientPhone):
    """update method successfully updates a specific phone."""
    user_mock = MagicMock()
    phone_mock = MagicMock()
    phone_mock.phone = "5511988888888"

    MockClientPhone.objects.filter.return_value.first.return_value = phone_mock

    data = {"phone": "11977777777"}
    updated = ClientPhoneService.update("test-phone-id", data, user_mock)

    self.assertEqual(updated.phone, "+55 (11) 9 7777-7777")
    phone_mock.save.assert_called_once()
    MockClientPhone.objects.filter.assert_called_once_with(id="test-phone-id", client__user=user_mock)

  @patch("apps.projects_and_clients.services.phones.ClientPhone")
  def test_update_phone_fails_unauthorized(self, MockClientPhone):
    """update method fails when phone belongs to another user's client."""
    user_mock = MagicMock()
    MockClientPhone.objects.filter.return_value.first.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.update("test-phone-id", {"phone": "11966666666"}, user_mock)


class TestClientPhoneService_Delete(TestCase):
  @patch("apps.projects_and_clients.services.phones.ClientPhone")
  def test_delete_phone_success(self, MockClientPhone):
    """delete method successfully removes a specific phone."""
    user_mock = MagicMock()
    phone_mock = MagicMock()

    MockClientPhone.objects.filter.return_value.first.return_value = phone_mock

    result = ClientPhoneService.delete("test-phone-id", user_mock)

    self.assertTrue(result)
    phone_mock.delete.assert_called_once()
    MockClientPhone.objects.filter.assert_called_once_with(id="test-phone-id", client__user=user_mock)

  @patch("apps.projects_and_clients.services.phones.ClientPhone")
  def test_delete_phone_fails_unauthorized(self, MockClientPhone):
    """delete method fails when phone belongs to another user's client."""
    user_mock = MagicMock()
    MockClientPhone.objects.filter.return_value.first.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.delete("test-phone-id", user_mock)
