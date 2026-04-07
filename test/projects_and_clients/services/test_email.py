import uuid
from django.test import TestCase
from apps.projects_and_clients.models import Client, ClientEmail
from apps.users.models import User
from apps.core.exceptions import ResourceNotFoundError
from apps.projects_and_clients.services.emails import ClientEmailService


class TestClientEmailService_Create(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="Create User", email="create@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Other User", email="other@example.com", password="password123"
    )
    cls.client_obj = Client.objects.create(user=cls.user, name="Test Client")

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    cls.other_user.delete()
    super().tearDownClass()

  def test_create_email_success(self):
    """create method successfully adds an email to a client."""
    data = {"email": "new@example.com"}
    email = ClientEmailService.create(str(self.client_obj.id), data, self.user)

    self.assertEqual(email.email, "new@example.com")
    self.assertEqual(email.client, self.client_obj)

  def test_create_email_fails_invalid_client(self):
    """create method fails when client_id is invalid."""
    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.create(
        str(uuid.uuid4()), {"email": "test@example.com"}, self.user
      )

  def test_create_email_fails_unauthorized(self):
    """create method fails when client does not belong to the user."""
    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.create(
        str(self.client_obj.id), {"email": "test@example.com"}, self.other_user
      )


class TestClientEmailService_List(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="List User", email="list@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Other User", email="other@example.com", password="password123"
    )
    cls.client_obj = Client.objects.create(user=cls.user, name="List Client")
    ClientEmail.objects.create(client=cls.client_obj, email="e1@example.com")
    ClientEmail.objects.create(client=cls.client_obj, email="e2@example.com")

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    super().tearDownClass()

  def test_list_emails_success(self):
    """list method successfully returns all emails for a specific client."""
    results = ClientEmailService.list(str(self.client_obj.id), self.user)
    self.assertEqual(results.count(), 2)
    emails = [e.email for e in results]
    self.assertIn("e1@example.com", emails)
    self.assertIn("e2@example.com", emails)

  def test_list_emails_fails_invalid_client(self):
    """list method fails when client_id is invalid."""
    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.list(str(uuid.uuid4()), self.user)

  def test_list_emails_fails_unauthorized(self):
    """list method fails when client does not belong to the user."""
    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.list(str(self.client_obj.id), self.other_user)


class TestClientEmailService_Update(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="Update User", email="update@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Update Other", email="u_other@example.com", password="password123"
    )
    cls.client_obj = Client.objects.create(user=cls.user, name="Update Client")
    cls.email_obj = ClientEmail.objects.create(
      client=cls.client_obj, email="old@example.com"
    )

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    cls.other_user.delete()
    super().tearDownClass()

  def test_update_email_success(self):
    """update method successfully updates a specific email."""
    data = {"email": "updated@example.com"}
    updated = ClientEmailService.update(str(self.email_obj.id), data, self.user)
    self.assertEqual(updated.email, "updated@example.com")

  def test_update_email_fails_unauthorized(self):
    """update method fails when email belongs to another user's client."""
    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.update(
        str(self.email_obj.id), {"email": "fail@example.com"}, self.other_user
      )


class TestClientEmailService_Delete(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="Delete User", email="delete@example.com", password="password123"
    )
    cls.other_user = User.objects.create_user(
      name="Delete Other", email="d_other@example.com", password="password123"
    )
    cls.client_obj = Client.objects.create(user=cls.user, name="Delete Client")

  @classmethod
  def tearDownClass(cls):
    cls.user.delete()
    cls.other_user.delete()
    super().tearDownClass()

  def test_delete_email_success(self):
    """delete method successfully removes a specific email."""
    email = ClientEmail.objects.create(
      client=self.client_obj, email="to_delete@example.com"
    )
    result = ClientEmailService.delete(str(email.id), self.user)
    self.assertTrue(result)
    self.assertFalse(ClientEmail.objects.filter(id=email.id).exists())

  def test_delete_email_fails_unauthorized(self):
    """delete method fails when email belongs to another user's client."""
    email = ClientEmail.objects.create(client=self.client_obj, email="safe@example.com")
    with self.assertRaises(ResourceNotFoundError):
      ClientEmailService.delete(str(email.id), self.other_user)
    self.assertTrue(ClientEmail.objects.filter(id=email.id).exists())
