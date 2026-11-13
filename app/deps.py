"""Authentication and role checks, written as FastAPI dependencies."""
import jwt
from fastapi import Depends, Request

from .errors import ApiError
from .security import decode_token
from .store import User

BEARER = {"WWW-Authenticate": "Bearer"}


def _unauthorized(message: str) -> ApiError:
    return ApiError(401, "unauthenticated", message, BEARER)


def get_current_user(request: Request) -> User:
    """Who is calling? Verify the token, then load the user. The role is NEVER read from the token."""
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise _unauthorized("Authentication required.")
    try:
        claims = decode_token(token.strip(), request.app.state.settings)
    except jwt.PyJWTError:
        raise _unauthorized("Invalid or expired token.")
    user = request.app.state.store.users.get(claims["sub"])
    if user is None or user.disabled:
        raise _unauthorized("Invalid or expired token.")
    request.state.username = user.username
    return user


def require_roles(*roles: str):
    """Role check: authenticated AND holding one of the allowed roles, else 403."""
    allowed = frozenset(roles)

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise ApiError(403, "forbidden", "You do not have permission to perform this action.")
        return user

    return dependency
