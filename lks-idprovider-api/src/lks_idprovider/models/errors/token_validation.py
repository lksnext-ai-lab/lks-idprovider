"""
Base token validation error for LKS Identity Provider API.

This module contains the base TokenValidationError class.
"""

from typing import Any, Optional

from .base import LKSIdProviderError


class TokenValidationError(LKSIdProviderError):
    """Token validation failed."""

    def __init__(
        self,
        message: str = "Token validation failed",
        token_type: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.token_type = token_type
