from apps.core.exceptions import AppError


class InvalidRankingsCountError(AppError):
  def __init__(
    self, message: str = "Invalid rankings count. Must be greater than 0."
  ) -> None:
    super().__init__(message)
