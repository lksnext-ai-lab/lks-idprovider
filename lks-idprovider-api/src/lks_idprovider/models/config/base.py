"""
Base configuration model for LKS Identity Provider API.

This module contains the base ProviderConfig class that all
provider configurations inherit from.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProviderConfig(BaseModel):
    """Base configuration for identity providers."""

    provider_name: str = Field(..., description="Name of the identity provider")
    base_url: str = Field(..., description="Base URL of the identity provider")
    timeout: int = Field(
        default=30, ge=1, le=300, description="Request timeout in seconds"
    )
    verify_ssl: bool = Field(
        default=True, description="Whether to verify SSL certificates"
    )
    debug: bool = Field(default=False, description="Enable debug logging")

    @field_validator("base_url")
    def validate_base_url(cls, v: str) -> str:
        """Validate that base_url is a valid URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        # Remove trailing slash for consistency
        return v.rstrip("/")

    @field_validator("provider_name")
    def validate_provider_name(cls, v: str) -> str:
        """Validate provider name is not empty."""
        if not v or not v.strip():
            raise ValueError("provider_name cannot be empty")
        return v.strip().lower()

    model_config = ConfigDict(validate_assignment=True, extra="forbid")
