"""
Base exception for LKS Identity Provider API.

This module contains the root exception class for the entire library.
"""

from typing import Any, Optional


class LKSIdProviderError(Exception):
    """Base exception for all LKS ID Provider errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
