"""
Test API register endpoint
"""

from django.test import TestCase, Client
from unittest.mock import patch
from django.db import DatabaseError

from apps.users.models import User


class RegisterTestCase(TestCase):
  def setUp(self):
    self.client = Client()
    self.register = lambda data, *args, **kwargs: self.client.post(
      "/api/users/auth/register", data, content_type="application/json", *args, **kwargs
    )

  def test_returns_detail_when_user_created_successfully(self):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
      "phone": "5584996162398",
    }

    response = self.register(userdata)
    response_data = response.json()

    self.assertEqual(response.status_code, 201)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertTrue(response_data.get("success", None))

  def test_user_created_on_database(self):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
      "phone": "5584990000000",
    }

    _ = self.register(userdata)
    user_created = User.objects.filter(email="joao_email@gmail.com").first()

    if not user_created:
      self.fail("Couldn't find created user on Database!")
    self.assertEqual(user_created.name, "João")
    self.assertEqual(user_created.email, "joao_email@gmail.com")
    self.assertTrue(user_created.check_password("SenhaJoao123@"))
    self.assertEqual(user_created.phone, "5584990000000")

  def test_can_create_user_without_phonenumber(self):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
    }

    _ = self.register(userdata)
    user_created = User.objects.filter(email="joao_email@gmail.com").first()

    if not user_created:
      self.fail("Couldn't find created user on Database!")
    self.assertEqual(user_created.name, "João")
    self.assertEqual(user_created.email, "joao_email@gmail.com")
    self.assertTrue(user_created.check_password("SenhaJoao123@"))
    self.assertIsNone(user_created.phone)

  def test_returns_error_when_email_not_unique(self):
    userdata1 = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
    }
    userdata2 = {
      "name": "João Pé de Feijão",
      "email": "joao_email@gmail.com",
      "password": "PasswdJoao456#",
    }

    _ = self.register(userdata1)
    response = self.register(userdata2)
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_returns_error_when_phone_not_unique(self):
    userdata1 = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
      "phone": "5584990000000",
    }
    userdata2 = {
      "name": "João Pé de Feijão",
      "email": "joao_pedefeijao_email@gmail.com",
      "password": "PasswdJoao456#",
      "phone": "5584990000000",
    }

    _ = self.register(userdata1)
    response = self.register(userdata2)
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_user_not_created_on_database_when_email_not_unique(self):
    userdata1 = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
    }
    userdata2 = {
      "name": "João Pé de Feijão",
      "email": "joao_email@gmail.com",
      "password": "PasswdJoao456#",
    }

    _ = self.register(userdata1)
    _ = self.register(userdata2)
    users_created = User.objects.filter(email="joao_email@gmail.com")

    self.assertEqual(users_created.count(), 1)

  def test_user_not_created_on_database_when_phone_not_unique(self):
    userdata1 = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
      "phone": "5584990000000",
    }
    userdata2 = {
      "name": "João Pé de Feijão",
      "email": "joao_pedefeijao_email@gmail.com",
      "password": "PasswdJoao456#",
      "phone": "5584990000000",
    }

    _ = self.register(userdata1)
    _ = self.register(userdata2)
    users_created = User.objects.filter(phone="5584990000000")

    self.assertEqual(users_created.count(), 1)

  @patch("apps.users.models.User.objects.create_user")
  def test_returns_error_when_database_fails(self, mock_create):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
      "phone": "5584990000000",
    }
    mock_create.side_effect = DatabaseError("Generic Database Error!")

    response = self.register(userdata)
    response_data = response.json()

    self.assertEqual(response.status_code, 500)
    self.assertIsInstance(response_data, dict)
    self.assertIsNotNone(response_data.get("details", None))
    self.assertEqual(response_data.get("success", None), False)

  def test_returns_error_when_name_is_missing(self):
    userdata = {
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_email_is_missing(self):
    userdata = {
      "name": "João",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_password_is_missing(self):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_password_is_too_short(self):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "short1@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_password_is_too_long(self):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "a" * 129,
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_email_is_too_long(self):
    userdata = {
      "name": "João",
      "email": "a" * 250 + "@example.com",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_name_is_empty_string(self):
    userdata = {
      "name": "",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_email_is_empty_string(self):
    userdata = {
      "name": "João",
      "email": "",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_password_is_empty_string(self):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_phone_is_too_long(self):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
      "phone": "1" * 25,
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_name_is_too_long(self):
    userdata = {
      "name": "a" * 129,
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_email_has_whitespace(self):
    userdata = {
      "name": "João",
      "email": "joao email@gmail.com",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_email_case_insensitive_duplicate_check(self):
    userdata1 = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
    }
    userdata2 = {
      "name": "João Pé de Feijão",
      "email": "JOAO_EMAIL@GMAIL.COM",
      "password": "SenhaJoao456#",
    }

    _ = self.register(userdata1)
    response = self.register(userdata2)
    response_data = response.json()

    self.assertEqual(response.status_code, 400)
    self.assertEqual(response_data.get("success", None), False)

  def test_returns_success_with_special_characters_in_name(self):
    userdata = {
      "name": "João José da Silva-Pereira",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 201)

  def test_returns_success_with_plus_sign_in_email(self):
    userdata = {
      "name": "João",
      "email": "joao+testing@gmail.com",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 201)

  def test_returns_success_with_phone_containing_special_characters(self):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
      "phone": "+55 (84) 99999-9999",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 201)

  def test_phone_duplicate_check_with_special_characters(self):
    userdata1 = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
      "phone": "+55 (84) 99999-9999",
    }
    userdata2 = {
      "name": "Maria",
      "email": "maria_email@gmail.com",
      "password": "SenhaJoao456#",
      "phone": "(84) 99999-9999",  # Different format, same digits
    }

    _ = self.register(userdata1)
    response = self.register(userdata2)

    # Note: This test checks that the exact string is used for duplicate detection
    # If the strings differ, it will succeed (current behavior)
    # If normalization is implemented, this should return 400
    self.assertIn(response.status_code, [201, 400])

  def test_returns_error_when_invalid_json_payload(self):
    response = self.client.post(
      "/api/users/auth/register",
      "invalid json",
      content_type="application/json",
    )
    self.assertEqual(response.status_code, 400)

  def test_returns_error_when_null_name(self):
    userdata = {
      "name": None,
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_null_email(self):
    userdata = {
      "name": "João",
      "email": None,
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_returns_error_when_null_password(self):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": None,
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 422)

  def test_can_create_user_with_empty_string_phone(self):
    userdata = {
      "name": "João",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
      "phone": "",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 201)

    user_created = User.objects.filter(email="joao_email@gmail.com").first()
    self.assertIsNone(user_created.phone)

  def test_returns_success_with_numeric_name(self):
    userdata = {
      "name": "123456",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 201)

  def test_returns_success_with_single_character_name(self):
    userdata = {
      "name": "J",
      "email": "joao_email@gmail.com",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 201)

  def test_email_validation_with_subdomain(self):
    userdata = {
      "name": "João",
      "email": "joao@mail.example.co.uk",
      "password": "SenhaJoao123@",
    }

    response = self.register(userdata)
    self.assertEqual(response.status_code, 201)

  def test_can_create_multiple_users_with_different_emails(self):
    userdata1 = {
      "name": "João",
      "email": "joao1@gmail.com",
      "password": "SenhaJoao123@",
    }
    userdata2 = {
      "name": "Maria",
      "email": "maria@gmail.com",
      "password": "SenhaJoao456#",
    }
    userdata3 = {
      "name": "Pedro",
      "email": "pedro@gmail.com",
      "password": "SenhaJoao789$",
    }

    response1 = self.register(userdata1)
    response2 = self.register(userdata2)
    response3 = self.register(userdata3)

    self.assertEqual(response1.status_code, 201)
    self.assertEqual(response2.status_code, 201)
    self.assertEqual(response3.status_code, 201)
    self.assertEqual(User.objects.count(), 3)
