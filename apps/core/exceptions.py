"""
Base app Exceptions.
"""


class AppError(Exception):
  """
  Base App Exception. Can be used to distinguish app errors from other errors.
  """

  def __init__(self, message: str):
    self.message = message


class BusinessRuleError(AppError):
  """
  Base Exception raised when a bussiness rule is violated.
  """

  def __init__(self, message: str):
    self.message = message


class ExternalServiceError(AppError):
  """
  Base Exception raised when an external service fails.
  """

  def __init__(self, message: str):
    self.message = message


class AuthenticationError(AppError):
  """
  Base Exception raised when an authentication error occurs.
  """

  def __init__(self, message: str):
    self.message = message


class ResourceNotFoundError(AppError):
  """
  Base Exception raised when a resource is not found.
  """

  def __init__(self, message: str):
    self.message = message


class ResourceAlreadyExistsError(AppError):
  """
  Base Exception raised when creating a resource that already exists.
  """

  def __init__(self, message: str):
    self.message = message
