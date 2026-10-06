from datetime import datetime, timezone

import pytest
from lks_idprovider.models.identity.client_identity import ClientIdentity
from lks_idprovider.models.token import TokenInfo

from lks_idprovider_keycloak.client_credentials_provider import (
    KeycloakClientCredentialsProvider,
)
from lks_idprovider_keycloak.config import KeycloakConfig


@pytest.fixture
def config():
    return KeycloakConfig(
        base_url="http://localhost:8080",
        realm="lks-test",
        client_id="PythonServiceTest",
        client_secret="python-service-secret-123",
    )


@pytest.fixture
def provider(config: KeycloakConfig):
    return KeycloakClientCredentialsProvider(config)


@pytest.mark.asyncio
async def test_validate_client_token_valid(provider, httpx_mock):
    token_claims = {
        "active": True,
        "sub": "client-123",
        "client_id": "PythonServiceTest",
        "aud": "api-audience",
        "exp": int(datetime.now(timezone.utc).timestamp()) + 3600,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "iss": "http://localhost:8080/realms/lks-test",
    }

    async def mock_introspect_token(token):
        return token_claims

    provider._client.introspect_token = mock_introspect_token
    result = await provider.validate_client_token("valid-client-token")
    assert result.is_valid is True
    assert isinstance(result.token_info, TokenInfo)
    assert result.token_info.subject == "client-123"
    assert result.token_info.audience == "api-audience"


@pytest.mark.asyncio
async def test_validate_client_token_invalid(provider, httpx_mock):
    async def mock_introspect_token(token):
        return {"active": False}

    provider._client.introspect_token = mock_introspect_token
    result = await provider.validate_client_token("invalid-client-token")
    assert result.is_valid is False
    assert result.token_info is None


@pytest.mark.asyncio
async def test_get_client_info_valid(provider, httpx_mock):
    token_claims = {
        "active": True,
        "sub": "client-123",
        "client_id": "PythonServiceTest",
        "client_name": "Python Service Test Client",
        "aud": "api-audience",
        "scope": "read write",
    }

    async def mock_introspect_token(token):
        return token_claims

    provider._client.introspect_token = mock_introspect_token
    client = await provider.get_client_info("valid-client-token")
    assert isinstance(client, ClientIdentity)
    assert client.client_id == "PythonServiceTest"
    assert client.client_name == "Python Service Test Client"
    assert client.audience == "api-audience"
    assert set(client.scopes) == {"read", "write"}
