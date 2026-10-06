"""
Client credentials error classes for LKS Identity Provider API.

This module contains client credentials related exception classes.
"""

from typing import Any, Optional

from .base import LKSIdProviderError


class ClientCredentialsError(LKSIdProviderError):
    """Client credentials flow failed."""

    def __init__(
        self,
        message: str = "Client credentials flow failed",
        client_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.client_id = client_id
