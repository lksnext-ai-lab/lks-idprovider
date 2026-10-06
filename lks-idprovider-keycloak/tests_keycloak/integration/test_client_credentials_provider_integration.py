import httpx
import pytest
from lks_idprovider.models.identity.client_identity import ClientIdentity
from lks_idprovider.models.token import TokenInfo
from lks_idprovider.types import TokenType

from lks_idprovider_keycloak.client_credentials_provider import (
    KeycloakClientCredentialsProvider,
)
from lks_idprovider_keycloak.config import KeycloakConfig


def get_client_credentials_token(config: KeycloakConfig) -> str:
    token_url = f"{config.base_url}/realms/{config.realm}/protocol/openid-connect/token"
    response = httpx.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": config.client_id,
            "client_secret": config.client_secret,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


@pytest.fixture()
def config():
    return KeycloakConfig(
        base_url="http://localhost:8080",
        realm="lks-test",
        client_id="PythonServiceTest",
        client_secret="python-service-secret-123",
    )


@pytest.fixture()
def provider(config: KeycloakConfig):
    return KeycloakClientCredentialsProvider(config)


@pytest.mark.asyncio
async def test_validate_client_token_with_real_token(
    provider: KeycloakClientCredentialsProvider, config: KeycloakConfig
):
    access_token = get_client_credentials_token(config)
    result = await provider.validate_client_token(access_token)
    assert result.is_valid is True
    assert isinstance(result.token_info, TokenInfo)
    assert result.token_info.token == access_token
    assert result.token_info.token_type == TokenType.ACCESS_TOKEN


@pytest.mark.asyncio
async def test_get_client_info_with_real_token(
    provider: KeycloakClientCredentialsProvider, config: KeycloakConfig
):
    access_token = get_client_credentials_token(config)
    client = await provider.get_client_info(access_token)
    assert isinstance(client, ClientIdentity)
    assert client.client_id == "PythonServiceTest"
    assert (
        client.name == "PythonServiceTest"
        or client.client_name == "Python Service Test Client"
    )


@pytest.mark.asyncio
async def test_get_client_credentials_token(
    provider: KeycloakClientCredentialsProvider,
):
    token_response = await provider.get_client_credentials_token()
    assert "access_token" in token_response
    assert token_response["token_type"].lower() == "bearer"
    token_response_with_scope = await provider.get_client_credentials_token(["openid"])
    assert "access_token" in token_response_with_scope
    assert token_response_with_scope["token_type"].lower() == "bearer"
    assert "scope" in token_response_with_scope
    assert "openid" in token_response_with_scope["scope"]
