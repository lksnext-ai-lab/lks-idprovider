"""
Models package for LKS Identity Provider API.

This package contains all data models used throughout the library:
- Authentication and authorization models (Identity, User, ClientIdentity, AuthContext)
- Token models and validation results
- Configuration models for providers
- Error hierarchy for consistent exception handling
"""

# Authentication and authorization models
from .auth import AuthContext

# Error models
from .errors import (
    AuthenticationRequiredError,
    AuthorizationError,
    ClientCredentialsError,
    ConfigurationError,
    LKSIdProviderError,
    NetworkError,
    ProviderError,
    TokenExpiredError,
    TokenMalformedError,
    TokenValidationError,
)
from .identity import ClientIdentity, Identity, IdentityType, User
from .role import Role

# Token models
from .token import TokenInfo, TokenValidationResult

__all__ = [
    # Authentication models
    "AuthContext",
    "ClientIdentity",
    "Identity",
    "IdentityType",
    "Role",
    "User",
    # Token models
    "TokenInfo",
    "TokenValidationResult",
    # Error models
    "AuthenticationRequiredError",
    "AuthorizationError",
    "ClientCredentialsError",
    "ConfigurationError",
    "LKSIdProviderError",
    "NetworkError",
    "ProviderError",
    "TokenExpiredError",
    "TokenMalformedError",
    "TokenValidationError",
]
