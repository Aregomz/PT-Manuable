from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.services.auth_service import AuthService

SESSION_COOKIE = "manuable_session"


def get_auth_service(settings: Annotated[Settings, Depends(get_settings)]) -> AuthService:
    return AuthService(settings)


def require_commercial_user(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> str:
    username = auth_service.verify_session(session)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tu sesión no es válida o ha expirado. Inicia sesión nuevamente.",
        )
    return username


CommercialUser = Annotated[str, Depends(require_commercial_user)]
