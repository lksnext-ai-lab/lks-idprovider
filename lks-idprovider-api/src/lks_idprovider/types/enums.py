"""
Enums for LKS Identity Provider API.

This module contains enumeration types used throughout the library.
"""

from enum import Enum


class TokenType(str, Enum):
    """Supported token types."""

    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    ID_TOKEN = "id_token"
