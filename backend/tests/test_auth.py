import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_login_creates_a_server_session() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login",
            json={"username": "comercial", "password": "comercial123"},
        )
        session = await client.get("/api/auth/me")

    assert login.status_code == 200
    assert login.json() == {"username": "comercial"}
    assert "HttpOnly" in login.headers["set-cookie"]
    assert session.status_code == 200
    assert session.json() == {"username": "comercial"}


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "comercial", "password": "incorrecta"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "El usuario o la contraseña no son correctos."


@pytest.mark.asyncio
async def test_protected_endpoint_requires_a_session() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_rejects_a_tampered_session_cookie() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies={"manuable_session": "not-a-valid-token"},
    ) as client:
        response = await client.get("/api/auth/me")

    assert response.status_code == 401
