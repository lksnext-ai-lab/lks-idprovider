"""
Token information model for LKS Identity Provider API.

This module contains the TokenInfo class for representing token metadata.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from ...types.enums import TokenType


class TokenInfo(BaseModel):
    """Token information and metadata."""

    model_config = ConfigDict(frozen=True)

    token: str = Field(..., description="The actual token string")
    token_type: TokenType = Field(..., description="Type of the token")
    expires_at: Optional[datetime] = Field(
        default=None, description="When the token expires"
    )
    issued_at: Optional[datetime] = Field(
        default=None, description="When the token was issued"
    )
    issuer: Optional[str] = Field(default=None, description="Token issuer")
    audience: Optional[str] = Field(default=None, description="Intended audience")
    subject: Optional[str] = Field(
        default=None, description="Subject (user/client) of the token"
    )
    scopes: list[str] = Field(default_factory=list, description="OAuth2 scopes")

    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def time_until_expiry(self) -> Optional[int]:
        """Get seconds until token expires, None if no expiry."""
        if self.expires_at is None:
            return None
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, int(delta.total_seconds()))
