from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from apps.projects_and_clients.models import Project
from apps.notifications.services.deadline import DeadlineNotificationService
from apps.notifications.schemas.deadline import DeadlineNotificationCreateReq


@receiver(post_save, sender=Project)
def create_deadline_notification(sender, instance, created, **kwargs):
  """
  Creates a deadline notification for a project.
  """
  if created and instance.estimated_deadline:
    try:
      # RN: Notificação de aproximação de prazo (7 dias antes)
      deadline = instance.estimated_deadline
      if isinstance(deadline, str):
        from django.utils.dateparse import parse_date

        deadline = parse_date(deadline)

      if not deadline:
        return

      deliver_at = deadline - timedelta(days=7)
      # Convert date to datetime
      deliver_datetime = timezone.make_aware(
        timezone.datetime.combine(deliver_at, timezone.datetime.min.time())
      )

      DeadlineNotificationService.create(
        user_id=str(instance.user.id),
        data=DeadlineNotificationCreateReq(
          title=f"Prazo Próximo: {instance.name}",
          message=f"O projeto {instance.name} vence em {instance.estimated_deadline.strftime('%d/%m/%Y')}.",
          deliver_at=deliver_datetime,
        ),
      )
    except Exception:
      # Do not break the main transaction if notification fails
      pass
