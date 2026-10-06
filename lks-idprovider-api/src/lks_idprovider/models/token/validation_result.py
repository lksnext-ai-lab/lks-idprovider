"""
Token validation result model for LKS Identity Provider API.

This module contains the TokenValidationResult class for
representing the result of token validation.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .token_info import TokenInfo


class TokenValidationResult(BaseModel):
    """Result of token validation."""

    model_config = ConfigDict(frozen=True)

    is_valid: bool = Field(..., description="Whether the token is valid")
    token_info: Optional[TokenInfo] = Field(
        default=None, description="Token information if valid"
    )
    error: Optional[str] = Field(None, description="Error message if validation failed")

    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if not self.is_valid or not self.token_info:
            return False
        return self.token_info.is_expired
