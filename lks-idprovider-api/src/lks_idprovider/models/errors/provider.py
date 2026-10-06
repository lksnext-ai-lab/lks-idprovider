"""
Provider error class for LKS Identity Provider API.

This module contains the base ProviderError class.
"""

from typing import Any, Optional

from .base import LKSIdProviderError


class ProviderError(LKSIdProviderError):
    """Provider-specific error."""

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.provider_name = provider_name
        self.status_code = status_code
