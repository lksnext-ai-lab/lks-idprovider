"""
Token validation error classes for LKS Identity Provider API.

This module contains all token-related exception classes.
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


class TokenMalformedError(TokenValidationError):
    """Token is malformed or invalid format."""

    def __init__(
        self,
        message: str = "Token is malformed",
        token_type: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, token_type, details)
