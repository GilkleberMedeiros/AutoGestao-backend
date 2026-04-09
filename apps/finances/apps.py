from django.apps import AppConfig


class FinancesConfig(AppConfig):
  name = "apps.finances"

  def ready(self):
    import apps.finances.signals
