import re
from typing import Literal


class InvalidPhoneError(Exception):
  """Exception raised for invalid phone numbers."""

  pass


class BRPhoneValidator:
  """
  Validates and format Brazillian phone number.
  """

  _validation_regex = r"^((\+?55)?\s*(\d{2}|\(\d{2}\))\s*(9)?\s*(\d{4}-?\d{4}))$"
  validation_regex = re.compile(_validation_regex)

  def __init__(self, phone: str):
    self._original_phone = phone
    unfilled_phone = self.validate(phone)
    self._phone = self.normalize(unfilled_phone)

  @classmethod
  def _validate(cls, phone: str):
    validated_phone = cls.validation_regex.match(phone)

    if not validated_phone:
      raise InvalidPhoneError(f"Invalid phone number: {phone}")

    return validated_phone.groups()[0]

  def validate(self, phone: str):
    return self._validate(phone)

  @classmethod
  def split_phone(cls, phone: str) -> tuple[str, str, str, str]:
    """Split phone into groups. group 1=+55, group 2=DDD, group 3=9, group 4=xxxx-xxxx"""
    match_regex = cls.validation_regex.match(phone)

    if not match_regex:
      raise InvalidPhoneError(f"Invalid phone number: {phone}")

    splited = match_regex.groups()

    return (splited[1], splited[2], splited[3], splited[4])

  @classmethod
  def normalize(cls, phone: str):
    """Normalize phone number in the form 55 11 9 99999999"""
    splited = list(cls.split_phone(phone))

    # Fill country code and leading nine
    if not splited[0]:
      splited[0] = "55"

    if not splited[2]:
      splited[2] = "9"

    # Remove spaces
    splited = [s.strip() for s in splited]
    splited[3] = re.sub(r"\s*", "", splited[3])  # Remove Middle spaces

    return " ".join(splited)

  @staticmethod
  def full_plain_formatter(string):
    return re.sub(r"\D", "", string)

  @staticmethod
  def full_nosymbol_formatter(string):
    return re.sub(r"[^0-9 ]", "", string)

  @staticmethod
  def full_formatter(string):
    return re.sub(
      r"^\+?55\s*\(?(\d{2})\)?\s*9\s*(\d{4})-?(\d{4})$", "+55 (\1) 9 \2-\3", string
    )

  formatters = {
    "FULL": full_formatter,
    "FULLPLAIN": full_plain_formatter,
    "FULLNOSYMBOL": full_nosymbol_formatter,
  }

  def get_formated(self, format: Literal["FULL", "FULLNOSYMBOL", "FULLPLAIN"] = "FULL"):
    formatter = self.formatters.get(format)
    if not formatter:
      raise ValueError(f"Invalid format: {format}")
    return formatter(self._phone)
