import unittest
from unittest.mock import patch, MagicMock
from django.db.models.signals import post_save

from apps.projects_and_clients.models import Project
from apps.users.models import User

# Import the module to ensure the signal is registered
import apps.finances.signals


class TestProjectSignal__CreateMovGroup(unittest.TestCase):
  @patch("apps.finances.signals.MovGroup")
  def test_handler_responses_only_to_correct_sender(self, mock_mov_group_class):
    # Arrange
    # Use a different model as sender
    other_instance = User(id=1, name="Test User")

    # Act
    # Send post_save using a different sender
    post_save.send(sender=User, instance=other_instance, created=True)

    # Assert
    # The MovGroup should not be created because the sender is not Project
    mock_mov_group_class.assert_not_called()

  @patch("apps.finances.signals.MovGroup")
  def test_movgroup_not_created_when_created_param_is_false(self, mock_mov_group_class):
    # Arrange
    mock_user = User(id=1)
    # Use the real Project model class but don't save it to the DB
    project_instance = Project(id=1, name="My Test Project")
    project_instance.user = mock_user

    # Act
    # Simulate an updated project (created=False)
    post_save.send(sender=Project, instance=project_instance, created=False)

    # Assert
    # MovGroup should not be instantiated when created=False
    mock_mov_group_class.assert_not_called()

  @patch("apps.finances.signals.MovGroup")
  def test_movgroup_instantiated_saved_and_bound_to_project(self, mock_mov_group_class):
    # Arrange
    mock_user = User(id=1)
    # Use the real Project model class but don't save it to the DB
    project_instance = Project(id=1, name="My Test Project")
    project_instance.user = mock_user

    mock_mov_group_instance = MagicMock()
    mock_mov_group_class.return_value = mock_mov_group_instance

    # Act
    post_save.send(sender=Project, instance=project_instance, created=True)

    # Assert
    # Check if the class was instantiated with correct fields, especially related_to and relation
    mock_mov_group_class.assert_called_once_with(
      user=project_instance.user,
      name="Grupo de Finanças Projeto - My Test Project...",
      description="Grupo de Finanças dedicado à registrar as finanças do Projeto - My Test Project",
      related_to=project_instance.id,
      relation="PROJECT",
    )
    # Check if the save method was called
    mock_mov_group_instance.save.assert_called_once()
