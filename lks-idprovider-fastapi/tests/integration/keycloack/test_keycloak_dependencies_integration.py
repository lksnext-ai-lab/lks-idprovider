import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from lks_idprovider_fastapi.dependencies import (
    get_auth_context,
    get_default_provider,
    login_required,
    requires_any_role,
    requires_role,
)
from tests.conftest import get_access_token


# --- Real Keycloak provider factories (from test_fastapi_auth_context) ---
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


# --- App factory for dependency override ---
def make_app(provider_factory):
    app = FastAPI()
    app.dependency_overrides[get_default_provider] = provider_factory

    @app.get("/auth-context")
    async def route(ctx=Depends(get_auth_context)):
        return {
            "identity_type": type(ctx.identity).__name__,
            "identity": ctx.identity.model_dump(),
            "roles": [r.model_dump() for r in ctx.roles],
        }

    @app.get("/login-required")
    async def login_route(ctx=Depends(login_required)):
        return {"identity_type": type(ctx.identity).__name__}

    @app.get("/admin")
    async def admin_route(ctx=Depends(requires_role("admin"))):
        return {"message": "admin access"}

    @app.get("/manager")
    async def manager_route(
        ctx=Depends(requires_role("write", client="PythonServiceTest")),
    ):
        return {"message": "manager access"}

    @app.get("/editor-or-admin")
    async def editor_route(ctx=Depends(requires_any_role("editor", "admin"))):
        return {"message": "editor or admin access"}

    return app


# --- Integration tests ---
def test_auth_context_user():
    client = TestClient(make_app(get_real_user_provider))
    provider = get_real_user_provider()
    config = provider.config
    user_token = get_access_token(config, username="testuser", password="password123")
    resp = client.get(
        "/auth-context", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["identity_type"] == "User"


def test_auth_context_client():
    client = TestClient(make_app(get_real_client_provider))
    provider = get_real_client_provider()
    config = provider.config
    client_token = get_access_token(config, client_credentials=True)
    resp = client.get(
        "/auth-context", headers={"Authorization": f"Bearer {client_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["identity_type"] == "ClientIdentity"


def test_auth_context_invalid_token():
    client = TestClient(make_app(get_real_user_provider))
    resp = client.get("/auth-context", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401


def test_login_required_user():
    client = TestClient(make_app(get_real_user_provider))
    provider = get_real_user_provider()
    config = provider.config
    user_token = get_access_token(config, username="testuser", password="password123")
    resp = client.get(
        "/login-required", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["identity_type"] == "User"


def test_login_required_invalid():
    client = TestClient(make_app(get_real_user_provider))
    resp = client.get("/login-required", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401


def test_requires_role_admin_success():
    client = TestClient(make_app(get_real_user_provider))
    provider = get_real_user_provider()
    config = provider.config
    user_token = get_access_token(config, username="admin", password="admin123")
    resp = client.get("/admin", headers={"Authorization": f"Bearer {user_token}"})
    # Only pass if testuser has admin role in Keycloak
    if resp.status_code == 200:
        assert resp.json()["message"] == "admin access"
    else:
        pytest.fail("Either the test case or the test is wrong: 403")


def test_requires_role_admin_failure():
    client = TestClient(make_app(get_real_user_provider))
    provider = get_real_user_provider()
    config = provider.config
    # Use a user without admin role if possible, else expect 403
    user_token = get_access_token(config, username="testuser", password="password123")
    resp = client.get("/admin", headers={"Authorization": f"Bearer {user_token}"})
    if resp.status_code == 403:
        assert "Required role 'admin'" in resp.json()["detail"]
    else:
        # If testuser has admin, this is not a failure
        pytest.fail("Either the test case or the test is wrong: 403")


def test_requires_role_manager_client_success():
    client = TestClient(make_app(get_real_user_provider))
    provider = get_real_user_provider()
    config = provider.config
    user_token = get_access_token(config, username="testuser", password="password123")
    resp = client.get("/manager", headers={"Authorization": f"Bearer {user_token}"})
    if resp.status_code == 200:
        assert resp.json()["message"] == "manager access"
    else:
        pytest.fail("Either the test case or the test is wrong: 403")


def test_requires_any_role_success():
    client = TestClient(make_app(get_real_user_provider))
    provider = get_real_user_provider()
    config = provider.config
    user_token = get_access_token(config, username="admin", password="admin123")
    resp = client.get(
        "/editor-or-admin", headers={"Authorization": f"Bearer {user_token}"}
    )
    if resp.status_code == 200:
        assert resp.json()["message"] == "editor or admin access"
    else:
        pytest.fail("Either the test case or the test is wrong: 403")


def test_requires_any_role_failure():
    client = TestClient(make_app(get_real_user_provider))
    provider = get_real_user_provider()
    config = provider.config
    # Use a user with no editor/admin roles if possible
    user_token = get_access_token(config, username="testuser", password="password123")
    resp = client.get(
        "/editor-or-admin", headers={"Authorization": f"Bearer {user_token}"}
    )
    if resp.status_code == 403:
        assert "At least one of roles" in resp.json()["detail"]
    else:
        pytest.fail("Either the test case or the test is wrong: 403")
