"""
Unit tests for Entra ID Provider.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from lks_idprovider.models.errors.provider import ProviderError

# >=32 bytes so pyjwt does not emit InsecureKeyLengthWarning for HS256.
TEST_HMAC_KEY = "entraid-unit-test-hmac-signing-key"


@pytest.mark.asyncio
async def test_provider_initialization(entraid_config):
    """Test provider initialization."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    provider = EntraIDProvider(entraid_config)

    assert provider.config == entraid_config
    assert provider.get_provider_name() == "entra_id"


@pytest.mark.asyncio
async def test_provider_context_manager(entraid_config):
    """Test provider as async context manager."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    provider = EntraIDProvider(entraid_config)

    async with provider:
        assert provider._http_client is not None
        assert provider._jwks_client is not None

    # After exit, http client should be closed (checked in credential client)


@pytest.mark.asyncio
async def test_get_tenant_info(entraid_config):
    """Test getting tenant information."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    provider = EntraIDProvider(entraid_config)
    info = provider.get_tenant_info()

    assert info["tenant_id"] == entraid_config.tenant_id
    assert info["client_id"] == entraid_config.client_id
    assert info["authority"] == entraid_config.authority
    assert info["api_version"] == entraid_config.api_version


@pytest.mark.asyncio
async def test_get_well_known_config(entraid_config, mock_well_known_config):
    """Test getting well-known configuration."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    provider = EntraIDProvider(entraid_config)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_well_known_config
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        config = await provider.get_well_known_config()

        assert config == mock_well_known_config
        assert provider._well_known_config == mock_well_known_config


@pytest.mark.asyncio
async def test_get_well_known_config_cached(entraid_config, mock_well_known_config):
    """Test well-known configuration caching."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    provider = EntraIDProvider(entraid_config)
    provider._well_known_config = mock_well_known_config

    config = await provider.get_well_known_config()

    assert config == mock_well_known_config
    # Should not make HTTP request (no need to mock httpx)


@pytest.mark.asyncio
async def test_validate_token_success(entraid_config, sample_token_claims):
    """Test successful token validation."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    # Create a real JWT token
    token = jwt.encode(sample_token_claims, TEST_HMAC_KEY, algorithm="HS256")

    provider = EntraIDProvider(entraid_config)

    with patch("lks_idprovider_entraid.provider.PyJWKClient") as mock_jwks_class:
        # Mock JWKS client
        mock_jwks_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = TEST_HMAC_KEY
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwks_class.return_value = mock_jwks_client

        with patch("jwt.decode", return_value=sample_token_claims):
            result = await provider.validate_token(token)

        assert result.is_valid
        assert result.token_info is not None
        assert result.token_info.subject == sample_token_claims["sub"]
        assert result.error is None


@pytest.mark.asyncio
async def test_validate_token_expired(entraid_config):
    """Test validation of expired token."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    claims = {
        "sub": "user123",
        "exp": 1234567890,  # Old timestamp
        "iat": 1234567890,
        "aud": "test-client-id",
        "iss": "https://login.microsoftonline.com/test-tenant-id/v2.0",
    }
    token = jwt.encode(claims, TEST_HMAC_KEY, algorithm="HS256")

    provider = EntraIDProvider(entraid_config)

    with patch("lks_idprovider_entraid.provider.PyJWKClient") as mock_jwks_class:
        mock_jwks_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = TEST_HMAC_KEY
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwks_class.return_value = mock_jwks_client

        with patch("jwt.decode", side_effect=jwt.ExpiredSignatureError()):
            result = await provider.validate_token(token)

        assert not result.is_valid
        assert result.error is not None
        assert "expired" in result.error.lower()


@pytest.mark.asyncio
async def test_validate_token_invalid_signature(entraid_config):
    """Test validation of token with invalid signature."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    claims = {"sub": "user123", "exp": 9999999999}
    token = jwt.encode(claims, TEST_HMAC_KEY, algorithm="HS256")

    provider = EntraIDProvider(entraid_config)

    with patch("lks_idprovider_entraid.provider.PyJWKClient") as mock_jwks_class:
        mock_jwks_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = "wrong-secret"
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwks_class.return_value = mock_jwks_client

        with patch("jwt.decode", side_effect=jwt.InvalidSignatureError()):
            result = await provider.validate_token(token)

        assert not result.is_valid
        assert result.error is not None
        assert "signature" in result.error.lower()


@pytest.mark.asyncio
async def test_get_user_info(
    entraid_config, mock_graph_user_response, sample_token_claims
):
    """Test getting user information."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    token = jwt.encode(sample_token_claims, TEST_HMAC_KEY, algorithm="HS256")

    provider = EntraIDProvider(entraid_config)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_graph_user_response
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        user = await provider.get_user_info(token)

        assert user.id == mock_graph_user_response["id"]
        assert user.username == mock_graph_user_response["userPrincipalName"]
        assert user.email == mock_graph_user_response["mail"]


@pytest.mark.asyncio
async def test_get_user_info_error(entraid_config):
    """Test error handling in get_user_info with invalid token."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    token = "invalid-token"

    provider = EntraIDProvider(entraid_config)

    # Invalid token should raise ProviderError during decoding
    with pytest.raises(ProviderError, match="Error getting user info"):
        await provider.get_user_info(token)


@pytest.mark.asyncio
async def test_get_user_roles(entraid_config, sample_token_claims):
    """Test extracting user roles from token."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    token = jwt.encode(sample_token_claims, TEST_HMAC_KEY, algorithm="HS256")

    provider = EntraIDProvider(entraid_config)
    roles = await provider.get_user_roles(token)

    assert len(roles) == 2
    assert roles[0].name == "AdminRole"
    assert roles[1].name == "UserRole"


@pytest.mark.asyncio
async def test_get_auth_context(
    entraid_config, sample_token_claims, mock_graph_user_response
):
    """Test getting complete auth context."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    token = jwt.encode(sample_token_claims, TEST_HMAC_KEY, algorithm="HS256")

    provider = EntraIDProvider(entraid_config)

    with patch("lks_idprovider_entraid.provider.PyJWKClient") as mock_jwks_class:
        mock_jwks_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = TEST_HMAC_KEY
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwks_class.return_value = mock_jwks_client

        with patch("jwt.decode", return_value=sample_token_claims):
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_response = MagicMock()
                mock_response.json.return_value = mock_graph_user_response
                mock_response.raise_for_status = MagicMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client_class.return_value = mock_client

                auth_context = await provider.get_auth_context(token)

        assert auth_context.identity.id == mock_graph_user_response["id"]
        assert len(auth_context.roles) == 2
        assert auth_context.provider == "entra_id"
        assert auth_context.token_info is not None


@pytest.mark.asyncio
async def test_get_auth_context_invalid_token(entraid_config):
    """Test auth context with invalid token."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    token = "invalid-token"

    provider = EntraIDProvider(entraid_config)

    with patch("lks_idprovider_entraid.provider.PyJWKClient") as mock_jwks_class:
        mock_jwks_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = TEST_HMAC_KEY
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwks_class.return_value = mock_jwks_client

        with patch("jwt.decode", side_effect=jwt.DecodeError()):
            with pytest.raises(ProviderError, match="Invalid token"):
                await provider.get_auth_context(token)


@pytest.mark.asyncio
async def test_health_check_healthy(entraid_config, mock_well_known_config):
    """Test health check when provider is healthy."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    provider = EntraIDProvider(entraid_config)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_well_known_config
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        health = await provider.health_check()

        assert health["status"] == "healthy"
        assert health["provider"] == "entra_id"
        assert health["endpoints_accessible"] is True


@pytest.mark.asyncio
async def test_health_check_unhealthy(entraid_config):
    """Test health check when provider is unhealthy."""
    import httpx

    from lks_idprovider_entraid.provider import EntraIDProvider

    provider = EntraIDProvider(entraid_config)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        health = await provider.health_check()

        assert health["status"] == "unhealthy"
        assert health["endpoints_accessible"] is False
        assert "error" in health


@pytest.mark.asyncio
async def test_get_provider_info(entraid_config):
    """Test getting provider information."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    provider = EntraIDProvider(entraid_config)
    info = await provider.get_provider_info()

    assert info["name"] == "entra_id"
    assert info["display_name"] == "Azure Entra ID"
    assert info["version"] == "1.0.0"
    assert info["tenant_id"] == entraid_config.tenant_id
    assert info["credential_type"] == "client_secret"
    assert info["supports_user_tokens"] is True
    assert info["supports_app_tokens"] is True


@pytest.mark.asyncio
async def test_test_connection_success(entraid_config, mock_well_known_config):
    """Test successful connection test."""
    from lks_idprovider_entraid.provider import EntraIDProvider

    provider = EntraIDProvider(entraid_config)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_well_known_config
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await provider.test_connection()

        assert result is True


@pytest.mark.asyncio
async def test_test_connection_failure(entraid_config):
    """Test connection test failure."""
    import httpx

    from lks_idprovider_entraid.provider import EntraIDProvider

    provider = EntraIDProvider(entraid_config)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        mock_client_class.return_value = mock_client

        with pytest.raises(ProviderError, match="Error connecting to Azure Entra ID"):
            await provider.test_connection()
