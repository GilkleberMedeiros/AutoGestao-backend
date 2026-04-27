from apps.core.exceptions import ExternalServiceError
from apps.users.models import User
from apps.authentication.schemas import LoginReq, RegisterReq
from apps.authentication.utils.jwt_auth import TokenPair, JWTAuth


class UserInvalidCredentialsError(Exception):
  def __init__(self, message: str = "User credentials are invalid."):
    self.message = message


class UserEmailAlreadyExistsError(Exception):
  def __init__(self, message: str = "User email already exists."):
    self.message = message


class UserPhoneAlreadyExistsError(Exception):
  def __init__(self, message: str = "User phone already exists."):
    self.message = message


class MissingRefreshTokenError(Exception):
  def __init__(self, message: str = "Missing refresh token."):
    self.message = message


class InvalidRefreshTokenError(Exception):
  def __init__(self, message: str = "Invalid refresh token."):
    self.message = message


class AuthService:
  @staticmethod
  def login(data: LoginReq) -> TokenPair:
    """
    Login user

    It searches for user by email and verifies credentials.
    If found, returns tokens.

    Args:
      data: Login credentials

    Returns:
      TokenPair with access and refresh tokens

    Raises:
      UserInvalidCredentialsError: If user is not found or credentials are invalid;
    """
    user = User.objects.filter(email=data.email).first()

    if not user or not user.check_password(data.password):
      raise UserInvalidCredentialsError()

    tokens = JWTAuth.create_tokens(user)

    return tokens

  @staticmethod
  def register(data: RegisterReq) -> User:
    """
    Register a new user.

    It validates user email and phone uniqueness.
    If valid, creates the user.

    Args:
      data: User registration data

    Returns:
      User object

    Raises:
      UserEmailAlreadyExistsError: If user email already exists;
      UserPhoneAlreadyExistsError: If user phone already exists;
      ExternalServiceError: If user creation fails;
    """
    # Validate user email is unique
    if User.objects.filter(email=data.email).exists():
      raise UserEmailAlreadyExistsError()

    # Validate user phone is unique, if provided
    if data.phone and User.objects.filter(phone=data.phone).exists():
      raise UserPhoneAlreadyExistsError()

    # create user
    try:
      user = User.objects.create_user(
        name=data.name, email=data.email, password=data.password, phone=data.phone
      )
    except Exception:
      raise ExternalServiceError(
        "Failed to create user on database for unknown reasons."
      )

    return user

  @staticmethod
  def refresh(refresh_token: str) -> TokenPair:
    """
    Refresh tokens

    Args:
      refresh_token: Refresh token

    Returns:
      TokenPair with access and refresh tokens

    Raises:
      MissingRefreshTokenError: If refresh token is not provided;
      InvalidRefreshTokenError: If refresh token is invalid;
    """
    if not refresh_token:
      raise MissingRefreshTokenError()

    decoded = JWTAuth.verify_token(refresh_token)
    if not decoded:
      raise InvalidRefreshTokenError()

    user_id = decoded.get("user_id")
    if not user_id:
      raise InvalidRefreshTokenError("Refresh Token does not contain user id.")

    user = User.objects.filter(id=user_id).first()
    if user is None:
      raise InvalidRefreshTokenError(
        "Couldn't find a user associated with the provided refresh token."
      )

    tokens = JWTAuth.create_tokens(user)

    return tokens
