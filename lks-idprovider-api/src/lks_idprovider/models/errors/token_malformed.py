"""
Token malformed error for LKS Identity Provider API.

This module contains the TokenMalformedError class.
"""

from typing import Any, Optional

from .token_validation import TokenValidationError


class TokenMalformedError(TokenValidationError):
    """Token is malformed or invalid format."""

    def __init__(
        self,
        message: str = "Token is malformed",
        token_type: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, token_type, details)
