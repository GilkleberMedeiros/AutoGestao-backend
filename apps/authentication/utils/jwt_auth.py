from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import jwt
from typing import TypedDict


class TokenPair(TypedDict):
  access: str
  refresh: str


class JWTAuth:
  @staticmethod
  def create_tokens(user) -> TokenPair:
    """Generate access and refresh tokens using RSA keys"""
    refresh = RefreshToken.for_user(user)
    return {
      "access": str(refresh.access_token),
      "refresh": str(refresh),
    }

  @staticmethod
  def verify_token(token):
    """Verify and decode token using public key"""
    try:
      decoded = jwt.decode(
        token,
        settings.JWT_PUBKEY,
        algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
      )
      return decoded
    except jwt.ExpiredSignatureError:
      return None
    except jwt.InvalidTokenError:
      return None
