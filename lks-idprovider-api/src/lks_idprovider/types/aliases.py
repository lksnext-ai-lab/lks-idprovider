"""
Type aliases for LKS Identity Provider API.

This module contains type aliases and custom types used throughout the library.
"""

from typing import Any, Optional, Union

# Basic type aliases
Claims = dict[str, Any]
Scopes = list[str]
Headers = dict[str, str]
Token = str  # Token string representation

# Optional types
OptionalClaims = Optional[Claims]
OptionalScopes = Optional[Scopes]

# Union types for flexibility
StringOrList = Union[str, list[str]]
StringOrInt = Union[str, int]
