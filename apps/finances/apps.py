from django.apps import AppConfig


class FinancesConfig(AppConfig):
  name = "apps.finances"

  def ready(self):
    # Register signals on module import
    import apps.finances.signals  # noqa
