from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .dependencies import get_config


security = HTTPBearer(auto_error=False)


def require_api_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> None:
    config = get_config()
    if not config.api_token:
        return

    if credentials is None or credentials.credentials != config.api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token")


def require_api_token_for_mutation(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> None:
    config = get_config()
    if not config.api_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="API auth not configured")

    if credentials is None or credentials.credentials != config.api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token")
