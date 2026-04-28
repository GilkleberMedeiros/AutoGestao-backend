from unittest import TestCase
from unittest.mock import MagicMock, patch
import uuid

from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.services.emails import ClientEmailService


class TestClientEmailService_Create(TestCase):
  @patch("apps.projects_and_clients.services.emails.ClientEmail")
  @patch("apps.projects_and_clients.services.emails.Client")
  def test_create_email_success(self, MockClient, MockClientEmail):
    """create method successfully adds an email to a client."""
    user_mock = MagicMock()
    client_mock = MagicMock()
    client_mock.id = "test-client-id"
    MockClient.objects.filter.return_value.first.return_value = client_mock

    email_mock = MagicMock()
    email_mock.email = "new@example.com"
    email_mock.client = client_mock
    MockClientEmail.objects.create.return_value = email_mock

    data = {"email": "new@example.com"}
    email = ClientEmailService.create("test-client-id", data, user_mock)

    self.assertEqual(email.email, "new@example.com")
    self.assertEqual(email.client, client_mock)
    MockClient.objects.filter.assert_called_once_with(id="test-client-id", user=user_mock)
    MockClientEmail.objects.create.assert_called_once_with(client=client_mock, email="new@example.com")

  @patch("apps.projects_and_clients.services.emails.Client")
  def test_create_email_fails_invalid_client(self, MockClient):
    """create method fails when client_id is invalid."""
    user_mock = MagicMock()
    MockClient.objects.filter.return_value.first.return_value = None

    invalid_id = str(uuid.uuid4())
    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.create(invalid_id, {"email": "test@example.com"}, user_mock)
    MockClient.objects.filter.assert_called_once_with(id=invalid_id, user=user_mock)

  @patch("apps.projects_and_clients.services.emails.Client")
  def test_create_email_fails_unauthorized(self, MockClient):
    """create method fails when client does not belong to the user."""
    user_mock = MagicMock()
    MockClient.objects.filter.return_value.first.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.create("test-client-id", {"email": "test@example.com"}, user_mock)
    MockClient.objects.filter.assert_called_once_with(id="test-client-id", user=user_mock)


class TestClientEmailService_List(TestCase):
  @patch("apps.projects_and_clients.services.emails.Client")
  def test_list_emails_success(self, MockClient):
    """list method successfully returns all emails for a specific client."""
    user_mock = MagicMock()
    client_mock = MagicMock()

    mock_email1 = MagicMock()
    mock_email1.email = "e1@example.com"
    mock_email2 = MagicMock()
    mock_email2.email = "e2@example.com"

    mock_qs = MagicMock()
    mock_qs.count.return_value = 2
    mock_qs.__iter__.return_value = [mock_email1, mock_email2]
    client_mock.emails.all.return_value = mock_qs

    MockClient.objects.filter.return_value.first.return_value = client_mock

    results = ClientEmailService.list("test-client-id", user_mock)

    self.assertEqual(results.count(), 2)
    emails = [e.email for e in results]
    self.assertIn("e1@example.com", emails)
    self.assertIn("e2@example.com", emails)
    MockClient.objects.filter.assert_called_once_with(id="test-client-id", user=user_mock)
    client_mock.emails.all.assert_called_once()

  @patch("apps.projects_and_clients.services.emails.Client")
  def test_list_emails_fails_invalid_client(self, MockClient):
    """list method fails when client_id is invalid."""
    user_mock = MagicMock()
    MockClient.objects.filter.return_value.first.return_value = None

    invalid_id = str(uuid.uuid4())
    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.list(invalid_id, user_mock)

  @patch("apps.projects_and_clients.services.emails.Client")
  def test_list_emails_fails_unauthorized(self, MockClient):
    """list method fails when client does not belong to the user."""
    user_mock = MagicMock()
    MockClient.objects.filter.return_value.first.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.list("test-client-id", user_mock)


class TestClientEmailService_Update(TestCase):
  @patch("apps.projects_and_clients.services.emails.ClientEmail")
  def test_update_email_success(self, MockClientEmail):
    """update method successfully updates a specific email."""
    user_mock = MagicMock()
    email_mock = MagicMock()
    email_mock.email = "old@example.com"

    MockClientEmail.objects.filter.return_value.first.return_value = email_mock

    data = {"email": "updated@example.com"}
    updated = ClientEmailService.update("test-email-id", data, user_mock)

    self.assertEqual(updated.email, "updated@example.com")
    email_mock.save.assert_called_once()
    MockClientEmail.objects.filter.assert_called_once_with(id="test-email-id", client__user=user_mock)

  @patch("apps.projects_and_clients.services.emails.ClientEmail")
  def test_update_email_fails_unauthorized(self, MockClientEmail):
    """update method fails when email belongs to another user's client."""
    user_mock = MagicMock()
    MockClientEmail.objects.filter.return_value.first.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.update("test-email-id", {"email": "fail@example.com"}, user_mock)


class TestClientEmailService_Delete(TestCase):
  @patch("apps.projects_and_clients.services.emails.ClientEmail")
  def test_delete_email_success(self, MockClientEmail):
    """delete method successfully removes a specific email."""
    user_mock = MagicMock()
    email_mock = MagicMock()

    MockClientEmail.objects.filter.return_value.first.return_value = email_mock

    result = ClientEmailService.delete("test-email-id", user_mock)

    self.assertTrue(result)
    email_mock.delete.assert_called_once()
    MockClientEmail.objects.filter.assert_called_once_with(id="test-email-id", client__user=user_mock)

  @patch("apps.projects_and_clients.services.emails.ClientEmail")
  def test_delete_email_fails_unauthorized(self, MockClientEmail):
    """delete method fails when email belongs to another user's client."""
    user_mock = MagicMock()
    MockClientEmail.objects.filter.return_value.first.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.delete("test-email-id", user_mock)
