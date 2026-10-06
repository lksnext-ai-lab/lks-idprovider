"""
Azure Entra ID specific configuration model.

This module contains the EntraIDConfig class that extends ProviderConfig
for Azure Entra ID specific configuration options.
"""

from enum import Enum

from lks_idprovider.models.config.base import ProviderConfig
from pydantic import Field, field_validator


# str+Enum kept over StrEnum: StrEnum changes str()/format() output (public API).
class TokenType(str, Enum):  # noqa: UP042
    """Token type to accept and validate."""

    ID_TOKEN = "id_token"
    """Accept ID tokens (audience = client_id).
    Use for OIDC authentication flows where React/frontend sends ID token.
    No need to configure 'Expose an API' in Azure AD."""

    ACCESS_TOKEN = "access_token"
    """Accept access tokens for YOUR API (audience = api://client_id).
    Requires 'Expose an API' configuration in Azure AD.
    Use for proper OAuth 2.0 authorization flows."""


class EntraIDConfig(ProviderConfig):
    """Azure Entra ID specific configuration."""

    provider_name: str = Field(
        default="entraid", description="Provider name (always 'entraid')"
    )
    base_url: str = Field(
        default="https://login.microsoftonline.com",
        description="Base URL for Azure AD (authority host)",
    )
    tenant_id: str = Field(
        ...,
        description="Azure AD tenant ID or domain (e.g., 'common' or specific tenant)",
    )
    client_id: str = Field(
        ..., description="Application (client) ID from Azure app registration"
    )
    client_secret: str | None = Field(
        default=None, description="Client secret for confidential client flows"
    )
    api_version: str = Field(
        default="v1.0",
        description="Microsoft Graph API version ('v1.0' or 'beta')",
    )

    default_scope: str = Field(
        default="https://graph.microsoft.com/.default",
        description="Default scope for client credentials flow",
    )

    # Certificate authentication
    certificate_path: str | None = Field(
        default=None,
        description="Path to certificate file for certificate-based authentication",
    )
    certificate_password: str | None = Field(
        default=None, description="Password for the certificate (if encrypted)"
    )

    # Managed identity authentication
    use_managed_identity: bool = Field(
        default=False, description="Use Azure Managed Identity for authentication"
    )

    # Token type configuration
    token_type: TokenType = Field(
        default=TokenType.ID_TOKEN,
        description="Type of token to accept and validate. "
        "ID_TOKEN: For OIDC authentication (aud=client_id). "
        "ACCESS_TOKEN: For OAuth 2.0 authorization (aud=api://client_id).",
    )

    # JWT validation settings
    validate_audience: bool = Field(
        default=True, description="Whether to validate the audience claim"
    )
    validate_issuer: bool = Field(
        default=True, description="Whether to validate the issuer claim"
    )
    leeway: int = Field(
        default=0, ge=0, le=300, description="Clock skew tolerance in seconds"
    )

    # Caching settings
    jwks_cache_ttl: int = Field(
        default=300, ge=60, le=3600, description="JWKS cache TTL in seconds"
    )
    token_cache_ttl: int = Field(
        default=60, ge=0, le=3600, description="Token validation cache TTL in seconds"
    )

    @field_validator("provider_name")
    def validate_provider_name_is_entraid(cls, v):
        """Ensure provider_name is always 'entraid'."""
        if v != "entraid":
            raise ValueError("provider_name must be 'entraid' for EntraIDConfig")
        return v

    @field_validator("tenant_id")
    def validate_tenant_id(cls, v):
        """Validate tenant ID."""
        if not v or not v.strip():
            raise ValueError("tenant_id cannot be empty")
        return v.strip()

    @field_validator("client_id")
    def validate_client_id(cls, v):
        """Validate client ID."""
        if not v or not v.strip():
            raise ValueError("client_id cannot be empty")
        return v.strip()

    @field_validator("client_secret")
    def validate_client_secret(cls, v):
        """Validate client secret if provided."""
        if v is not None and not v.strip():
            raise ValueError("client_secret cannot be empty string")
        return v.strip() if v else None

    @field_validator("api_version")
    def validate_api_version(cls, v):
        """Validate API version."""
        if v not in ("v1.0", "beta"):
            raise ValueError("api_version must be either 'v1.0' or 'beta'")
        return v

    @property
    def authority(self) -> str:
        """Get the full authority URL."""
        # Handle both base_url and authority_host for flexibility
        host = self.base_url.replace("https://", "").replace("http://", "")
        return f"https://{host}/{self.tenant_id}"

    @property
    def token_endpoint(self) -> str:
        """Get the token endpoint URL."""
        return f"{self.authority}/oauth2/v2.0/token"

    @property
    def authorization_endpoint(self) -> str:
        """Get the authorization endpoint URL."""
        return f"{self.authority}/oauth2/v2.0/authorize"

    @property
    def jwks_endpoint(self) -> str:
        """Get the JWKS endpoint URL."""
        return f"{self.authority}/discovery/v2.0/keys"

    @property
    def well_known_endpoint(self) -> str:
        """Get the well-known OpenID configuration endpoint."""
        return f"{self.authority}/v2.0/.well-known/openid-configuration"

    @property
    def userinfo_endpoint(self) -> str:
        """Get the userinfo endpoint from Microsoft Graph API."""
        return f"https://graph.microsoft.com/{self.api_version}/me"

    @property
    def issuer(self) -> str:
        """Get the expected issuer claim value."""
        return f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"

    @property
    def graph_endpoint(self) -> str:
        """Get the Microsoft Graph API base endpoint."""
        return f"https://graph.microsoft.com/{self.api_version}"

    def get_credential_type(self) -> str:
        """Determine the credential type to use based on configuration.

        Returns:
            str: One of 'managed_identity', 'certificate', or 'client_secret'
        """
        if self.use_managed_identity:
            return "managed_identity"
        elif self.certificate_path:
            return "certificate"
        elif self.client_secret:
            return "client_secret"
        else:
            raise ValueError(
                "No valid credential configuration: "
                "provide client_secret, certificate_path,"
                "or enable use_managed_identity"
            )

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
    }
