from typing import TypedDict, Literal
from datetime import datetime


class NotificationTypes:
  PERSONAL = "PERSONAL"
  SPENDING_LIMIT = "SPENDING_LIMIT"
  DEADLINE = "DEADLINE"


class NotificationPeriods:
  WEEKLY = "WEEKLY"
  MONTHLY = "MONTHLY"
  QUARTERLY = "QUARTERLY"
  SEMI_ANNUALLY = "SEMI_ANNUALLY"


class BaseNotificationDTO(TypedDict):
  id: str
  user_id: str
  title: str
  message: str
  type: Literal[
    NotificationTypes.PERSONAL,
    NotificationTypes.SPENDING_LIMIT,
    NotificationTypes.DEADLINE,
  ]


class NotificationDTO(BaseNotificationDTO):
  deliver_at: datetime


class SpendingLimitNotificationDTO(BaseNotificationDTO):
  threshold: float
  period: Literal[
    NotificationPeriods.WEEKLY,
    NotificationPeriods.MONTHLY,
    NotificationPeriods.QUARTERLY,
    NotificationPeriods.SEMI_ANNUALLY,
  ]


class DeadlineNotificationDTO(BaseNotificationDTO):
  pass
