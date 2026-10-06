"""
Authentication and authorization error classes for LKS Identity Provider API.

This module contains authentication and authorization related exception classes.
"""

from typing import Any, Optional

from .base import LKSIdProviderError


class AuthenticationRequiredError(LKSIdProviderError):
    """Authentication is required but not provided."""

    def __init__(
        self,
        message: str = "Authentication is required",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)


class AuthorizationError(LKSIdProviderError):
    """Authorization failed - user/client lacks required roles."""

    def __init__(
        self,
        message: str = "Authorization failed",
        required_roles: Optional[list[str]] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.required_roles = required_roles or []
