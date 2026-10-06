"""
Integration tests for EntraIDProvider.

These tests require real Azure Entra ID credentials configured via environment
variables. They will make actual API calls to Azure AD.

IMPORTANT: These tests are configured to work with ID tokens (OIDC flow),
which is the default and recommended approach for authentication scenarios.

Required Environment Variables:
    ENTRAID_TENANT_ID: Azure tenant ID
    ENTRAID_CLIENT_ID: Azure application (client) ID
    ENTRAID_CLIENT_SECRET: Azure application client secret (optional for some tests)
    AZURE_TEST_USER_TOKEN: Valid ID token for testing
    AZURE_TEST_USERNAME: Test user UPN for ROPC tests (optional)
    AZURE_TEST_PASSWORD: Test user password for ROPC tests (optional)

To run these tests:
    pytest tests_entraid/integration/test_provider_integration.py -v

To skip if credentials are not configured:
    pytest tests_entraid/integration/ -v -m "not integration"
"""

import os
from collections.abc import AsyncGenerator

import httpx
import pytest
from lks_idprovider.models.auth import AuthContext
from lks_idprovider.models.identity import User

from lks_idprovider_entraid import EntraIDConfig, EntraIDProvider

# Check if integration tests should run
ENTRAID_TENANT_ID = os.getenv("ENTRAID_TENANT_ID")
ENTRAID_CLIENT_ID = os.getenv("ENTRAID_CLIENT_ID")
ENTRAID_CLIENT_SECRET = os.getenv("ENTRAID_CLIENT_SECRET")

skip_integration = not all(
    [ENTRAID_TENANT_ID, ENTRAID_CLIENT_ID, ENTRAID_CLIENT_SECRET]
)
skip_reason = (
    "Azure credentials not configured. Set ENTRAID_TENANT_ID, "
    "ENTRAID_CLIENT_ID, and ENTRAID_CLIENT_SECRET environment variables."
)


@pytest.fixture
def config() -> EntraIDConfig:
    """Return an EntraIDConfig instance for integration testing.

    Configured to accept ID tokens (default OIDC flow).
    """
    if skip_integration:
        pytest.skip(skip_reason)

    from lks_idprovider_entraid import TokenType

    # Validate required environment variables
    if not ENTRAID_TENANT_ID or not ENTRAID_CLIENT_ID:
        pytest.skip("Missing ENTRAID_TENANT_ID or ENTRAID_CLIENT_ID")

    return EntraIDConfig(
        tenant_id=ENTRAID_TENANT_ID,
        client_id=ENTRAID_CLIENT_ID,
        client_secret=ENTRAID_CLIENT_SECRET or "",
        token_type=TokenType.ID_TOKEN,  # Accept ID tokens
    )


@pytest.fixture
async def provider(
    config: EntraIDConfig,
) -> AsyncGenerator[EntraIDProvider, None]:
    """Return an EntraIDProvider instance for integration testing."""
    provider = EntraIDProvider(config)
    async with provider:
        yield provider


def get_client_credentials_token(config: EntraIDConfig) -> str:
    """Get an access token using client credentials flow.

    This simulates a service-to-service authentication scenario.
    The token will have application permissions, not user permissions.
    """
    token_url = config.token_endpoint

    data = {
        "grant_type": "client_credentials",
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }

    response = httpx.post(token_url, data=data, timeout=30.0)
    response.raise_for_status()
    return response.json()["access_token"]


def get_id_token_via_ropc(
    config: EntraIDConfig,
    username: str,
    password: str,
    scope: str = "openid profile email offline_access",
) -> str | None:
    """Get an ID token using Resource Owner Password Credentials flow.

    WARNING: ROPC is not recommended for production use. It's only used here
    for testing purposes. In production, use interactive authentication flows.

    This flow must be explicitly enabled in Azure AD and the user account
    must not have MFA enabled.

    Returns:
        ID token (not access token) for authentication purposes.
    """
    token_url = config.token_endpoint

    data = {
        "grant_type": "password",
        "client_id": config.client_id,
        "username": username,
        "password": password,
        "scope": scope,
    }

    try:
        response = httpx.post(token_url, data=data, timeout=30.0)
        response.raise_for_status()
        token_response = response.json()
        # Return ID token instead of access token
        return token_response.get("id_token")
    except httpx.HTTPStatusError as e:
        pytest.skip(
            f"Could not get ID token via ROPC. "
            f"Error: {e.response.status_code} - {e.response.text}. "
            f"ROPC may not be enabled or user may have MFA."
        )
        return None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_connection_to_azure_ad(provider: EntraIDProvider):
    """Test that we can connect to Azure AD and retrieve well-known config."""
    # This test verifies basic connectivity to Azure AD
    result = await provider.test_connection()
    assert result is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_well_known_config(provider: EntraIDProvider):
    """Test retrieving OpenID Connect discovery document."""
    config = await provider.get_well_known_config()

    assert config is not None
    assert "token_endpoint" in config
    assert "authorization_endpoint" in config
    assert "jwks_uri" in config
    assert "issuer" in config


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check(provider: EntraIDProvider):
    """Test provider health check."""
    health = await provider.health_check()

    assert health["status"] == "healthy"
    assert health["provider"] == "entra_id"
    assert health["endpoints_accessible"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_provider_info(provider: EntraIDProvider):
    """Test getting provider metadata."""
    info = await provider.get_provider_info()

    assert info["name"] == "entra_id"
    assert info["display_name"] == "Azure Entra ID"
    assert "version" in info
    assert info["supports_user_tokens"] is True
    assert info["supports_app_tokens"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_client_credentials_token(
    provider: EntraIDProvider, config: EntraIDConfig
):
    """Test validation of a real client credentials token.

    NOTE: This test is skipped when token_type=ID_TOKEN because client
    credentials tokens are access tokens for Graph API, not ID tokens.
    Client credentials flow is only tested with token_type=ACCESS_TOKEN.
    """
    from lks_idprovider_entraid import TokenType

    if config.token_type == TokenType.ID_TOKEN:
        pytest.skip("Client credentials test skipped for ID_TOKEN mode")

    # Get a token using client credentials
    access_token = get_client_credentials_token(config)

    # Validate it
    result = await provider.validate_token(access_token)

    assert result.is_valid is True
    assert result.token_info is not None
    assert result.token_info.token == access_token
    assert result.error is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_expired_token(provider: EntraIDProvider):
    """Test validation of an expired token."""
    # This is a deliberately expired token (you'd need to provide one)
    # For now, we'll use a malformed token to test error handling
    expired_token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MzAwMDAwMDB9.invalid"
    )

    result = await provider.validate_token(expired_token)

    assert result.is_valid is False
    assert result.error is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_user_roles_from_token(
    provider: EntraIDProvider, config: EntraIDConfig
):
    """Test extracting roles from a client credentials token."""
    access_token = get_client_credentials_token(config)

    # Get roles from the token
    roles = await provider.get_user_roles(access_token)

    # Client credentials tokens should have application roles
    assert isinstance(roles, list)
    # Note: The actual roles depend on what's configured in Azure AD
    # We just verify the method works and returns a list


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("AZURE_TEST_USER_TOKEN"), reason="AZURE_TEST_USER_TOKEN not provided"
)
async def test_get_user_info_with_user_token(provider: EntraIDProvider):
    """Test getting user info from a real ID token.

    This test requires AZURE_TEST_USER_TOKEN environment variable
    containing a valid ID token (can be obtained via get_id_token.py script).
    """
    id_token = os.getenv("AZURE_TEST_USER_TOKEN")
    assert id_token is not None, "AZURE_TEST_USER_TOKEN is required"

    # Get user info
    user = await provider.get_user_info(id_token)

    assert isinstance(user, User)
    assert user.id is not None
    assert user.username is not None
    assert user.email is not None
    assert user.identity_type == "user"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("AZURE_TEST_USER_TOKEN"), reason="AZURE_TEST_USER_TOKEN not provided"
)
async def test_validate_user_token(provider: EntraIDProvider):
    """Test validation of a real ID token."""
    id_token = os.getenv("AZURE_TEST_USER_TOKEN")
    assert id_token is not None, "AZURE_TEST_USER_TOKEN is required"

    result = await provider.validate_token(id_token)

    assert result.is_valid is True
    assert result.token_info is not None
    assert result.error is None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("AZURE_TEST_USER_TOKEN"), reason="AZURE_TEST_USER_TOKEN not provided"
)
async def test_get_auth_context_with_user_token(provider: EntraIDProvider):
    """Test getting complete auth context from an ID token."""
    id_token = os.getenv("AZURE_TEST_USER_TOKEN")
    assert id_token is not None, "AZURE_TEST_USER_TOKEN is required"

    auth_context = await provider.get_auth_context(id_token)

    assert isinstance(auth_context, AuthContext)
    assert isinstance(auth_context.identity, User)
    assert auth_context.provider == "entra_id"
    assert auth_context.token_info is not None
    assert isinstance(auth_context.roles, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_token_validation(provider: EntraIDProvider):
    """Test validation of an invalid/malformed token."""
    invalid_token = "this.is.not.a.valid.jwt"

    result = await provider.validate_token(invalid_token)

    assert result.is_valid is False
    assert result.error is not None
    assert "decode" in result.error.lower() or "invalid" in result.error.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tenant_info(provider: EntraIDProvider, config: EntraIDConfig):
    """Test getting tenant information."""
    tenant_info = provider.get_tenant_info()

    assert tenant_info["tenant_id"] == config.tenant_id
    assert tenant_info["client_id"] == config.client_id
    assert tenant_info["authority"] == config.authority


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not all([os.getenv("AZURE_TEST_USERNAME"), os.getenv("AZURE_TEST_PASSWORD")]),
    reason="AZURE_TEST_USERNAME and AZURE_TEST_PASSWORD not provided",
)
async def test_ropc_flow_full_scenario(
    provider: EntraIDProvider, config: EntraIDConfig
):
    """Test complete flow using ROPC to get user token.

    WARNING: This test requires ROPC to be enabled in Azure AD
    and the test user must not have MFA enabled.

    Set environment variables:
    - AZURE_TEST_USERNAME: Test user's UPN (e.g., user@tenant.com)
    - AZURE_TEST_PASSWORD: Test user's password
    """
    username = os.getenv("AZURE_TEST_USERNAME")
    password = os.getenv("AZURE_TEST_PASSWORD")

    assert username is not None, "AZURE_TEST_USERNAME is required"
    assert password is not None, "AZURE_TEST_PASSWORD is required"

    # Get ID token via ROPC
    id_token = get_id_token_via_ropc(config, username, password)

    if not id_token:
        pytest.skip("Could not obtain ID token via ROPC")

    # Validate token
    validation_result = await provider.validate_token(id_token)
    assert validation_result.is_valid is True

    # Get user info
    user = await provider.get_user_info(id_token)
    assert isinstance(user, User)
    assert user.username is not None
    assert user.username.lower() == username.lower()

    # Get roles
    roles = await provider.get_user_roles(id_token)
    assert isinstance(roles, list)

    # Get full auth context
    auth_context = await provider.get_auth_context(id_token)
    assert isinstance(auth_context, AuthContext)
    assert isinstance(auth_context.identity, User)
    assert auth_context.identity.username.lower() == username.lower()
