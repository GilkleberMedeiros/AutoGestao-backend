from django.apps import apps
from django.contrib.auth.hashers import make_password
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager

from uuid import uuid4


class UserManager(DjangoUserManager):
  @classmethod
  def normalize_email(cls, email):
    """
    Lower-case all the email (not only domain part) and
    strip left and right
    """
    email = super().normalize_email(email).lower().strip()
    return email

  def _create_user_object(self, name, email, password, **extra_fields):
    if not name:
      raise ValueError("The given username must be set")
    email = self.normalize_email(email)
    # Lookup the real model class from the global app registry so this
    # manager method can be used in migrations. This is fine because
    # managers are by definition working on the real model.
    GlobalUserModel = apps.get_model(
      self.model._meta.app_label, self.model._meta.object_name
    )
    name = GlobalUserModel.normalize_username(name)
    user = self.model(name=name, email=email, **extra_fields)
    user.password = make_password(password)

    return user

  def _create_user(self, name, email, password, **extra_fields):
    """
    Create and save a user with the given username, email, and password.
    """
    user = self._create_user_object(name, email, password, **extra_fields)
    user.save(using=self._db)
    return user

  async def _acreate_user(self, name, email, password, **extra_fields):
    """See _create_user()"""
    user = self._create_user_object(name, email, password, **extra_fields)
    await user.asave(using=self._db)
    return user

  def create_user(self, name, email=None, password=None, **extra_fields):
    extra_fields.setdefault("is_staff", False)
    extra_fields.setdefault("is_superuser", False)
    return self._create_user(name, email, password, **extra_fields)

  async def acreate_user(self, name, email=None, password=None, **extra_fields):
    extra_fields.setdefault("is_staff", False)
    extra_fields.setdefault("is_superuser", False)
    return await self._acreate_user(name, email, password, **extra_fields)

  def create_superuser(self, name, email=None, password=None, **extra_fields):
    extra_fields.setdefault("is_staff", True)
    extra_fields.setdefault("is_superuser", True)

    if extra_fields.get("is_staff") is not True:
      raise ValueError("Superuser must have is_staff=True.")
    if extra_fields.get("is_superuser") is not True:
      raise ValueError("Superuser must have is_superuser=True.")

    return self._create_user(name, email, password, **extra_fields)

  async def acreate_superuser(self, name, email=None, password=None, **extra_fields):
    extra_fields.setdefault("is_staff", True)
    extra_fields.setdefault("is_superuser", True)

    if extra_fields.get("is_staff") is not True:
      raise ValueError("Superuser must have is_staff=True.")
    if extra_fields.get("is_superuser") is not True:
      raise ValueError("Superuser must have is_superuser=True.")

    return await self._acreate_user(name, email, password, **extra_fields)


class User(AbstractUser):
  id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
  name = models.CharField(max_length=128)
  username = None  # Remove the username field from AbstractUser
  email = models.EmailField(unique=True, max_length=256)
  phone = models.CharField(max_length=24, unique=True, blank=True, null=True)
  # Implicitly inherit the password field from AbstractUser
  is_email_valid = models.BooleanField(default=False)
  is_phone_valid = models.BooleanField(default=False)

  REQUIRED_FIELDS = ["name", "phone", "password"]
  USERNAME_FIELD = "email"

  objects = UserManager()

  def __str__(self):
    return self.email
