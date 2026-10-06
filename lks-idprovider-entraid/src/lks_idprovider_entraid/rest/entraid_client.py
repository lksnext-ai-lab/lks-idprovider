"""
Azure Entra ID Credential Client.

This module contains the EntraIDCredentialClient class that handles
credential management and token acquisition using azure.identity.
"""

from typing import Any

from azure.core.credentials import AccessToken
from azure.identity.aio import (
    CertificateCredential as AsyncCertificateCredential,
)
from azure.identity.aio import (
    ClientSecretCredential as AsyncClientSecretCredential,
)
from azure.identity.aio import (
    ManagedIdentityCredential as AsyncManagedIdentityCredential,
)

from ..config import EntraIDConfig


class EntraIDCredentialClient:
    """Credential client for Azure Entra ID token management.

    This client uses azure.identity for automatic token acquisition and refresh,
    eliminating the need for manual token management.
    """

    def __init__(self, config: EntraIDConfig):
        """Initialize the Entra ID credential client.

        Args:
            config: EntraIDConfig instance with Azure AD settings
        """
        self.config = config
        self._credential: Any | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._ensure_credential()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _get_credential(self) -> Any:
        """Get the appropriate Azure credential based on configuration.

        Returns:
            Azure Identity credential instance (async version)

        Raises:
            ValueError: If no valid credential configuration is found
        """
        credential_type = self.config.get_credential_type()

        if credential_type == "managed_identity":
            return AsyncManagedIdentityCredential(
                client_id=self.config.client_id if self.config.client_id else None
            )
        elif credential_type == "certificate":
            if not self.config.certificate_path:
                raise ValueError("certificate_path is required for authentication")
            return AsyncCertificateCredential(
                tenant_id=self.config.tenant_id,
                client_id=self.config.client_id,
                certificate_path=self.config.certificate_path,
                password=self.config.certificate_password,
            )
        elif credential_type == "client_secret":
            if not self.config.client_secret:
                raise ValueError("client_secret is required for client authentication")
            return AsyncClientSecretCredential(
                tenant_id=self.config.tenant_id,
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
            )
        else:
            raise ValueError(f"Unsupported credential type: {credential_type}")

    def _ensure_credential(self):
        """Ensure credential is initialized."""
        if self._credential is None:
            self._credential = self._get_credential()

    async def close(self):
        """Close the credential."""
        if self._credential:
            await self._credential.close()
            self._credential = None

    async def get_access_token(self, scopes: list[str] | None = None) -> str:
        """Get an access token for Microsoft Graph API.

        Args:
            scopes: List of OAuth2 scopes. Defaults to config.default_scope

        Returns:
            Access token string

        Raises:
            RuntimeError: If credential is not initialized
            Azure exceptions: If token acquisition fails
        """
        self._ensure_credential()

        if not self._credential:
            raise RuntimeError("Credential is not initialized")

        if scopes is None:
            scopes = [self.config.default_scope]

        # Get token using azure.identity
        token: AccessToken = await self._credential.get_token(*scopes)
        return token.token

    async def get_token_info(self, scopes: list[str] | None = None) -> dict[str, Any]:
        """Get detailed access token information including claims.

        This method uses get_token_info() from azure.identity which returns
        additional token information including claims, expiration, and other metadata.

        Args:
            scopes: List of OAuth2 scopes. Defaults to config.default_scope

        Returns:
            Dictionary containing token information including:
            - token: The access token string
            - expires_on: Expiration timestamp
            - Additional fields depending on the credential type

        Raises:
            RuntimeError: If credential is not initialized
            Azure exceptions: If token acquisition fails
        """
        self._ensure_credential()

        if not self._credential:
            raise RuntimeError("Credential is not initialized")

        if scopes is None:
            scopes = [self.config.default_scope]

        # Check if credential supports get_token_info (not all do)
        get_token_info_method = getattr(self._credential, "get_token_info", None)
        if get_token_info_method and callable(get_token_info_method):
            token_info = await get_token_info_method(*scopes)  # type: ignore[misc]
            return {
                "token": token_info.token,
                "expires_on": token_info.expires_on,
            }
        else:
            # Fallback to get_token if get_token_info is not available
            token = await self._credential.get_token(*scopes)
            return {
                "token": token.token,
                "expires_on": token.expires_on,
            }
