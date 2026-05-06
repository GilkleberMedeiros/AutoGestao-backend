from unittest import TestCase
from unittest.mock import MagicMock, patch

from apps.core.exceptions import ResourceNotFoundError
from apps.finances.services.movgroup import (
  MovGroupService,
  MovGroupNameAlreadyExistsError,
)
from apps.finances.schemas.movgroup import (
  CreateMovGroupReq,
  UpdateMovGroupReq,
  PartialUpdateMovGroupReq,
)


class TestMovGroupService_ValidateUniqueConstraints(TestCase):
  @patch("apps.finances.services.movgroup.MovGroup")
  def test_validate_unique_constraints_success(self, MockMovGroup):
    user = MagicMock()
    data = MagicMock()
    data.name = "My Group"

    mock_qs = MagicMock()
    MockMovGroup.objects.filter.return_value = mock_qs
    mock_qs.exists.return_value = False

    MovGroupService.validate_unique_constraints(user, data)
    MockMovGroup.objects.filter.assert_called_once_with(user=user, name="My Group")

  @patch("apps.finances.services.movgroup.MovGroup")
  def test_validate_unique_constraints_exists(self, MockMovGroup):
    user = MagicMock()
    data = MagicMock()
    data.name = "My Group"

    mock_qs = MagicMock()
    MockMovGroup.objects.filter.return_value = mock_qs
    mock_qs.exists.return_value = True

    with self.assertRaises(MovGroupNameAlreadyExistsError):
      MovGroupService.validate_unique_constraints(user, data)

  @patch("apps.finances.services.movgroup.MovGroup")
  def test_validate_unique_constraints_with_exclude_id(self, MockMovGroup):
    user = MagicMock()
    data = MagicMock()
    data.name = "My Group"

    mock_qs = MagicMock()
    MockMovGroup.objects.filter.return_value = mock_qs
    mock_qs.exclude.return_value = mock_qs
    mock_qs.exists.return_value = False

    MovGroupService.validate_unique_constraints(user, data, exclude_id="some-id")
    MockMovGroup.objects.filter.assert_called_once_with(user=user, name="My Group")
    mock_qs.exclude.assert_called_once_with(id="some-id")


class TestMovGroupService_Create(TestCase):
  @patch("apps.finances.services.movgroup.MovGroup")
  @patch("apps.finances.services.movgroup.MovGroupService.validate_unique_constraints")
  def test_create_success(self, mock_validate, MockMovGroup):
    user = MagicMock()
    data = CreateMovGroupReq(name="New Group", description="Desc")

    mock_group = MagicMock()
    MockMovGroup.objects.create.return_value = mock_group

    result = MovGroupService.create(user, data)

    mock_validate.assert_called_once_with(user, data)
    MockMovGroup.objects.create.assert_called_once_with(
      user=user,
      name="New Group",
      description="Desc",
    )
    self.assertEqual(result, mock_group)


class TestMovGroupService_Get(TestCase):
  @patch("apps.finances.services.movgroup.MovGroup")
  def test_get_success(self, MockMovGroup):
    user = MagicMock()
    group_id = "some-id"
    mock_group = MagicMock()

    mock_qs = MagicMock()
    MockMovGroup.objects.filter.return_value = mock_qs
    mock_qs.first.return_value = mock_group

    result = MovGroupService.get(user, group_id)
    self.assertEqual(result, mock_group)
    MockMovGroup.objects.filter.assert_called_once_with(id=group_id, user=user)

  @patch("apps.finances.services.movgroup.MovGroup")
  def test_get_not_found(self, MockMovGroup):
    user = MagicMock()
    group_id = "some-id"

    mock_qs = MagicMock()
    MockMovGroup.objects.filter.return_value = mock_qs
    mock_qs.first.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      MovGroupService.get(user, group_id)


class TestMovGroupService_List(TestCase):
  @patch("apps.finances.services.movgroup.MovGroup")
  def test_list_success(self, MockMovGroup):
    user = MagicMock()
    mock_qs = MagicMock()
    MockMovGroup.objects.filter.return_value = mock_qs

    result = MovGroupService.list(user)
    self.assertEqual(result, mock_qs)
    MockMovGroup.objects.filter.assert_called_once_with(user=user)


class TestMovGroupService_Update(TestCase):
  @patch("apps.finances.services.movgroup.MovGroupService.get")
  @patch("apps.finances.services.movgroup.MovGroupService.validate_unique_constraints")
  def test_update_success(self, mock_validate, mock_get):
    user = MagicMock()
    group_id = "some-id"

    mock_group = MagicMock()
    mock_group.name = "Old Name"
    mock_get.return_value = mock_group

    data = UpdateMovGroupReq(name="New Name", description="New Desc")

    result = MovGroupService.update(user, group_id, data)

    mock_get.assert_called_once_with(user, group_id)
    mock_validate.assert_called_once_with(user, data, exclude_id=mock_group.id)

    self.assertEqual(mock_group.name, "New Name")
    self.assertEqual(mock_group.description, "New Desc")
    mock_group.save.assert_called_once()
    self.assertEqual(result, mock_group)

  @patch("apps.finances.services.movgroup.MovGroupService.get")
  @patch("apps.finances.services.movgroup.MovGroupService.validate_unique_constraints")
  def test_update_same_name(self, mock_validate, mock_get):
    user = MagicMock()
    group_id = "some-id"

    mock_group = MagicMock()
    mock_group.name = "Same Name"
    mock_get.return_value = mock_group

    data = UpdateMovGroupReq(name="Same Name", description="New Desc")

    _ = MovGroupService.update(user, group_id, data)

    mock_validate.assert_not_called()
    self.assertEqual(mock_group.name, "Same Name")
    self.assertEqual(mock_group.description, "New Desc")
    mock_group.save.assert_called_once()


class TestMovGroupService_PartialUpdate(TestCase):
  @patch("apps.finances.services.movgroup.MovGroupService.get")
  @patch("apps.finances.services.movgroup.MovGroupService.validate_unique_constraints")
  def test_partial_update_success(self, mock_validate, mock_get):
    user = MagicMock()
    group_id = "some-id"

    mock_group = MagicMock()
    mock_group.name = "Old Name"
    mock_group.description = "Old Desc"
    mock_get.return_value = mock_group

    data = PartialUpdateMovGroupReq(name="New Name")

    result = MovGroupService.partial_update(user, group_id, data)

    mock_get.assert_called_once_with(user, group_id)
    mock_validate.assert_called_once_with(user, data, exclude_id=mock_group.id)

    self.assertEqual(mock_group.name, "New Name")
    self.assertEqual(mock_group.description, "Old Desc")  # Unchanged
    mock_group.save.assert_called_once()
    self.assertEqual(result, mock_group)

  @patch("apps.finances.services.movgroup.MovGroupService.get")
  @patch("apps.finances.services.movgroup.MovGroupService.validate_unique_constraints")
  def test_partial_update_same_name(self, mock_validate, mock_get):
    user = MagicMock()
    group_id = "some-id"

    mock_group = MagicMock()
    mock_group.name = "Same Name"
    mock_get.return_value = mock_group

    data = PartialUpdateMovGroupReq(name="Same Name")

    _ = MovGroupService.partial_update(user, group_id, data)

    mock_validate.assert_not_called()
    mock_group.save.assert_called_once()

  @patch("apps.finances.services.movgroup.MovGroupService.get")
  @patch("apps.finances.services.movgroup.MovGroupService.validate_unique_constraints")
  def test_partial_update_no_name(self, mock_validate, mock_get):
    user = MagicMock()
    group_id = "some-id"

    mock_group = MagicMock()
    mock_group.name = "Old Name"
    mock_group.description = "Old Desc"
    mock_get.return_value = mock_group

    data = PartialUpdateMovGroupReq(description="New Desc")

    _ = MovGroupService.partial_update(user, group_id, data)

    mock_validate.assert_not_called()
    self.assertEqual(mock_group.name, "Old Name")
    self.assertEqual(mock_group.description, "New Desc")
    mock_group.save.assert_called_once()


class TestMovGroupService_Delete(TestCase):
  @patch("apps.finances.services.movgroup.MovGroupService.get")
  def test_delete_success(self, mock_get):
    user = MagicMock()
    group_id = "some-id"

    mock_group = MagicMock()
    mock_get.return_value = mock_group

    result = MovGroupService.delete(user, group_id)

    mock_get.assert_called_once_with(user, group_id)
    mock_group.delete.assert_called_once()
    self.assertEqual(result, {"success": True})
