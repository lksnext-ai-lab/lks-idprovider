"""
Network error class for LKS Identity Provider API.

This module contains the NetworkError class for communication issues.
"""

from typing import Any, Optional

from .provider import ProviderError


class NetworkError(ProviderError):
    """Network communication error with identity provider."""

    def __init__(
        self,
        message: str = "Network error occurred",
        provider_name: Optional[str] = None,
        url: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, provider_name, None, details)
        self.url = url
