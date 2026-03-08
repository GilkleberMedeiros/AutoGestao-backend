"""
Base app Exceptions.
"""


class ExternalServiceError(Exception):
  """
  Base Exception raised when an external service fails.
  """

  def __init__(self, message: str):
    self.message = message
