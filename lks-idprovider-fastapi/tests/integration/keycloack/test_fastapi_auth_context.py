from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from lks_idprovider_fastapi.dependencies import get_auth_context, get_default_provider
from tests.conftest import get_access_token


def get_real_user_provider():
    from lks_idprovider_keycloak.config import KeycloakConfig
    from lks_idprovider_keycloak.provider import KeycloakProvider

    config = KeycloakConfig(
        base_url="http://localhost:8080",
        realm="lks-test",
        client_id="PythonServiceTest",
        client_secret="python-service-secret-123",
    )
    return KeycloakProvider(config)


def get_real_client_provider():
    from lks_idprovider_keycloak.client_credentials_provider import (
        KeycloakClientCredentialsProvider,
    )
    from lks_idprovider_keycloak.config import KeycloakConfig

    config = KeycloakConfig(
        base_url="http://localhost:8080",
        realm="lks-test",
        client_id="PythonServiceTest",
        client_secret="python-service-secret-123",
    )
    return KeycloakClientCredentialsProvider(config)


def make_app(provider_factory):
    app = FastAPI()

    # Override the provider dependency with our test provider
    app.dependency_overrides[get_default_provider] = provider_factory

    @app.get("/auth-context")
    async def route(ctx=Depends(get_auth_context)):
        return {
            "identity_type": type(ctx.identity).__name__,
            "identity": ctx.identity.model_dump(),
            "roles": [r.model_dump() for r in ctx.roles],
        }

    return app


def test_user_token_flow():
    client = TestClient(make_app(get_real_user_provider))
    provider = get_real_user_provider()
    config = provider.config
    user_token = get_access_token(config, username="testuser", password="password123")
    resp = client.get(
        "/auth-context", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["identity_type"] == "User"


def test_client_token_flow():
    client = TestClient(make_app(get_real_client_provider))
    provider = get_real_client_provider()
    config = provider.config
    client_token = get_access_token(config, client_credentials=True)
    resp = client.get(
        "/auth-context", headers={"Authorization": f"Bearer {client_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["identity_type"] == "ClientIdentity"


def test_invalid_token():
    client = TestClient(make_app(get_real_user_provider))
    resp = client.get("/auth-context", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401
