"""
Authorization error for LKS Identity Provider API.

This module contains the AuthorizationError class.
"""

from typing import Any, Optional

from .base import LKSIdProviderError


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
