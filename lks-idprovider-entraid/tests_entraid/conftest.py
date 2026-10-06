"""
Test configuration and fixtures for lks-idprovider-entraid.
"""

import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def entraid_config():
    """Fixture for basic EntraID configuration."""
    from lks_idprovider_entraid.config import EntraIDConfig

    return EntraIDConfig(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        client_secret="test-client-secret",
    )


@pytest.fixture
def entraid_config_with_certificate():
    """Fixture for EntraID configuration with certificate."""
    from lks_idprovider_entraid.config import EntraIDConfig

    return EntraIDConfig(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        certificate_path="/path/to/cert.pem",
        certificate_password="cert-password",
    )


@pytest.fixture
def entraid_config_with_managed_identity():
    """Fixture for EntraID configuration with managed identity."""
    from lks_idprovider_entraid.config import EntraIDConfig

    return EntraIDConfig(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        use_managed_identity=True,
    )


@pytest.fixture
def sample_token_claims():
    """Sample Azure AD token claims for user."""
    return {
        "aud": "test-client-id",
        "iss": "https://login.microsoftonline.com/test-tenant-id/v2.0",
        "iat": 1234567890,
        "nbf": 1234567890,
        "exp": 1234571490,
        "sub": "user-object-id",
        "oid": "user-object-id",
        "tid": "test-tenant-id",
        "upn": "user@example.com",
        "name": "Test User",
        "given_name": "Test",
        "family_name": "User",
        "email": "user@example.com",
        "roles": ["AdminRole", "UserRole"],
        "scp": "User.Read profile",
        "idtyp": "user",
    }


@pytest.fixture
def sample_client_token_claims():
    """Sample Azure AD token claims for client/app."""
    return {
        "aud": "https://graph.microsoft.com",
        "iss": "https://login.microsoftonline.com/test-tenant-id/v2.0",
        "iat": 1234567890,
        "nbf": 1234567890,
        "exp": 1234571490,
        "sub": "app-object-id",
        "oid": "app-object-id",
        "appid": "test-client-id",
        "tid": "test-tenant-id",
        "roles": ["Application.ReadWrite.All"],
        "idtyp": "app",
    }


@pytest.fixture
def mock_azure_credential():
    """Mock azure.identity credential."""
    mock_credential = AsyncMock()
    mock_token = MagicMock()
    mock_token.token = "mock-access-token"
    mock_token.expires_on = 1234571490
    mock_credential.get_token = AsyncMock(return_value=mock_token)
    mock_credential.close = AsyncMock()
    return mock_credential


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.post = AsyncMock()
    mock_client.aclose = AsyncMock()
    return mock_client


@pytest.fixture
def mock_graph_user_response():
    """Mock Microsoft Graph /me response."""
    return {
        "id": "user-object-id",
        "userPrincipalName": "user@example.com",
        "displayName": "Test User",
        "givenName": "Test",
        "surname": "User",
        "mail": "user@example.com",
        "mobilePhone": "+1234567890",
        "jobTitle": "Software Engineer",
        "department": "Engineering",
        "officeLocation": "Building 1",
    }


@pytest.fixture
def mock_well_known_config():
    """Mock OpenID Connect well-known configuration."""
    return {
        "authorization_endpoint": "https://login.microsoftonline.com/test-tenant-id/oauth2/v2.0/authorize",
        "token_endpoint": "https://login.microsoftonline.com/test-tenant-id/oauth2/v2.0/token",
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",
            "private_key_jwt",
        ],
        "jwks_uri": "https://login.microsoftonline.com/test-tenant-id/discovery/v2.0/keys",
        "response_modes_supported": ["query", "fragment", "form_post"],
        "subject_types_supported": ["pairwise"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "response_types_supported": [
            "code",
            "id_token",
            "code id_token",
            "id_token token",
        ],
        "scopes_supported": ["openid", "profile", "email", "offline_access"],
        "issuer": "https://login.microsoftonline.com/test-tenant-id/v2.0",
        "request_uri_parameter_supported": False,
        "userinfo_endpoint": "https://graph.microsoft.com/oidc/userinfo",
        "end_session_endpoint": "https://login.microsoftonline.com/test-tenant-id/oauth2/v2.0/logout",
    }
