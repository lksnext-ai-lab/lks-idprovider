import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from lks_idprovider.models.auth import AuthContext
from lks_idprovider.models.identity.client_identity import ClientIdentity
from lks_idprovider.models.identity.user import User
from lks_idprovider_fastapi.dependencies import get_auth_context, get_default_provider
from lks_idprovider_fastapi.security import get_bearer_token

# Import common fixtures and utilities
from .conftest import (
    MockClientProvider,
    MockUserProvider,
    override_bearer_token_factory,
    override_provider_factory,
)


@pytest.mark.parametrize(
    "token,expected_type,provider",
    [
        ("user_token", User, MockUserProvider()),  # pyright: ignore
        ("client_token", ClientIdentity, MockClientProvider()),  # pyright: ignore
    ],
)
def test_get_auth_context_returns_correct_identity(token, expected_type, provider):
    app = FastAPI()
    # Override dependencies properly - need to override the Union type dependency
    app.dependency_overrides[get_bearer_token] = lambda: token
    app.dependency_overrides[get_default_provider] = lambda: provider

    @app.get("/auth-context")
    async def route(ctx: AuthContext = Depends(get_auth_context)):
        return {"identity_type": type(ctx.identity).__name__}

    client = TestClient(app)
    resp = client.get("/auth-context", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["identity_type"] == expected_type.__name__


def test_get_auth_context_invalid_token():
    app = FastAPI()
    provider = MockUserProvider()  # type: ignore This will fail for invalid tokens
    app.dependency_overrides[get_bearer_token] = override_bearer_token_factory(
        "invalid"
    )
    app.dependency_overrides[get_default_provider] = override_provider_factory(provider)

    @app.get("/auth-context")
    async def route(ctx: AuthContext = Depends(get_auth_context)):
        return ctx

    client = TestClient(app)
    resp = client.get("/auth-context", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401
