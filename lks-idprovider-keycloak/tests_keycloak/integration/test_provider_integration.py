"""
Integration tests for KeycloakProvider.

These tests require a running Keycloak instance configured with the lks-test realm.
"""

import httpx
import pytest
from lks_idprovider.models import Role
from lks_idprovider.models.auth import AuthContext
from lks_idprovider.models.identity import User
from lks_idprovider.protocols import IdentityProvider

from lks_idprovider_keycloak.config import KeycloakConfig
from lks_idprovider_keycloak.provider import KeycloakProvider


@pytest.fixture
def config():
    """Return a KeycloakConfig instance for integration testing."""
    return KeycloakConfig(
        base_url="http://localhost:8080",
        realm="lks-test",
        client_id="PythonServiceTest",
        client_secret="python-service-secret-123",
    )


@pytest.fixture
def provider(config: KeycloakConfig) -> IdentityProvider:
    """Return a KeycloakProvider instance for integration testing."""
    return KeycloakProvider(config)


@pytest.fixture
def get_admin_access_token(config: KeycloakConfig):
    """Get a fresh access token for the admin user."""
    return get_access_token(config, "admin", "admin123")


def get_access_token(
    config: KeycloakConfig, username=None, password=None, client_credentials=False
) -> str:
    """Get an access token from Keycloak for testing."""
    token_url = f"{config.base_url}/realms/{config.realm}/protocol/openid-connect/token"
    data = {
        "client_id": config.client_id,
        "client_secret": config.client_secret,
    }
    if client_credentials:
        data["grant_type"] = "client_credentials"
    else:
        data["grant_type"] = "password"
        data["username"] = username
        data["password"] = password
        data["scope"] = "openid"
    response = httpx.post(token_url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_get_user_info_with_valid_token(
    provider: IdentityProvider, config: KeycloakConfig
):
    """Test get_user_info returns correct User for a real token from Keycloak."""
    # Arrange: Get a real access token for testuser
    access_token = get_access_token(config, "testuser", "password123")

    # Act
    user = await provider.get_user_info(access_token)

    # Assert
    assert isinstance(user, User)
    assert user.username == "testuser"
    assert user.email == "testuser@lks.com"
    assert user.first_name == "Test"
    assert user.last_name == "User"


@pytest.mark.asyncio
async def test_validate_token_with_valid_token(
    provider: IdentityProvider, config: KeycloakConfig
):
    """Test that a valid token is correctly validated
    against a live Keycloak instance."""
    # Arrange: Get a real access token from Keycloak
    access_token = get_access_token(config, "testuser", "password123")

    # Act
    result = await provider.validate_token(access_token)

    # Assert
    assert result.is_valid is True


@pytest.mark.asyncio
async def test_validate_token_and_get_user_info_sequence(
    provider: IdentityProvider, config: KeycloakConfig
):
    """Test both validate_token and get_user_info in sequence with the same token."""
    access_token = get_access_token(config, "testuser", "password123")

    # First, validate the token
    result = await provider.validate_token(access_token)
    assert result.is_valid is True

    # Then, get user info
    user = await provider.get_user_info(access_token)
    assert isinstance(user, User)
    assert user.username == "testuser"
    assert user.email == "testuser@lks.com"
    assert user.first_name == "Test"
    assert user.last_name == "User"


@pytest.mark.asyncio
async def test_get_user_roles_with_valid_token(
    provider: IdentityProvider, config: KeycloakConfig
):
    """Test get_user_roles returns correct roles for a real token from Keycloak."""
    access_token = get_access_token(config, "testuser", "password123")

    roles = await provider.get_user_roles(access_token)
    assert any(r.name == "user" and r.client is None for r in roles)  # realm role
    assert any(
        r.name == "read" and r.client == "PythonServiceTest" for r in roles
    )  # client role
    assert any(
        r.name == "write" and r.client == "PythonServiceTest" for r in roles
    )  # client role
    assert all(isinstance(r, Role) for r in roles)


@pytest.mark.asyncio
async def test_get_user_roles_with_admin_token(
    provider: IdentityProvider, config: KeycloakConfig, get_admin_access_token: str
):
    """Test get_user_roles returns correct roles for the admin user from Keycloak."""
    access_token = get_admin_access_token
    roles = await provider.get_user_roles(access_token)
    # Realm roles
    assert any(r.name == "admin" and r.client is None for r in roles)
    assert any(r.name == "user" and r.client is None for r in roles)
    # Client roles for PythonServiceTest
    assert any(r.name == "admin" and r.client == "PythonServiceTest" for r in roles)
    assert any(r.name == "read" and r.client == "PythonServiceTest" for r in roles)
    assert any(r.name == "write" and r.client == "PythonServiceTest" for r in roles)
    # Client role for realm-management
    assert any(
        r.name == "realm-admin" and r.client == "realm-management" for r in roles
    )


@pytest.mark.asyncio
async def test_get_auth_context_with_valid_token(
    provider: IdentityProvider, config: KeycloakConfig
):
    """Test get_auth_context returns correct AuthContext for a real token."""
    access_token = get_access_token(config, "testuser", "password123")

    auth_context = await provider.get_auth_context(access_token)
    assert isinstance(auth_context, AuthContext)
    if isinstance(auth_context.identity, User):
        assert auth_context.identity.name == "testuser"
        assert auth_context.identity.email == "testuser@lks.com"
    assert any(r.name == "user" and r.client is None for r in auth_context.roles)
    assert any(
        r.name == "read" and r.client == "PythonServiceTest" for r in auth_context.roles
    )
    assert any(
        r.name == "write" and r.client == "PythonServiceTest"
        for r in auth_context.roles
    )
