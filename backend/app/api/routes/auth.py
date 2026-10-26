from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import SESSION_COOKIE, CommercialUser, get_auth_service
from app.config import Settings, get_settings
from app.schemas.auth import LoginRequest, SessionResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=SessionResponse)
def login(
    credentials: LoginRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SessionResponse:
    username = credentials.username.strip().lower()
    if not auth_service.credentials_are_valid(username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario o la contraseña no son correctos.",
        )
    response.set_cookie(
        key=SESSION_COOKIE,
        value=auth_service.create_session(username),
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )
    return SessionResponse(username=username)


@router.get("/me", response_model=SessionResponse)
def current_session(username: CommercialUser) -> SessionResponse:
    return SessionResponse(username=username)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", samesite="lax")
