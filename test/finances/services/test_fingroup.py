from django.test import TestCase
import uuid

from apps.users.models import User
from apps.finances.models import FinGroup
from apps.finances.services.fingroup import FinGroupService
from apps.core.exceptions import ResourceNotFoundError
from apps.finances.schemas.fingroup import (
  CreateFinGroupReq,
  UpdateFinGroupReq,
  PartialUpdateFinGroupReq,
)


class BaseFinGroupTest(TestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.user = User.objects.create_user(
      name="finuser",
      email="finuser@test.com",
      password="testpass",
      phone="5584000000000",
    )
    cls.other_user = User.objects.create_user(
      name="otherfinuser",
      email="otherfinuser@test.com",
      password="testpass",
      phone="5584000000001",
    )

  @classmethod
  def tearDownClass(cls):
    cls.other_user.delete()
    cls.user.delete()
    super().tearDownClass()


class TestCreateFinGroup(BaseFinGroupTest):
  def test_create_personal_group(self):
    data = CreateFinGroupReq(name="Personal Expenses")
    fg = FinGroupService.create(self.user, data)
    self.assertEqual(fg.name, "Personal Expenses")
    self.assertEqual(fg.relation, "PERSONAL")
    self.assertIsNone(fg.related_to)

  def test_create_project_group(self):
    project_id = str(uuid.uuid4())
    data = CreateFinGroupReq(name="Project Finance", related_to=project_id, relation="PROJECT")
    fg = FinGroupService.create(self.user, data)
    self.assertEqual(fg.relation, "PROJECT")
    self.assertEqual(str(fg.related_to), project_id)


class TestGetFinGroup(BaseFinGroupTest):
  def test_get_success(self):
    fg = FinGroup.objects.create(user=self.user, name="Group A")
    result = FinGroupService.get(self.user, str(fg.id))
    self.assertEqual(result.id, fg.id)

  def test_get_not_found(self):
    with self.assertRaises(ResourceNotFoundError):
      FinGroupService.get(self.user, str(uuid.uuid4()))

  def test_get_other_user(self):
    fg = FinGroup.objects.create(user=self.user, name="Group B")
    with self.assertRaises(ResourceNotFoundError):
      FinGroupService.get(self.other_user, str(fg.id))


class TestListFinGroups(BaseFinGroupTest):
  def test_list_groups(self):
    FinGroup.objects.create(user=self.user, name="G1")
    FinGroup.objects.create(user=self.user, name="G2")
    groups = FinGroupService.list(self.user)
    self.assertGreaterEqual(groups.count(), 2)

  def test_list_other_user_empty(self):
    groups = FinGroupService.list(self.other_user)
    self.assertEqual(groups.count(), 0)


class TestUpdateFinGroup(BaseFinGroupTest):
  def test_update_success(self):
    fg = FinGroup.objects.create(user=self.user, name="Before")
    data = UpdateFinGroupReq(name="After")
    updated = FinGroupService.update(self.user, str(fg.id), data)
    self.assertEqual(updated.name, "After")


class TestPartialUpdateFinGroup(BaseFinGroupTest):
  def test_partial_update_success(self):
    fg = FinGroup.objects.create(user=self.user, name="Before", relation="PERSONAL")
    data = PartialUpdateFinGroupReq(name="After")
    updated = FinGroupService.partial_update(self.user, str(fg.id), data)
    self.assertEqual(updated.name, "After")
    self.assertEqual(updated.relation, "PERSONAL")


class TestDeleteFinGroup(BaseFinGroupTest):
  def test_delete_success(self):
    fg = FinGroup.objects.create(user=self.user, name="Bye")
    FinGroupService.delete(self.user, str(fg.id))
    with self.assertRaises(ResourceNotFoundError):
      FinGroupService.get(self.user, str(fg.id))
