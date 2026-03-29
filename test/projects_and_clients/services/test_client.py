import uuid
from django.test import TestCase
from django.http import Http404

from apps.users.models import User
from apps.projects_and_clients.models import (
  Client,
  ClientEmail,
  ClientPhone,
  ClientAddress,
  ClientRating,
)
from apps.projects_and_clients.services.client import ClientService


class TestClientService_Get(TestCase):
  @classmethod
  def setUpClass(cls):
    cls.user = User.objects.create_user(
      name="Test User", email="test@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Other User", email="other@example.com", password="password123"
    )
    cls.client_obj = Client.objects.create(
      user=cls.user, name="Client A", cpf="12345678901"
    )

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    cls.other_user.delete()
    cls.client_obj.delete()

  def test_get_client_success_with_user(self):
    """get method successfully returns a client when passing a valid client_id and User object."""
    result = ClientService.get(client_id=str(self.client_obj.id), user=self.user)
    self.assertEqual(result.id, self.client_obj.id)
    self.assertEqual(result.name, "Client A")

  def test_get_client_success_without_user(self):
    """get method successfully returns a client when passing only the client_id."""
    result = ClientService.get(client_id=str(self.client_obj.id))
    self.assertEqual(result.id, self.client_obj.id)
    self.assertEqual(result.name, "Client A")

  def test_get_client_not_found_invalid_id(self):
    """get method returns 404 http error when passing an invalid client_id."""
    invalid_id = str(uuid.uuid4())
    with self.assertRaises(Http404):
      ClientService.get(client_id=invalid_id)

  def test_get_client_not_found_invalid_user(self):
    """get method returns 404 http error when passing a valid client_id and an invalid User model."""
    with self.assertRaises(Http404):
      ClientService.get(client_id=str(self.client_obj.id), user=self.other_user)


class TestClientService_List(TestCase):
  @classmethod
  def setUpClass(cls):
    cls.user1 = User.objects.create_user(
      name="User 1", email="user1@example.com", password="password123"
    )
    cls.user2 = User.objects.create_user(
      name="User 2", email="user2@example.com", password="password123"
    )
    cls.user_without_clients = User.objects.create_user(
      name="Empty User", email="empty@example.com", password="password123"
    )

    cls.client1 = Client.objects.create(user=cls.user1, name="Client 1")
    cls.client2 = Client.objects.create(user=cls.user1, name="Client 2")
    cls.client3 = Client.objects.create(user=cls.user2, name="Client 3")

  @classmethod
  def tearDownClass(cls):
    cls.user1.delete()
    cls.user2.delete()
    cls.user_without_clients.delete()
    cls.client1.delete()
    cls.client2.delete()
    cls.client3.delete()

  def test_list_clients_filtered_by_user(self):
    """list method successfully returns only clients from specific user when filtering by a User."""
    results = ClientService.list(user=self.user1)
    self.assertEqual(results.count(), 2)
    self.assertIn(self.client1, results)
    self.assertIn(self.client2, results)
    self.assertNotIn(self.client3, results)

  def test_list_clients_no_user(self):
    """list method successfully returns all clients when not filtering by an User."""
    results = ClientService.list()
    self.assertEqual(results.count(), 3)
    self.assertIn(self.client1, results)
    self.assertIn(self.client2, results)
    self.assertIn(self.client3, results)

  def test_list_clients_invalid_user_returns_empty(self):
    """list method do not returns clients when User is invalid."""
    results = ClientService.list(user=self.user_without_clients)
    self.assertEqual(results.count(), 0)


class TestClientService_Create(TestCase):
  @classmethod
  def setUpClass(cls):
    cls.user = User.objects.create_user(
      name="Create Test User", email="create@example.com", password="password123"
    )

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()

  def test_create_success_full_data_with_user_param(self):
    """create method successfully creates and returns the client when receiving full data and user param."""
    data = {
      "name": "Full Client Param",
      "cpf": "11122233344",
      "emails": ["full1@example.com", "full2@example.com"],
      "phones": ["+5511999999999"],
      "address": {
        "state": "SP",
        "city": "Sao Paulo",
        "neighborhood": "Centro",
        "street": "Rua A",
        "house_number": "123",
      },
      "rating": {"score": 4.5, "comment": "Great client"},
    }
    client = ClientService.create(data, user=self.user)

    self.assertEqual(client.name, "Full Client Param")
    self.assertEqual(client.user, self.user)
    self.assertEqual(client.clientemail_set.count(), 2)
    self.assertEqual(client.clientphone_set.count(), 1)
    self.assertTrue(hasattr(client, "clientaddress"))
    self.assertTrue(hasattr(client, "clientrating"))

  def test_create_success_full_data_with_user_in_data(self):
    """create method successfully creates and returns client when receiving full data with user within it."""
    data = {
      "name": "Full Client Data",
      "cpf": "55566677788",
      "user": self.user,
      "emails": ["data@example.com"],
      "phones": ["+5511888888888"],
    }
    client = ClientService.create(data)

    self.assertEqual(client.name, "Full Client Data")
    self.assertEqual(client.user, self.user)
    self.assertEqual(client.clientemail_set.count(), 1)
    self.assertEqual(client.clientphone_set.count(), 1)

  def test_create_success_minimum_data_with_user_param(self):
    """create method successfully creates and returns client when receiving minimum data and user as param."""
    data = {"name": "Min Client"}
    client = ClientService.create(data, user=self.user)

    self.assertEqual(client.name, "Min Client")
    self.assertEqual(client.user, self.user)
    self.assertEqual(client.clientemail_set.count(), 0)
    self.assertEqual(client.clientphone_set.count(), 0)
    self.assertFalse(hasattr(client, "clientaddress"))
    self.assertFalse(hasattr(client, "clientrating"))

  def test_create_failure_without_user(self):
    """create method fails if no user is provided as param or in data."""
    data = {"name": "No User Client"}
    from django.db.utils import IntegrityError

    with self.assertRaises(IntegrityError):
      ClientService.create(data)


class TestClientService_Update(TestCase):
  @classmethod
  def setUpClass(cls):
    cls.user = User.objects.create_user(
      name="Update Test User", email="update@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Other Update User", email="otherupdate@example.com", password="password123"
    )

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    cls.other_user.delete()

  def setUp(self):
    self.client_obj = Client.objects.create(
      user=self.user, name="Original Name", cpf="11111111111"
    )
    ClientEmail.objects.create(client=self.client_obj, email="old@example.com")
    ClientPhone.objects.create(client=self.client_obj, phone="+5511999999999")
    ClientAddress.objects.create(
      client=self.client_obj,
      state="SP",
      city="Old City",
      neighborhood="Old Neigh",
      street="Old St",
      house_number="1",
    )
    ClientRating.objects.create(client=self.client_obj, score=3.0, comment="Ok")

  def test_update_success_full_data_with_user_param(self):
    """update method successfully updates and return updated client model when passing user as param and full data."""
    data = {
      "name": "Updated Name",
      "cpf": "22222222222",
      "emails": ["new@example.com", "new2@example.com"],
      "phones": ["+5511888888888"],
      "address": {
        "state": "RJ",
        "city": "New City",
        "neighborhood": "New Neigh",
        "street": "New St",
        "house_number": "2",
      },
      "rating": {"score": 5.0, "comment": "Excellent"},
    }
    updated = ClientService.update(str(self.client_obj.id), data, user=self.user)

    self.assertEqual(updated.name, "Updated Name")
    self.assertEqual(updated.clientemail_set.count(), 2)
    self.assertEqual(updated.clientphone_set.count(), 1)
    self.assertEqual(updated.clientaddress.city, "New City")
    self.assertEqual(updated.clientrating.score, 5.0)

  def test_update_success_no_user_param(self):
    """update method successfully updates and return updated client model when not parsing user."""
    data = {
      "name": "Updated Name No User",
    }
    updated = ClientService.update(str(self.client_obj.id), data)
    self.assertEqual(updated.name, "Updated Name No User")

  def test_update_success_required_data_only(self):
    """update method successfully updates and return updated client model when passing only the required data."""
    # Assuming name and cpf are the required data for an update payload
    data = {"name": "Required Only", "cpf": "33333333333"}
    updated = ClientService.update(str(self.client_obj.id), data, user=self.user)
    self.assertEqual(updated.name, "Required Only")
    self.assertEqual(updated.cpf, "33333333333")

  def test_update_deletes_unspecified_nested_collections(self):
    """update method deletes nested collections that where not specified within data."""
    data = {
      "name": "Rest of Fields will be Deleted",
      # missing emails, phones, address, rating
    }
    updated = ClientService.update(str(self.client_obj.id), data, user=self.user)
    self.assertEqual(updated.name, "Rest of Fields will be Deleted")
    # Nestings should be Deleted
    self.assertEqual(updated.clientemail_set.count(), 0)
    self.assertEqual(updated.clientphone_set.count(), 0)
    self.assertFalse(hasattr(updated, "clientaddress"))
    self.assertFalse(hasattr(updated, "clientrating"))

  def test_update_replaces_and_deletes_nested_collections(self):
    """
    update method fully replace nested collections
    as well as Client data, even when specified None as data (means delete),
    instead of appending.
    """
    rating = {"score": 0, "comment": "Deleted"}
    data = {
      "name": "Deleted Collections",
      "emails": None,
      "phones": [],  # Empty list also means delete
      "address": None,
      "rating": rating,
    }
    updated = ClientService.update(str(self.client_obj.id), data, user=self.user)
    self.assertEqual(updated.name, "Deleted Collections")
    self.assertEqual(updated.clientemail_set.count(), 0)
    self.assertEqual(updated.clientphone_set.count(), 0)
    self.assertFalse(hasattr(updated, "clientaddress"))
    self.assertTrue(hasattr(updated, "clientrating"))

  def test_update_fails_invalid_client_id(self):
    """update method fails to update client model when client_id is invalid."""
    with self.assertRaises(Http404):
      ClientService.update(str(uuid.uuid4()), {"name": "Test"})

  def test_update_fails_invalid_user(self):
    """update method fails to update client model when user is invalid."""
    with self.assertRaises(Http404):
      ClientService.update(
        str(self.client_obj.id), {"name": "Test"}, user=self.other_user
      )


class TestClientService_PartialUpdate(TestCase):
  @classmethod
  def setUpClass(cls):
    cls.user = User.objects.create_user(
      name="Partial Update Test User",
      email="partialupdate@example.com",
      password="password123",
    )
    cls.other_user = User.objects.create_user(
      name="Other Partial Update User",
      email="otherpartial@example.com",
      password="password123",
    )

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    cls.other_user.delete()

  def setUp(self):
    self.client_obj = Client.objects.create(
      user=self.user, name="Original Name", cpf="11111111111"
    )
    ClientEmail.objects.create(client=self.client_obj, email="old@example.com")
    ClientPhone.objects.create(client=self.client_obj, phone="+5511999999999")
    ClientAddress.objects.create(
      client=self.client_obj,
      state="SP",
      city="Old City",
      neighborhood="Old Neigh",
      street="Old St",
      house_number="1",
    )
    ClientRating.objects.create(client=self.client_obj, score=3.0, comment="Ok")

  def test_partial_update_success_no_user_param(self):
    """partial_update method successfully updates and return updated client model when not parsing user."""
    data = {
      "name": "Updated Name No User",
    }
    updated = ClientService.partial_update(str(self.client_obj.id), data)
    self.assertEqual(updated.name, "Updated Name No User")

  def test_partial_update_ignores_unspecified_nested_collections(self):
    """partial_update method ignores a nested collection when it is not specified in given data."""
    data = {
      "name": "Only Name Partial Update",
      # emails, phones, address, rating are omitted and should remain intact
    }
    updated = ClientService.partial_update(
      str(self.client_obj.id), data, user=self.user
    )
    self.assertEqual(updated.name, "Only Name Partial Update")

    # Assert nestings are intact
    self.assertEqual(updated.clientemail_set.count(), 1)
    self.assertEqual(updated.clientphone_set.count(), 1)
    self.assertTrue(hasattr(updated, "clientaddress"))
    self.assertTrue(hasattr(updated, "clientrating"))

  def test_partial_update_erases_nested_collection_when_none_or_empty(self):
    """partial_update method only erases a nested collection if it is explicitly specified within data as none or empty data."""
    data = {
      "emails": [],  # specifies empty list, should delete all
      "rating": None,  # specifies None, should delete
      # phones and address are omitted, should be ignored and intact
    }
    updated = ClientService.partial_update(
      str(self.client_obj.id), data, user=self.user
    )

    self.assertEqual(updated.name, "Original Name")  # Main data shouldn't change
    self.assertEqual(updated.clientemail_set.count(), 0)  # erased
    self.assertFalse(hasattr(updated, "clientrating"))  # erased

    self.assertEqual(updated.clientphone_set.count(), 1)  # intact
    self.assertTrue(hasattr(updated, "clientaddress"))  # intact

  def test_partial_update_updates_only_non_required_data(self):
    """partial_update method can update only non-required data like nested collections."""
    data = {
      "phones": ["+5511888888888", "+5511777777777"],
      "address": {
        "state": "RJ",
        "city": "New City",
        "neighborhood": "New Neigh",
        "street": "New St",
        "house_number": "2",
      },
    }
    updated = ClientService.partial_update(
      str(self.client_obj.id), data, user=self.user
    )

    # Required fields untouched
    self.assertEqual(updated.name, "Original Name")
    self.assertEqual(updated.cpf, "11111111111")

    # Updated nested fields
    self.assertEqual(updated.clientphone_set.count(), 2)
    self.assertEqual(updated.clientaddress.city, "New City")

  def test_partial_update_fails_invalid_client_id(self):
    with self.assertRaises(Http404):
      ClientService.partial_update(str(uuid.uuid4()), {"name": "Test"})

  def test_partial_update_fails_invalid_user(self):
    with self.assertRaises(Http404):
      ClientService.partial_update(
        str(self.client_obj.id), {"name": "Test"}, user=self.other_user
      )


class TestClientService_Delete(TestCase):
  @classmethod
  def setUpClass(cls):
    cls.user = User.objects.create_user(
      name="Delete Test User", email="delete@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Other Delete User", email="otherdelete@example.com", password="password123"
    )

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    cls.other_user.delete()

  def setUp(self):
    self.client_obj = Client.objects.create(
      user=self.user, name="To Delete", cpf="99999999999"
    )

  def test_delete_success_with_user(self):
    """delete method successfully deletes the client when passing valid client_id and user."""
    result = ClientService.delete(str(self.client_obj.id), user=self.user)
    self.assertTrue(result)
    with self.assertRaises(Client.DoesNotExist):
      Client.objects.get(id=self.client_obj.id)

  def test_delete_success_no_user_param(self):
    """delete method successfully deletes the client when passing only the client_id."""
    result = ClientService.delete(str(self.client_obj.id))
    self.assertTrue(result)
    with self.assertRaises(Client.DoesNotExist):
      Client.objects.get(id=self.client_obj.id)

  def test_delete_fails_invalid_client_id(self):
    """delete method fails when client_id is invalid."""
    with self.assertRaises(Http404):
      ClientService.delete(str(uuid.uuid4()))

  def test_delete_fails_invalid_user(self):
    """delete method fails when user does not own the client."""
    with self.assertRaises(Http404):
      ClientService.delete(str(self.client_obj.id), user=self.other_user)
    
    # Verify it still exists in the DB
    self.assertTrue(Client.objects.filter(id=self.client_obj.id).exists())
