"""
Integration tests for auth endpoints, using an in-memory-ish test DB.

Run with: pytest tests/ -v
Requires a running Postgres test database (see conftest.py for setup)
or can be adapted to use SQLite for CI speed (note: SQLite lacks native
ARRAY/JSONB support used by some models, so Postgres is recommended —
e.g. via a docker-compose.test.yml service).
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
class TestAuthFlow:
    async def test_register_creates_user_and_returns_tokens(self, test_db_session, monkeypatch):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={"email": "student@example.com", "password": "securepass123", "full_name": "Jane Doe"},
            )
            assert response.status_code == 201
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data

    async def test_duplicate_registration_fails(self, test_db_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {"email": "duplicate@example.com", "password": "securepass123"}
            first = await client.post("/api/v1/auth/register", json=payload)
            assert first.status_code == 201

            second = await client.post("/api/v1/auth/register", json=payload)
            assert second.status_code == 400

    async def test_login_with_wrong_password_fails(self, test_db_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/v1/auth/register", json={"email": "loginuser@example.com", "password": "correctpass123"}
            )
            response = await client.post(
                "/api/v1/auth/login", json={"email": "loginuser@example.com", "password": "wrongpassword"}
            )
            assert response.status_code == 401

    async def test_protected_route_requires_token(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")
            assert response.status_code == 401
