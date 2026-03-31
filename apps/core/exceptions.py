"""
Base app Exceptions.
"""


class ExternalServiceError(Exception):
  """
  Base Exception raised when an external service fails.
  """

  def __init__(self, message: str):
    self.message = message


class ResourceNotFoundError(Exception):
  """
  Base Exception raised when a resource is not found.
  """

  def __init__(self, message: str):
    self.message = message
