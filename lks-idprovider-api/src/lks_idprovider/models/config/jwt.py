"""
JWT configuration model for LKS Identity Provider API.

This module contains JWT-specific configuration options.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class JWTConfig(BaseModel):
    """JWT validation configuration."""

    validate_signature: bool = Field(
        default=True, description="Whether to validate JWT signature"
    )
    validate_audience: bool = Field(
        default=True, description="Whether to validate audience claim"
    )
    validate_issuer: bool = Field(
        default=True, description="Whether to validate issuer claim"
    )
    validate_expiration: bool = Field(
        default=True, description="Whether to validate expiration"
    )
    validate_not_before: bool = Field(
        default=True, description="Whether to validate not-before claim"
    )

    leeway: int = Field(
        default=0, ge=0, le=300, description="Clock skew tolerance in seconds"
    )

    # Expected values for validation
    expected_audience: Optional[str] = Field(
        None, description="Expected audience value"
    )
    expected_issuer: Optional[str] = Field(None, description="Expected issuer value")

    # Algorithm settings
    allowed_algorithms: list[str] = Field(
        default_factory=lambda: ["RS256", "HS256"], description="Allowed JWT algorithms"
    )

    model_config = ConfigDict(validate_assignment=True)
