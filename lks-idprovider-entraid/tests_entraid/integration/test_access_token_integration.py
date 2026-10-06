"""
Integration tests for Entra ID Provider with ACCESS_TOKEN mode.

These tests verify that the provider works correctly when configured to validate
access tokens (audience = api://{client_id}) instead of ID tokens.

Required Environment Variables:
    ENTRAID_TENANT_ID: Azure tenant ID
    ENTRAID_CLIENT_ID: Azure application (client) ID
    AZURE_TEST_ACCESS_TOKEN: Valid access token for your API
    AZURE_TEST_USERNAME: Test user UPN (optional, for ROPC tests)
    AZURE_TEST_PASSWORD: Test user password (optional, for ROPC tests)

To run these tests:
    pytest tests_entraid/integration/test_access_token_integration.py -v
"""

import os

import httpx
import pytest
from lks_idprovider.models.auth import AuthContext
from lks_idprovider.models.identity import User

from lks_idprovider_entraid import EntraIDConfig, EntraIDProvider, TokenType

# Check if integration tests should run
ENTRAID_TENANT_ID = os.getenv("ENTRAID_TENANT_ID")
ENTRAID_CLIENT_ID = os.getenv("ENTRAID_CLIENT_ID")
ENTRAID_CLIENT_SECRET = os.getenv("ENTRAID_CLIENT_SECRET")
AZURE_TEST_ACCESS_TOKEN = os.getenv("AZURE_TEST_ACCESS_TOKEN")
AZURE_TEST_USERNAME = os.getenv("AZURE_TEST_USERNAME")
AZURE_TEST_PASSWORD = os.getenv("AZURE_TEST_PASSWORD")

pytestmark = pytest.mark.skipif(
    not all([ENTRAID_TENANT_ID, ENTRAID_CLIENT_ID]),
    reason="Entra ID credentials not configured",
)


@pytest.fixture
def config():
    """Return an EntraIDConfig configured for ACCESS_TOKEN mode."""
    if not ENTRAID_TENANT_ID or not ENTRAID_CLIENT_ID:
        pytest.skip("Missing ENTRAID_TENANT_ID or ENTRAID_CLIENT_ID")

    return EntraIDConfig(
        tenant_id=ENTRAID_TENANT_ID,
        client_id=ENTRAID_CLIENT_ID,
        client_secret=ENTRAID_CLIENT_SECRET or "",
        token_type=TokenType.ACCESS_TOKEN,  # Accept access tokens
    )


@pytest.fixture
async def provider(config: EntraIDConfig):
    """Return an EntraIDProvider instance configured for access tokens."""
    provider = EntraIDProvider(config)
    async with provider:
        yield provider


def get_access_token_via_ropc(config, username, password):
    """
    Get an access token via ROPC flow for testing.

    Args:
        config: EntraIDConfig instance
        username: User's UPN
        password: User's password

    Returns:
        str: Access token or None
    """
    if not username or not password:
        return None

    token_endpoint = (
        f"https://login.microsoftonline.com/{config.tenant_id}/oauth2/v2.0/token"
    )

    # Request access token for YOUR API
    api_scope = f"api://{config.client_id}/access_as_user"

    data = {
        "grant_type": "password",
        "client_id": config.client_id,
        "username": username,
        "password": password,
        "scope": api_scope,
    }

    try:
        response = httpx.post(token_endpoint, data=data, timeout=30.0)
        response.raise_for_status()
        token_data = response.json()
        return token_data.get("access_token")
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None


# --- Tests ---


@pytest.mark.integration
@pytest.mark.asyncio
async def test_provider_initialization_with_access_token_mode(config):
    """Test that provider initializes correctly with ACCESS_TOKEN mode."""
    assert config.token_type == TokenType.ACCESS_TOKEN
    provider = EntraIDProvider(config)
    assert provider.config.token_type == TokenType.ACCESS_TOKEN


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not AZURE_TEST_ACCESS_TOKEN,
    reason="AZURE_TEST_ACCESS_TOKEN not provided",
)
async def test_validate_access_token(provider: EntraIDProvider):
    """Test validation of a real access token."""
    access_token = AZURE_TEST_ACCESS_TOKEN
    assert access_token is not None

    result = await provider.validate_token(access_token)

    assert result.is_valid is True
    assert result.error is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_id_token_should_fail_in_access_token_mode(
    provider: EntraIDProvider,
):
    """Test that ID tokens are rejected when in ACCESS_TOKEN mode."""
    # Get an ID token (which has aud = client_id)
    id_token = os.getenv("AZURE_TEST_USER_TOKEN")
    if not id_token:
        pytest.skip("AZURE_TEST_USER_TOKEN not available")

    result = await provider.validate_token(id_token)

    # Should fail because audience doesn't match api://{client_id}
    assert result.is_valid is False
    assert result.error is not None
    assert "audience" in result.error.lower() or "aud" in result.error.lower()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not AZURE_TEST_ACCESS_TOKEN,
    reason="AZURE_TEST_ACCESS_TOKEN not provided",
)
async def test_get_user_info_with_access_token(provider: EntraIDProvider):
    """
    Test getting user info with an access token.

    In ACCESS_TOKEN mode, user info is extracted from token claims.
    """
    access_token = AZURE_TEST_ACCESS_TOKEN
    assert access_token is not None

    user = await provider.get_user_info(access_token)

    assert isinstance(user, User)
    assert user.id is not None
    assert user.username is not None
    assert user.email is not None
    assert user.identity_type == "user"
    assert user.name is not None
    print(f"\n✅ User info retrieved: {user.name} ({user.username})")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not AZURE_TEST_ACCESS_TOKEN,
    reason="AZURE_TEST_ACCESS_TOKEN not provided",
)
async def test_get_auth_context_with_access_token(provider: EntraIDProvider):
    """Test getting complete auth context from an access token."""
    access_token = AZURE_TEST_ACCESS_TOKEN
    assert access_token is not None

    auth_context = await provider.get_auth_context(access_token)

    assert isinstance(auth_context, AuthContext)
    assert isinstance(auth_context.identity, User)
    assert auth_context.provider == "entra_id"
    assert auth_context.token_info is not None
    assert isinstance(auth_context.roles, list)
    print(f"\n✅ Auth context: {auth_context.identity.username}")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not all([AZURE_TEST_USERNAME, AZURE_TEST_PASSWORD]),
    reason="AZURE_TEST_USERNAME or AZURE_TEST_PASSWORD not provided",
)
async def test_ropc_flow_with_access_token(
    provider: EntraIDProvider, config: EntraIDConfig
):
    """Test complete flow using ROPC to get access token."""
    username = AZURE_TEST_USERNAME
    password = AZURE_TEST_PASSWORD

    assert username is not None
    assert password is not None

    # Get access token via ROPC
    access_token = get_access_token_via_ropc(config, username, password)

    if not access_token:
        pytest.skip("Could not obtain access token via ROPC")

    print("\n✅ Obtained access token via ROPC")

    # Validate token
    validation_result = await provider.validate_token(access_token)
    assert validation_result.is_valid is True

    # Get user info (should call Graph API)
    user = await provider.get_user_info(access_token)
    assert isinstance(user, User)
    assert user.username is not None
    assert user.username.lower() == username.lower()
    print(f"✅ User info: {user.name}")

    # Get auth context
    auth_context = await provider.get_auth_context(access_token)
    assert isinstance(auth_context, AuthContext)
    assert isinstance(auth_context.identity, User)
    print("✅ Auth context created successfully")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_access_token_rejected(provider: EntraIDProvider):
    """Test that invalid access tokens are properly rejected."""
    invalid_token = "invalid.access.token"

    result = await provider.validate_token(invalid_token)

    assert result.is_valid is False
    assert result.error is not None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not AZURE_TEST_ACCESS_TOKEN,
    reason="AZURE_TEST_ACCESS_TOKEN not provided",
)
async def test_access_token_has_correct_audience(provider: EntraIDProvider):
    """Test that access token has the correct audience (api://{client_id})."""
    from lks_idprovider_entraid.utils import decode_token_without_validation

    access_token = AZURE_TEST_ACCESS_TOKEN
    assert access_token is not None
    claims = decode_token_without_validation(access_token)

    expected_aud = f"api://{provider.config.client_id}"
    actual_aud = claims.get("aud")

    print(f"\n✅ Expected audience: {expected_aud}")
    print(f"✅ Actual audience: {actual_aud}")

    assert actual_aud == expected_aud, (
        f"Audience mismatch. Expected '{expected_aud}', got '{actual_aud}'"
    )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not AZURE_TEST_ACCESS_TOKEN,
    reason="AZURE_TEST_ACCESS_TOKEN not provided",
)
async def test_access_token_scopes(provider: EntraIDProvider):
    """Test that access token contains the expected scopes."""
    from lks_idprovider_entraid.utils import decode_token_without_validation

    access_token = AZURE_TEST_ACCESS_TOKEN
    assert access_token is not None
    claims = decode_token_without_validation(access_token)

    scopes = claims.get("scp", "").split() or claims.get("roles", [])

    print(f"\n✅ Token scopes: {scopes}")

    # Should have the access_as_user scope
    assert len(scopes) > 0, "Token should have at least one scope"
    assert "access_as_user" in scopes or any("access" in s.lower() for s in scopes), (
        "Token should have access_as_user scope"
    )
