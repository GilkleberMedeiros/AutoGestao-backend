"""
Phone Validator for Django Fields.
"""

from django.core.exceptions import ValidationError

from apps.core.validation.br_phone import BRPhoneValidator, InvalidPhoneError


class PhoneValidator:
  """
  Phone Validator for Django Fields.
  """

  def __init__(self, value):
    self.value = value

  def __call__(self, value):
    if not value:
      return None

    if isinstance(value, str):
      value = value.strip()

    if value == "":
      return None

    try:
      validator = BRPhoneValidator(value)
    except ValueError, InvalidPhoneError:
      raise ValidationError("Invalid phone number")

    return validator.get_formated(format="FULLPLAIN")
