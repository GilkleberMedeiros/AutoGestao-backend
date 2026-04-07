import uuid
from django.test import TestCase
from apps.projects_and_clients.models import Client, ClientPhone
from apps.users.models import User
from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.services.phones import ClientPhoneService


class TestClientPhoneService_Create(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="Create User", email="create_p@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Other User", email="other_p@example.com", password="password123"
    )
    cls.client_obj = Client.objects.create(user=cls.user, name="Test Client")

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    cls.other_user.delete()
    super().tearDownClass()

  def test_create_phone_success(self):
    """create method successfully adds a phone to a client."""
    data = {"phone": "11999999999"}
    phone = ClientPhoneService.create(str(self.client_obj.id), data, self.user)

    self.assertEqual(phone.phone, "+55 (11) 9 9999-9999")
    self.assertEqual(phone.client, self.client_obj)

  def test_create_phone_fails_invalid_client(self):
    """create method fails when client_id is invalid."""
    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.create(str(uuid.uuid4()), {"phone": "11999999999"}, self.user)

  def test_create_phone_fails_unauthorized(self):
    """create method fails when client does not belong to the user."""
    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.create(
        str(self.client_obj.id), {"phone": "11999999999"}, self.other_user
      )


class TestClientPhoneService_List(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="List User", email="list_p@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Other User", email="other_list_p@example.com", password="password123"
    )
    cls.client_obj = Client.objects.create(user=cls.user, name="List Client")
    ClientPhone.objects.create(client=cls.client_obj, phone="5511911111111")
    ClientPhone.objects.create(client=cls.client_obj, phone="5511922222222")

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    cls.other_user.delete()
    super().tearDownClass()

  def test_list_phones_success(self):
    """list method successfully returns all phones for a specific client."""
    results = ClientPhoneService.list(str(self.client_obj.id), self.user)
    self.assertEqual(len(results), 2)
    phones = [p.phone for p in results]
    self.assertIn("+55 (11) 9 1111-1111", phones)
    self.assertIn("+55 (11) 9 2222-2222", phones)

  def test_list_phones_fails_invalid_client(self):
    """list method fails when client_id is invalid."""
    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.list(str(uuid.uuid4()), self.user)

  def test_list_phones_fails_unauthorized(self):
    """list method fails when client does not belong to the user."""
    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.list(str(self.client_obj.id), self.other_user)


class TestClientPhoneService_Update(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="Update User", email="update_p@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Update Other", email="u_other_p@example.com", password="password123"
    )
    cls.client_obj = Client.objects.create(user=cls.user, name="Update Client")
    cls.phone_obj = ClientPhone.objects.create(
      client=cls.client_obj, phone="5511988888888"
    )

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    cls.other_user.delete()
    super().tearDownClass()

  def test_update_phone_success(self):
    """update method successfully updates a specific phone."""
    data = {"phone": "11977777777"}
    updated = ClientPhoneService.update(str(self.phone_obj.id), data, self.user)
    self.assertEqual(updated.phone, "+55 (11) 9 7777-7777")

  def test_update_phone_fails_unauthorized(self):
    """update method fails when phone belongs to another user's client."""
    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.update(
        str(self.phone_obj.id), {"phone": "11966666666"}, self.other_user
      )


class TestClientPhoneService_Delete(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="Delete User", email="delete_p@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Delete Other", email="d_other_p@example.com", password="password123"
    )
    cls.client_obj = Client.objects.create(user=cls.user, name="Delete Client")

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    cls.other_user.delete()
    super().tearDownClass()

  def test_delete_phone_success(self):
    """delete method successfully removes a specific phone."""
    phone = ClientPhone.objects.create(client=self.client_obj, phone="5511955555555")
    result = ClientPhoneService.delete(str(phone.id), self.user)
    self.assertTrue(result)
    self.assertFalse(ClientPhone.objects.filter(id=phone.id).exists())

  def test_delete_phone_fails_unauthorized(self):
    """delete method fails when phone belongs to another user's client."""
    phone = ClientPhone.objects.create(client=self.client_obj, phone="5511944444444")
    with self.assertRaises(ResourceNotFoundError):
      ClientPhoneService.delete(str(phone.id), self.other_user)
    self.assertTrue(ClientPhone.objects.filter(id=phone.id).exists())
