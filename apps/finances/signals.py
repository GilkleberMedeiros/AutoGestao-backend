from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.projects_and_clients.models import Project
from apps.finances.models import FinGroup


@receiver(post_save, sender=Project)
def create_project_fingroup(sender, instance, created, **kwargs):
  if created:
    FinGroup.objects.create(
      user=instance.user,
      related_to=instance.id,
      relation="PROJECT",
      name=f"Finanças: {instance.name}",
    )
