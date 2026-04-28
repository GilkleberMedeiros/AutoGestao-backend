from unittest import TestCase
from unittest.mock import MagicMock, patch
import uuid

from django.db.utils import IntegrityError
from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.services.client import ClientService


class TestClientService_Get(TestCase):
  @patch("apps.projects_and_clients.services.client.Client")
  def test_get_client_success_with_user(self, MockClient):
    """get method successfully returns a client when passing a valid client_id and User object."""
    mock_client = MagicMock()
    mock_client.id = "test-id"
    mock_client.name = "Client A"
    MockClient.objects.filter.return_value.first.return_value = mock_client

    user_mock = MagicMock()
    result = ClientService.get(client_id="test-id", user=user_mock)

    self.assertEqual(result.id, "test-id")
    self.assertEqual(result.name, "Client A")
    MockClient.objects.filter.assert_called_once_with(id="test-id", user=user_mock)

  @patch("apps.projects_and_clients.services.client.Client")
  def test_get_client_success_without_user(self, MockClient):
    """get method successfully returns a client when passing only the client_id."""
    mock_client = MagicMock()
    mock_client.id = "test-id"
    mock_client.name = "Client A"
    MockClient.objects.filter.return_value.first.return_value = mock_client

    result = ClientService.get(client_id="test-id")

    self.assertEqual(result.id, "test-id")
    self.assertEqual(result.name, "Client A")
    MockClient.objects.filter.assert_called_once_with(id="test-id")

  @patch("apps.projects_and_clients.services.client.Client")
  def test_get_client_not_found(self, MockClient):
    """get method returns None when passing an invalid client_id."""
    invalid_id = str(uuid.uuid4())
    MockClient.objects.filter.return_value.first.return_value = None

    result = ClientService.get(client_id=invalid_id)

    self.assertIsNone(result)
    MockClient.objects.filter.assert_called_once_with(id=invalid_id)

  @patch("apps.projects_and_clients.services.client.Client")
  def test_get_client_not_found_invalid_user(self, MockClient):
    """get method returns None when passing a valid client_id and an invalid User model."""
    MockClient.objects.filter.return_value.first.return_value = None
    user_mock = MagicMock()
    result = ClientService.get(client_id="test-id", user=user_mock)
    self.assertIsNone(result)
    MockClient.objects.filter.assert_called_once_with(id="test-id", user=user_mock)


class TestClientService_List(TestCase):
  @patch("apps.projects_and_clients.services.client.Client")
  def test_list_clients_filtered_by_user(self, MockClient):
    """list method successfully returns only clients from specific user when filtering by a User."""
    user_mock = MagicMock()
    mock_qs = MagicMock()
    MockClient.objects.all.return_value = mock_qs
    mock_qs.filter.return_value = "filtered_qs"

    results = ClientService.list(user=user_mock)

    self.assertEqual(results, "filtered_qs")
    MockClient.objects.all.assert_called_once()
    mock_qs.filter.assert_called_once_with(user=user_mock)

  @patch("apps.projects_and_clients.services.client.Client")
  def test_list_clients_no_user(self, MockClient):
    """list method successfully returns all clients when not filtering by an User."""
    MockClient.objects.all.return_value = "all_qs"

    results = ClientService.list()

    self.assertEqual(results, "all_qs")
    MockClient.objects.all.assert_called_once()

  @patch("apps.projects_and_clients.services.client.Client")
  def test_list_clients_invalid_user_returns_empty(self, MockClient):
    """list method do not returns clients when User is invalid."""
    user_mock = MagicMock()
    mock_qs = MagicMock()
    MockClient.objects.all.return_value = mock_qs
    mock_qs.filter.return_value.count.return_value = 0
    results = ClientService.list(user=user_mock)
    self.assertEqual(results.count(), 0)
    mock_qs.filter.assert_called_once_with(user=user_mock)


class TestClientService_Create(TestCase):
  @patch("apps.projects_and_clients.services.client.ClientRating")
  @patch("apps.projects_and_clients.services.client.ClientAddress")
  @patch("apps.projects_and_clients.services.client.ClientPhone")
  @patch("apps.projects_and_clients.services.client.ClientEmail")
  @patch("apps.projects_and_clients.services.client.Client")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_create_success_full_data_with_user_param(
      self, MockClient, MockClientEmail, MockClientPhone, MockClientAddress, MockClientRating
  ):
    """create method successfully creates and returns the client when receiving full data and user param."""
    mock_client = MagicMock()
    MockClient.objects.create.return_value = mock_client

    user_mock = MagicMock()
    data = {
      "name": "Full Client Param",
      "cpf": "11122233344",
      "emails": ["full1@example.com", "full2@example.com"],
      "phones": ["+5511999999999"],
      "address": {
        "state": "SP",
        "city": "Sao Paulo",
      },
      "rating": {"score": 4.5, "comment": "Great client"},
    }

    client = ClientService.create(data.copy(), user=user_mock)

    self.assertEqual(client, mock_client)
    MockClient.objects.create.assert_called_once_with(
        user=user_mock, name="Full Client Param", cpf="11122233344"
    )

    # Check bulk_create calls (they use list comprehensions, so any argument is passed)
    MockClientEmail.objects.bulk_create.assert_called_once()
    MockClientPhone.objects.bulk_create.assert_called_once()

    MockClientAddress.objects.create.assert_called_once_with(
        client=mock_client, state="SP", city="Sao Paulo"
    )
    MockClientRating.objects.create.assert_called_once_with(
        client=mock_client, score=4.5, comment="Great client"
    )

  @patch("apps.projects_and_clients.services.client.ClientPhone")
  @patch("apps.projects_and_clients.services.client.ClientEmail")
  @patch("apps.projects_and_clients.services.client.Client")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_create_success_full_data_with_user_in_data(
      self, MockClient, MockClientEmail, MockClientPhone
  ):
    """create method successfully creates and returns client when receiving full data with user within it."""
    mock_client = MagicMock()
    MockClient.objects.create.return_value = mock_client

    user_mock = MagicMock()
    data = {
      "name": "Full Client Data",
      "cpf": "55566677788",
      "user": user_mock,
      "emails": ["data@example.com"],
      "phones": ["+5511888888888"],
    }

    client = ClientService.create(data.copy())

    self.assertEqual(client, mock_client)
    MockClient.objects.create.assert_called_once_with(
        user=user_mock, name="Full Client Data", cpf="55566677788"
    )
    MockClientEmail.objects.bulk_create.assert_called_once()
    MockClientPhone.objects.bulk_create.assert_called_once()

  @patch("apps.projects_and_clients.services.client.Client")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_create_success_minimum_data_with_user_param(self, MockClient):
    """create method successfully creates and returns client when receiving minimum data and user as param."""
    mock_client = MagicMock()
    MockClient.objects.create.return_value = mock_client

    user_mock = MagicMock()
    data = {"name": "Min Client"}

    client = ClientService.create(data.copy(), user=user_mock)

    self.assertEqual(client, mock_client)
    MockClient.objects.create.assert_called_once_with(user=user_mock, name="Min Client")

  @patch("apps.projects_and_clients.services.client.Client")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_create_failure_without_user(self, MockClient):
    """create method fails if no user is provided as param or in data."""
    MockClient.objects.create.side_effect = IntegrityError
    data = {"name": "No User Client"}

    with self.assertRaises(IntegrityError):
      ClientService.create(data)


class TestClientService_Update(TestCase):
  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.ClientRating")
  @patch("apps.projects_and_clients.services.client.ClientAddress")
  @patch("apps.projects_and_clients.services.client.ClientPhone")
  @patch("apps.projects_and_clients.services.client.ClientEmail")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_update_success_full_data_with_user_param(
      self, MockClientEmail, MockClientPhone, MockClientAddress, MockClientRating, mock_get
  ):
    """update method successfully updates and return updated client model when passing user as param and full data."""
    mock_client = MagicMock()
    mock_get.return_value = mock_client

    user_mock = MagicMock()
    data = {
      "name": "Updated Name",
      "cpf": "22222222222",
      "emails": ["new@example.com", "new2@example.com"],
      "phones": ["+5511888888888"],
      "address": {
        "state": "RJ",
        "city": "New City",
      },
      "rating": {"score": 5.0, "comment": "Excellent"},
    }

    updated = ClientService.update("test-id", data.copy(), user=user_mock)

    mock_get.assert_called_once_with("test-id", user_mock)
    self.assertEqual(updated.name, "Updated Name")
    self.assertEqual(updated.cpf, "22222222222")
    mock_client.save.assert_called_once()

    MockClientEmail.objects.filter.assert_called_once_with(client=mock_client)
    MockClientEmail.objects.filter.return_value.delete.assert_called_once()
    MockClientEmail.objects.bulk_create.assert_called_once()

    MockClientPhone.objects.filter.assert_called_once_with(client=mock_client)
    MockClientPhone.objects.filter.return_value.delete.assert_called_once()
    MockClientPhone.objects.bulk_create.assert_called_once()

    MockClientAddress.objects.update_or_create.assert_called_once_with(
        client=mock_client, defaults={"state": "RJ", "city": "New City"}
    )
    MockClientRating.objects.update_or_create.assert_called_once_with(
        client=mock_client, defaults={"score": 5.0, "comment": "Excellent"}
    )

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.ClientRating")
  @patch("apps.projects_and_clients.services.client.ClientAddress")
  @patch("apps.projects_and_clients.services.client.ClientPhone")
  @patch("apps.projects_and_clients.services.client.ClientEmail")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_update_success_no_user_param(self, MockClientEmail, MockClientPhone, MockClientAddress, MockClientRating, mock_get):
    """update method successfully updates and return updated client model when not parsing user."""
    mock_client = MagicMock()
    mock_get.return_value = mock_client
    data = {"name": "Updated Name No User"}
    updated = ClientService.update("test-id", data.copy())
    mock_get.assert_called_once_with("test-id", None)
    self.assertEqual(updated.name, "Updated Name No User")
    mock_client.save.assert_called_once()

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.ClientRating")
  @patch("apps.projects_and_clients.services.client.ClientAddress")
  @patch("apps.projects_and_clients.services.client.ClientPhone")
  @patch("apps.projects_and_clients.services.client.ClientEmail")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_update_success_required_data_only(self, MockClientEmail, MockClientPhone, MockClientAddress, MockClientRating, mock_get):
    """update method successfully updates and return updated client model when passing only the required data."""
    mock_client = MagicMock()
    mock_get.return_value = mock_client
    user_mock = MagicMock()
    data = {"name": "Required Only", "cpf": "33333333333"}
    updated = ClientService.update("test-id", data.copy(), user=user_mock)
    mock_get.assert_called_once_with("test-id", user_mock)
    self.assertEqual(updated.name, "Required Only")
    self.assertEqual(updated.cpf, "33333333333")
    mock_client.save.assert_called_once()

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.ClientRating")
  @patch("apps.projects_and_clients.services.client.ClientAddress")
  @patch("apps.projects_and_clients.services.client.ClientPhone")
  @patch("apps.projects_and_clients.services.client.ClientEmail")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_update_deletes_unspecified_nested_collections(
      self, MockClientEmail, MockClientPhone, MockClientAddress, MockClientRating, mock_get
  ):
    """update method deletes nested collections that where not specified within data."""
    mock_client = MagicMock()
    mock_get.return_value = mock_client

    user_mock = MagicMock()
    data = {"name": "Rest of Fields will be Deleted"}

    updated = ClientService.update("test-id", data.copy(), user=user_mock)

    self.assertEqual(updated.name, "Rest of Fields will be Deleted")
    mock_client.save.assert_called_once()

    MockClientEmail.objects.filter.assert_called_once_with(client=mock_client)
    MockClientEmail.objects.filter.return_value.delete.assert_called_once()
    MockClientEmail.objects.bulk_create.assert_not_called()

    MockClientPhone.objects.filter.assert_called_once_with(client=mock_client)
    MockClientPhone.objects.filter.return_value.delete.assert_called_once()
    MockClientPhone.objects.bulk_create.assert_not_called()

    MockClientAddress.objects.filter.assert_called_once_with(client=mock_client)
    MockClientAddress.objects.filter.return_value.delete.assert_called_once()
    MockClientAddress.objects.update_or_create.assert_not_called()

    MockClientRating.objects.filter.assert_called_once_with(client=mock_client)
    MockClientRating.objects.filter.return_value.delete.assert_called_once()
    MockClientRating.objects.update_or_create.assert_not_called()

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.ClientRating")
  @patch("apps.projects_and_clients.services.client.ClientAddress")
  @patch("apps.projects_and_clients.services.client.ClientPhone")
  @patch("apps.projects_and_clients.services.client.ClientEmail")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_update_replaces_and_deletes_nested_collections(
      self, MockClientEmail, MockClientPhone, MockClientAddress, MockClientRating, mock_get
  ):
    """
    update method fully replace nested collections
    as well as Client data, even when specified None as data (means delete),
    instead of appending.
    """
    mock_client = MagicMock()
    mock_get.return_value = mock_client

    user_mock = MagicMock()
    rating = {"score": 0, "comment": "Deleted"}
    data = {
      "name": "Deleted Collections",
      "emails": None,
      "phones": [],
      "address": None,
      "rating": rating,
    }

    updated = ClientService.update("test-id", data.copy(), user=user_mock)

    self.assertEqual(updated.name, "Deleted Collections")
    
    MockClientEmail.objects.filter.return_value.delete.assert_called_once()
    MockClientEmail.objects.bulk_create.assert_not_called()

    MockClientPhone.objects.filter.return_value.delete.assert_called_once()
    MockClientPhone.objects.bulk_create.assert_not_called()

    MockClientAddress.objects.filter.return_value.delete.assert_called_once()
    
    MockClientRating.objects.update_or_create.assert_called_once_with(
        client=mock_client, defaults=rating
    )

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_update_fails_invalid_client_id(self, mock_get):
    """update method fails to update client model when client_id is invalid."""
    mock_get.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      ClientService.update("invalid-id", {"name": "Test"})

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_update_fails_invalid_user(self, mock_get):
    """update method fails to update client model when user is invalid."""
    mock_get.return_value = None
    user_mock = MagicMock()
    with self.assertRaises(ResourceNotFoundError):
      ClientService.update("test-id", {"name": "Test"}, user=user_mock)


class TestClientService_PartialUpdate(TestCase):
  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_partial_update_success_no_user_param(self, mock_get):
    """partial_update method successfully updates and return updated client model when not parsing user."""
    mock_client = MagicMock()
    mock_get.return_value = mock_client

    data = {"name": "Updated Name No User"}
    updated = ClientService.partial_update("test-id", data.copy())

    self.assertEqual(updated.name, "Updated Name No User")
    mock_client.save.assert_called_once()
    mock_get.assert_called_once_with("test-id", None)

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.ClientRating")
  @patch("apps.projects_and_clients.services.client.ClientAddress")
  @patch("apps.projects_and_clients.services.client.ClientPhone")
  @patch("apps.projects_and_clients.services.client.ClientEmail")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_partial_update_ignores_unspecified_nested_collections(
      self, MockClientEmail, MockClientPhone, MockClientAddress, MockClientRating, mock_get
  ):
    """partial_update method ignores a nested collection when it is not specified in given data."""
    mock_client = MagicMock()
    mock_get.return_value = mock_client

    user_mock = MagicMock()
    data = {"name": "Only Name Partial Update"}

    updated = ClientService.partial_update("test-id", data.copy(), user=user_mock)

    self.assertEqual(updated.name, "Only Name Partial Update")
    mock_client.save.assert_called_once()

    MockClientEmail.objects.filter.assert_not_called()
    MockClientPhone.objects.filter.assert_not_called()
    MockClientAddress.objects.filter.assert_not_called()
    MockClientRating.objects.filter.assert_not_called()

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.ClientRating")
  @patch("apps.projects_and_clients.services.client.ClientEmail")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_partial_update_erases_nested_collection_when_none_or_empty(
      self, MockClientEmail, MockClientRating, mock_get
  ):
    """partial_update method only erases a nested collection if it is explicitly specified within data as none or empty data."""
    mock_client = MagicMock()
    mock_get.return_value = mock_client

    user_mock = MagicMock()
    data = {
      "emails": [],  # specifies empty list, should delete all
      "rating": None,  # specifies None, should delete
    }

    ClientService.partial_update("test-id", data.copy(), user=user_mock)

    MockClientEmail.objects.filter.assert_called_once_with(client=mock_client)
    MockClientEmail.objects.filter.return_value.delete.assert_called_once()
    MockClientEmail.objects.bulk_create.assert_not_called()

    MockClientRating.objects.filter.assert_called_once_with(client=mock_client)
    MockClientRating.objects.filter.return_value.delete.assert_called_once()
    MockClientRating.objects.update_or_create.assert_not_called()

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.ClientAddress")
  @patch("apps.projects_and_clients.services.client.ClientPhone")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_partial_update_updates_only_non_required_data(
      self, MockClientPhone, MockClientAddress, mock_get
  ):
    """partial_update method can update only non-required data like nested collections."""
    mock_client = MagicMock()
    mock_get.return_value = mock_client

    user_mock = MagicMock()
    data = {
      "phones": ["+5511888888888", "+5511777777777"],
      "address": {
        "state": "RJ",
        "city": "New City",
      },
    }

    ClientService.partial_update("test-id", data.copy(), user=user_mock)

    MockClientPhone.objects.filter.assert_called_once_with(client=mock_client)
    MockClientPhone.objects.filter.return_value.delete.assert_called_once()
    MockClientPhone.objects.bulk_create.assert_called_once()

    MockClientAddress.objects.update_or_create.assert_called_once_with(
        client=mock_client, defaults={"state": "RJ", "city": "New City"}
    )

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_partial_update_fails_invalid_client_id(self, mock_get):
    mock_get.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      ClientService.partial_update("invalid-id", {"name": "Test"})

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  @patch("apps.projects_and_clients.services.client.transaction.atomic", lambda f: f)
  def test_partial_update_fails_invalid_user(self, mock_get):
    mock_get.return_value = None
    user_mock = MagicMock()
    with self.assertRaises(ResourceNotFoundError):
      ClientService.partial_update("test-id", {"name": "Test"}, user=user_mock)


class TestClientService_Delete(TestCase):
  @patch("apps.projects_and_clients.services.client.ClientService.get")
  def test_delete_success_with_user(self, mock_get):
    """delete method successfully deletes the client when passing valid client_id and user."""
    mock_client = MagicMock()
    mock_get.return_value = mock_client

    user_mock = MagicMock()
    result = ClientService.delete("test-id", user=user_mock)

    self.assertTrue(result)
    mock_get.assert_called_once_with("test-id", user_mock)
    mock_client.delete.assert_called_once()

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  def test_delete_success_no_user_param(self, mock_get):
    """delete method successfully deletes the client when passing only the client_id."""
    mock_client = MagicMock()
    mock_get.return_value = mock_client

    result = ClientService.delete("test-id")

    self.assertTrue(result)
    mock_get.assert_called_once_with("test-id", None)
    mock_client.delete.assert_called_once()

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  def test_delete_fails_invalid_client_id(self, mock_get):
    """delete method fails when client_id is invalid."""
    mock_get.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      ClientService.delete("invalid-id")

  @patch("apps.projects_and_clients.services.client.ClientService.get")
  def test_delete_fails_invalid_user(self, mock_get):
    """delete method fails when user does not own the client."""
    mock_get.return_value = None
    user_mock = MagicMock()
    with self.assertRaises(ResourceNotFoundError):
      ClientService.delete("test-id", user=user_mock)
