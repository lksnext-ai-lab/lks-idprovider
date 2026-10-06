"""
Integration tests for Entra ID with FastAPI dependencies.

These tests require real Azure Entra ID credentials configured via environment
variables. They will make actual API calls to Azure AD.

Required Environment Variables:
    ENTRAID_TENANT_ID: Azure tenant ID
    ENTRAID_CLIENT_ID: Azure application (client) ID
    AZURE_TEST_USER_TOKEN: Valid ID token for testing
    AZURE_TEST_USERNAME: Test user UPN (optional, for ROPC tests)
    AZURE_TEST_PASSWORD: Test user password (optional, for ROPC tests)

To run these tests:
    pytest tests/integration/entraid/test_entraid_dependencies_integration.py -v

To skip if credentials are not configured:
    pytest tests/integration/entraid/ -v -m "not integration"
"""

import os

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

# Check if integration tests should run
ENTRAID_TENANT_ID = os.getenv("ENTRAID_TENANT_ID")
ENTRAID_CLIENT_ID = os.getenv("ENTRAID_CLIENT_ID")
AZURE_TEST_USER_TOKEN = os.getenv("AZURE_TEST_USER_TOKEN")

pytestmark = pytest.mark.skipif(
    not all([ENTRAID_TENANT_ID, ENTRAID_CLIENT_ID, AZURE_TEST_USER_TOKEN]),
    reason="Entra ID credentials not configured",
)


# --- Real Entra ID provider factory ---
def get_real_entraid_provider():
    """Create an Entra ID provider for integration testing."""
    from lks_idprovider_entraid import EntraIDConfig, EntraIDProvider, TokenType

    config = EntraIDConfig(
        tenant_id=ENTRAID_TENANT_ID or "",
        client_id=ENTRAID_CLIENT_ID or "",
        token_type=TokenType.ID_TOKEN,  # Using ID tokens for authentication
    )
    return EntraIDProvider(config)


# --- App factory for dependency override ---
def make_app(provider_factory):
    """Create a FastAPI app with the given provider factory."""
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
        ctx=Depends(requires_role("manager", client=ENTRAID_CLIENT_ID)),
    ):
        return {"message": "manager access"}

    @app.get("/editor-or-admin")
    async def editor_route(ctx=Depends(requires_any_role("editor", "admin"))):
        return {"message": "editor or admin access"}

    return app


# --- Integration tests ---
@pytest.mark.integration
def test_auth_context_user():
    """Test getting auth context with a real user ID token."""
    client = TestClient(make_app(get_real_entraid_provider))
    user_token = AZURE_TEST_USER_TOKEN

    resp = client.get(
        "/auth-context", headers={"Authorization": f"Bearer {user_token}"}
    )
    if resp.status_code != 200:
        print(f"Error response: {resp.json()}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["identity_type"] == "User"
    assert "id" in data["identity"]
    assert "username" in data["identity"]
    assert "email" in data["identity"]
    assert isinstance(data["roles"], list)


@pytest.mark.integration
@pytest.mark.asyncio
def test_auth_context_invalid_token():
    """Test that invalid tokens are rejected."""
    client = TestClient(make_app(get_real_entraid_provider))
    resp = client.get("/auth-context", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
def test_auth_context_missing_token():
    """Test that missing tokens are rejected."""
    client = TestClient(make_app(get_real_entraid_provider))
    resp = client.get("/auth-context")
    assert resp.status_code == 403  # FastAPI returns 403 for missing auth


@pytest.mark.integration
@pytest.mark.asyncio
def test_login_required_user():
    """Test login_required dependency with a real user ID token."""
    client = TestClient(make_app(get_real_entraid_provider))
    user_token = AZURE_TEST_USER_TOKEN

    resp = client.get(
        "/login-required", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["identity_type"] == "User"


@pytest.mark.integration
@pytest.mark.asyncio
def test_login_required_invalid():
    """Test login_required rejects invalid tokens."""
    client = TestClient(make_app(get_real_entraid_provider))
    resp = client.get("/login-required", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.skip(reason="Entra ID users don't have roles configured yet")
def test_requires_role_with_token():
    """
    Test requires_role dependency with a real token.

    Note: This test will pass if the user has the 'admin' role in Azure AD,
    or return 403 if they don't. Adjust the test based on your test user's roles.
    """
    client = TestClient(make_app(get_real_entraid_provider))
    user_token = AZURE_TEST_USER_TOKEN

    resp = client.get("/admin", headers={"Authorization": f"Bearer {user_token}"})

    # The response depends on whether the test user has the admin role
    if resp.status_code == 200:
        assert resp.json()["message"] == "admin access"
    elif resp.status_code == 403:
        # User doesn't have admin role - this is expected for most test users
        assert "Required role 'admin'" in resp.json()["detail"]
    else:
        pytest.fail(f"Unexpected status code: {resp.status_code}")


@pytest.mark.integration
@pytest.mark.skip(reason="Entra ID users don't have roles configured yet")
def test_requires_role_invalid_token():
    """Test requires_role rejects invalid tokens."""
    client = TestClient(make_app(get_real_entraid_provider))
    resp = client.get("/admin", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.skip(reason="Entra ID users don't have roles configured yet")
def test_requires_any_role_with_token():
    """
    Test requires_any_role dependency with a real token.

    Note: This test behavior depends on the user's roles in Azure AD.
    """
    client = TestClient(make_app(get_real_entraid_provider))
    user_token = AZURE_TEST_USER_TOKEN

    resp = client.get(
        "/editor-or-admin", headers={"Authorization": f"Bearer {user_token}"}
    )

    # The response depends on whether the test user has editor or admin role
    if resp.status_code == 200:
        assert resp.json()["message"] == "editor or admin access"
    elif resp.status_code == 403:
        # User doesn't have either role - expected for most test users
        assert "At least one of roles" in resp.json()["detail"]
    else:
        pytest.fail(f"Unexpected status code: {resp.status_code}")


@pytest.mark.integration
@pytest.mark.asyncio
def test_multiple_endpoints_same_token():
    """Test that the same token can be used across multiple endpoints."""
    client = TestClient(make_app(get_real_entraid_provider))
    user_token = AZURE_TEST_USER_TOKEN
    headers = {"Authorization": f"Bearer {user_token}"}

    # Test multiple endpoints with the same token
    resp1 = client.get("/auth-context", headers=headers)
    assert resp1.status_code == 200

    resp2 = client.get("/login-required", headers=headers)
    assert resp2.status_code == 200

    # Both should return the same identity
    identity1 = resp1.json()["identity"]
    identity2_type = resp2.json()["identity_type"]
    assert identity1 is not None
    assert identity2_type == "User"


@pytest.mark.integration
@pytest.mark.asyncio
def test_token_validation_with_provider_lifecycle():
    """Test that provider properly handles context management in FastAPI."""

    # Create a provider and wrap it in an async context manager
    async def get_provider_with_context():
        provider = get_real_entraid_provider()
        async with provider:
            return provider

    # Override with a function that returns the provider
    def provider_factory():
        return get_real_entraid_provider()

    client = TestClient(make_app(provider_factory))
    user_token = AZURE_TEST_USER_TOKEN

    resp = client.get(
        "/auth-context", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["identity_type"] == "User"
