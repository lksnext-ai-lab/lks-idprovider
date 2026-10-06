"""
Client credentials configuration model for LKS Identity Provider API.

This module contains configuration for OAuth2 client credentials flow.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClientCredentialsConfig(BaseModel):
    """Client credentials flow configuration."""

    client_id: str = Field(..., description="OAuth2 client identifier")
    client_secret: Optional[str] = Field(None, description="OAuth2 client secret")

    # Scope settings
    default_scopes: list[str] = Field(
        default_factory=list, description="Default scopes to request"
    )
    allowed_scopes: list[str] = Field(
        default_factory=list, description="Allowed scopes for this client"
    )

    # Token settings
    token_endpoint: Optional[str] = Field(None, description="Custom token endpoint URL")

    @field_validator("client_id")
    def validate_client_id(cls, v: str) -> str:
        """Validate client_id is not empty."""
        if not v or not v.strip():
            raise ValueError("client_id cannot be empty")
        return v.strip()

    model_config = ConfigDict(validate_assignment=True)
