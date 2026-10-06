"""
Types package for LKS Identity Provider API.

This package contains type definitions, enums, and aliases used throughout the library.
"""

# Type aliases
from .aliases import (
    Claims,
    Headers,
    OptionalClaims,
    OptionalScopes,
    Scopes,
    StringOrInt,
    StringOrList,
)

# Enums
from .enums import TokenType

__all__ = [
    # Enums
    "TokenType",
    # Type aliases
    "Claims",
    "Headers",
    "OptionalClaims",
    "OptionalScopes",
    "Scopes",
    "StringOrInt",
    "StringOrList",
]
