"""
Configuration error classes for LKS Identity Provider API.

This module contains configuration-related exception classes.
"""

from typing import Any, Optional

from .base import LKSIdProviderError


class ConfigurationError(LKSIdProviderError):
    """Configuration is invalid."""

    def __init__(
        self,
        message: str = "Configuration is invalid",
        field_name: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.field_name = field_name
