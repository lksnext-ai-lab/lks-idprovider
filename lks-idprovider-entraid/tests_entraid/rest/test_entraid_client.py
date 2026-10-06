"""
Unit tests for EntraIDCredentialClient.
"""

from unittest.mock import patch

import pytest
from azure.core.credentials import AccessToken


@pytest.mark.asyncio
async def test_entraid_client_initialization(entraid_config):
    """Test EntraIDCredentialClient initialization."""
    from lks_idprovider_entraid.rest.entraid_client import EntraIDCredentialClient

    client = EntraIDCredentialClient(entraid_config)
    assert client.config == entraid_config
    assert client._credential is None


@pytest.mark.asyncio
async def test_entraid_client_context_manager(entraid_config, mock_azure_credential):
    """Test EntraIDCredentialClient as async context manager."""
    from lks_idprovider_entraid.rest.entraid_client import EntraIDCredentialClient

    with patch(
        "lks_idprovider_entraid.rest.entraid_client.AsyncClientSecretCredential",
        return_value=mock_azure_credential,
    ):
        async with EntraIDCredentialClient(entraid_config) as client:
            assert client._credential is not None


@pytest.mark.asyncio
async def test_entraid_client_get_credential_client_secret(entraid_config):
    """Test getting client secret credential."""
    from lks_idprovider_entraid.rest.entraid_client import EntraIDCredentialClient

    client = EntraIDCredentialClient(entraid_config)

    with patch(
        "lks_idprovider_entraid.rest.entraid_client.AsyncClientSecretCredential"
    ) as mock_cred:
        client._get_credential()
        mock_cred.assert_called_once_with(
            tenant_id=entraid_config.tenant_id,
            client_id=entraid_config.client_id,
            client_secret=entraid_config.client_secret,
        )


@pytest.mark.asyncio
async def test_entraid_client_get_credential_certificate(
    entraid_config_with_certificate,
):
    """Test getting certificate credential."""
    from lks_idprovider_entraid.rest.entraid_client import EntraIDCredentialClient

    client = EntraIDCredentialClient(entraid_config_with_certificate)

    with patch(
        "lks_idprovider_entraid.rest.entraid_client.AsyncCertificateCredential"
    ) as mock_cred:
        client._get_credential()
        mock_cred.assert_called_once_with(
            tenant_id=entraid_config_with_certificate.tenant_id,
            client_id=entraid_config_with_certificate.client_id,
            certificate_path=entraid_config_with_certificate.certificate_path,
            password=entraid_config_with_certificate.certificate_password,
        )


@pytest.mark.asyncio
async def test_entraid_client_get_credential_managed_identity(
    entraid_config_with_managed_identity,
):
    """Test getting managed identity credential."""
    from lks_idprovider_entraid.rest.entraid_client import EntraIDCredentialClient

    client = EntraIDCredentialClient(entraid_config_with_managed_identity)

    with patch(
        "lks_idprovider_entraid.rest.entraid_client.AsyncManagedIdentityCredential"
    ) as mock_cred:
        client._get_credential()
        mock_cred.assert_called_once_with(
            client_id=entraid_config_with_managed_identity.client_id
        )


@pytest.mark.asyncio
async def test_entraid_client_get_access_token(entraid_config, mock_azure_credential):
    """Test getting access token."""
    from lks_idprovider_entraid.rest.entraid_client import EntraIDCredentialClient

    # Mock token
    mock_token = AccessToken(token="mock_access_token", expires_on=9999999999)
    mock_azure_credential.get_token.return_value = mock_token

    with patch(
        "lks_idprovider_entraid.rest.entraid_client.AsyncClientSecretCredential",
        return_value=mock_azure_credential,
    ):
        async with EntraIDCredentialClient(entraid_config) as client:
            token = await client.get_access_token()
            assert token == "mock_access_token"
            mock_azure_credential.get_token.assert_called_once_with(
                entraid_config.default_scope
            )


@pytest.mark.asyncio
async def test_entraid_client_get_access_token_custom_scopes(
    entraid_config, mock_azure_credential
):
    """Test getting access token with custom scopes."""
    from lks_idprovider_entraid.rest.entraid_client import EntraIDCredentialClient

    mock_token = AccessToken(token="mock_access_token", expires_on=9999999999)
    mock_azure_credential.get_token.return_value = mock_token

    custom_scopes = ["https://graph.microsoft.com/User.Read"]

    with patch(
        "lks_idprovider_entraid.rest.entraid_client.AsyncClientSecretCredential",
        return_value=mock_azure_credential,
    ):
        async with EntraIDCredentialClient(entraid_config) as client:
            token = await client.get_access_token(scopes=custom_scopes)
            assert token == "mock_access_token"
            mock_azure_credential.get_token.assert_called_once_with(*custom_scopes)


@pytest.mark.asyncio
async def test_entraid_client_get_token_info(entraid_config, mock_azure_credential):
    """Test getting detailed token info."""
    from lks_idprovider_entraid.rest.entraid_client import EntraIDCredentialClient

    # Mock token
    mock_token = AccessToken(token="mock_access_token", expires_on=9999999999)
    mock_azure_credential.get_token.return_value = mock_token

    # Mock get_token_info not being available (fallback to get_token)
    mock_azure_credential.get_token_info = None

    with patch(
        "lks_idprovider_entraid.rest.entraid_client.AsyncClientSecretCredential",
        return_value=mock_azure_credential,
    ):
        async with EntraIDCredentialClient(entraid_config) as client:
            token_info = await client.get_token_info()
            assert token_info["token"] == "mock_access_token"
            assert token_info["expires_on"] == 9999999999
            mock_azure_credential.get_token.assert_called_with(
                entraid_config.default_scope
            )


@pytest.mark.asyncio
async def test_entraid_client_close(entraid_config, mock_azure_credential):
    """Test closing the client."""
    from lks_idprovider_entraid.rest.entraid_client import EntraIDCredentialClient

    with patch(
        "lks_idprovider_entraid.rest.entraid_client.AsyncClientSecretCredential",
        return_value=mock_azure_credential,
    ):
        client = EntraIDCredentialClient(entraid_config)
        client._ensure_credential()

        assert client._credential is not None

        await client.close()

        assert client._credential is None
        mock_azure_credential.close.assert_called_once()
