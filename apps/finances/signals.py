from django.dispatch import receiver
from django.db.models.signals import post_save

from apps.projects_and_clients.models import Project
from apps.finances.models import MovGroup


@receiver(post_save, sender=Project)
def create_movimentation_group(sender: Project, instance: Project, created, **kwargs):
  """Create a movimentation group when a new project is created."""
  if created:
    proj_movgroup = MovGroup(
      user=instance.user,
      name=("Grupo de Finanças Projeto - " + instance.name.strip())[0:124] + "...",
      description=(
        "Grupo de Finanças dedicado à registrar as finanças do Projeto - "
        + instance.name.strip()
      ),
      related_to=instance.id,
      relation="PROJECT",
    )
    proj_movgroup.save()
