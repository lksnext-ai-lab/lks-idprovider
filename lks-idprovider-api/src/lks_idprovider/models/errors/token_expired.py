"""
Token expired error for LKS Identity Provider API.

This module contains the TokenExpiredError class.
"""

from typing import Any, Optional

from .token_validation import TokenValidationError


class TokenExpiredError(TokenValidationError):
    """Token has expired."""

    def __init__(
        self,
        message: str = "Token has expired",
        token_type: Optional[str] = None,
        expired_at: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, token_type, details)
        self.expired_at = expired_at
