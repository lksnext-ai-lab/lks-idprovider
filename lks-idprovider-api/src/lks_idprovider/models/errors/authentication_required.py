"""
Authentication required error for LKS Identity Provider API.

This module contains the AuthenticationRequiredError class.
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
