"""
Keycloak-specific configuration model.

This module contains the KeycloakConfig class that extends ProviderConfig
for Keycloak-specific configuration options.
"""

from typing import Optional

from lks_idprovider.models.config.base import ProviderConfig
from pydantic import Field, field_validator


class KeycloakConfig(ProviderConfig):
    """Keycloak-specific configuration."""

    provider_name: str = Field(
        default="keycloak", description="Provider name (always 'keycloak')"
    )
    realm: str = Field(..., description="Keycloak realm name")
    client_id: str = Field(..., description="Keycloak client ID")
    client_secret: Optional[str] = Field(
        default=None, description="Keycloak client secret"
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

    # Client credentials settings
    client_credentials_scope: Optional[str] = Field(
        default=None, description="Default scope for client credentials flow"
    )

    # API endpoint settings
    use_token_introspection: bool = Field(
        default=True, description="Use token introspection endpoint for validation"
    )
    use_userinfo_endpoint: bool = Field(
        default=True, description="Use userinfo endpoint for user information"
    )

    @field_validator("provider_name")
    def validate_provider_name_is_keycloak(cls, v):
        """Ensure provider_name is always 'keycloak'."""
        if v != "keycloak":
            raise ValueError("provider_name must be 'keycloak' for KeycloakConfig")
        return v

    @field_validator("realm")
    def validate_realm(cls, v):
        """Validate realm name."""
        if not v or not v.strip():
            raise ValueError("realm cannot be empty")
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

    @property
    def realm_url(self) -> str:
        """Get the realm URL."""
        return f"{self.base_url}/realms/{self.realm}"

    @property
    def token_endpoint(self) -> str:
        """Get the token endpoint URL."""
        return f"{self.realm_url}/protocol/openid-connect/token"

    @property
    def userinfo_endpoint(self) -> str:
        """Get the userinfo endpoint URL."""
        return f"{self.realm_url}/protocol/openid-connect/userinfo"

    @property
    def token_introspection_endpoint(self) -> str:
        """Get the token introspection endpoint URL."""
        return f"{self.realm_url}/protocol/openid-connect/token/introspect"

    @property
    def jwks_endpoint(self) -> str:
        """Get the JWKS endpoint URL."""
        return f"{self.realm_url}/protocol/openid-connect/certs"

    @property
    def well_known_endpoint(self) -> str:
        """Get the well-known configuration endpoint URL."""
        return f"{self.realm_url}/.well-known/openid_connect_configuration"

    @property
    def issuer(self) -> str:
        """Get the expected issuer for JWT tokens."""
        return self.realm_url

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
    }
