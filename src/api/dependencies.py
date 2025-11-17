from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.schemes import ErrorCode
from src.settings import get_settings

security = HTTPBearer(auto_error=False)


def require_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.AUTHORIZATION_FAILED, "detail": "Missing bearer token"},
        )

    token = credentials.credentials
    settings = get_settings()
    if token != settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.AUTHORIZATION_FAILED, "detail": "Invalid token"},
        )


__all__ = ["require_bearer_token"]
