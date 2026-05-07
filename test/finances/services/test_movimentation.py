from unittest import TestCase
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

from apps.core.exceptions import ResourceNotFoundError
from apps.finances.services.movimentation import MovimentationService
from apps.finances.schemas.movimentation import (
  CreateMovimentationReq,
  UpdateMovimentationReq,
  PartialUpdateMovimentationReq,
)


class TestMovimentationService_Create(TestCase):
  @patch("apps.finances.services.movimentation.Movimentation")
  @patch("apps.finances.services.movimentation.MovGroupService.get")
  def test_create_success(self, mock_get_group, MockMovimentation):
    user = MagicMock()
    mov_group_id = "group-123"
    data = CreateMovimentationReq(
      amount=100.50, balance="+", reason="Test", movemented_at="2026-05-05T00:00:00Z"
    )

    mock_group = MagicMock()
    mock_get_group.return_value = mock_group

    mock_movimentation = MagicMock()
    MockMovimentation.objects.create.return_value = mock_movimentation

    result = MovimentationService.create(user, mov_group_id, data)

    mock_get_group.assert_called_once_with(user, mov_group_id)
    MockMovimentation.objects.create.assert_called_once_with(
      mov_group=mock_group,
      amount=Decimal("100.50"),
      balance="+",
      reason="Test",
      movemented_at=datetime.fromisoformat("2026-05-05T00:00:00Z"),
    )
    self.assertEqual(result, mock_movimentation)


class TestMovimentationService_Get(TestCase):
  @patch("apps.finances.services.movimentation.Movimentation")
  def test_get_success(self, MockMovimentation):
    user = MagicMock()
    movimentation_id = "mov-123"
    mock_movimentation = MagicMock()

    mock_qs = MagicMock()
    MockMovimentation.objects.filter.return_value = mock_qs
    mock_qs.first.return_value = mock_movimentation

    result = MovimentationService.get(user, movimentation_id)
    self.assertEqual(result, mock_movimentation)
    MockMovimentation.objects.filter.assert_called_once_with(
      id=movimentation_id, mov_group__user=user
    )

  @patch("apps.finances.services.movimentation.Movimentation")
  def test_get_not_found(self, MockMovimentation):
    user = MagicMock()
    movimentation_id = "mov-123"

    mock_qs = MagicMock()
    MockMovimentation.objects.filter.return_value = mock_qs
    mock_qs.first.return_value = None

    with self.assertRaises(ResourceNotFoundError):
      MovimentationService.get(user, movimentation_id)


class TestMovimentationService_List(TestCase):
  @patch("apps.finances.services.movimentation.Movimentation")
  def test_list_all_success(self, MockMovimentation):
    user = MagicMock()
    mock_qs = MagicMock()
    MockMovimentation.objects.filter.return_value = mock_qs

    result = MovimentationService.list(user)
    self.assertEqual(result, mock_qs)
    MockMovimentation.objects.filter.assert_called_once_with(mov_group__user=user)
    mock_qs.filter.assert_not_called()

  @patch("apps.finances.services.movimentation.Movimentation")
  def test_list_with_group_id_success(self, MockMovimentation):
    user = MagicMock()
    mov_group_id = "group-123"
    mock_qs = MagicMock()
    mock_qs_filtered = MagicMock()
    MockMovimentation.objects.filter.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs_filtered

    result = MovimentationService.list(user, mov_group_id=mov_group_id)
    self.assertEqual(result, mock_qs_filtered)
    MockMovimentation.objects.filter.assert_called_once_with(mov_group__user=user)
    mock_qs.filter.assert_called_once_with(mov_group_id=mov_group_id)


class TestMovimentationService_Update(TestCase):
  @patch("apps.finances.services.movimentation.MovimentationService.get")
  def test_update_success(self, mock_get):
    user = MagicMock()
    movimentation_id = "mov-123"

    mock_movimentation = MagicMock()
    mock_get.return_value = mock_movimentation

    data = UpdateMovimentationReq(
      amount=200.0, balance="-", reason="Updated", movemented_at="2026-05-06T00:00:00Z"
    )

    result = MovimentationService.update(user, movimentation_id, data)

    mock_get.assert_called_once_with(user, movimentation_id)

    self.assertEqual(mock_movimentation.amount, Decimal("200.0"))
    self.assertEqual(mock_movimentation.balance, "-")
    self.assertEqual(mock_movimentation.reason, "Updated")
    self.assertEqual(mock_movimentation.movemented_at, datetime.fromisoformat("2026-05-06T00:00:00Z"))
    mock_movimentation.save.assert_called_once()
    self.assertEqual(result, mock_movimentation)


class TestMovimentationService_PartialUpdate(TestCase):
  @patch("apps.finances.services.movimentation.MovimentationService.get")
  def test_partial_update_success(self, mock_get):
    user = MagicMock()
    movimentation_id = "mov-123"

    mock_movimentation = MagicMock()
    mock_movimentation.amount = 100.0
    mock_movimentation.reason = "Old Reason"
    mock_get.return_value = mock_movimentation

    data = PartialUpdateMovimentationReq(amount=50.0)

    result = MovimentationService.partial_update(user, movimentation_id, data)

    mock_get.assert_called_once_with(user, movimentation_id)

    self.assertEqual(mock_movimentation.amount, Decimal("50.0"))
    self.assertEqual(mock_movimentation.reason, "Old Reason")
    mock_movimentation.save.assert_called_once()
    self.assertEqual(result, mock_movimentation)


class TestMovimentationService_Delete(TestCase):
  @patch("apps.finances.services.movimentation.MovimentationService.get")
  def test_delete_success(self, mock_get):
    user = MagicMock()
    movimentation_id = "mov-123"

    mock_movimentation = MagicMock()
    mock_get.return_value = mock_movimentation

    result = MovimentationService.delete(user, movimentation_id)

    mock_get.assert_called_once_with(user, movimentation_id)
    mock_movimentation.delete.assert_called_once()
    self.assertEqual(result, {"success": True})
