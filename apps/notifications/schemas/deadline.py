from apps.notifications.schemas.notification import (
  NotificationCreateReq,
  NotificationSchema,
  UpdateNotificationReq,
)


class DeadlineNotificationSchema(NotificationSchema):
  pass


class DeadlineNotificationCreateReq(NotificationCreateReq):
  pass


class UpdateDeadlineNotificationReq(UpdateNotificationReq):
  pass
