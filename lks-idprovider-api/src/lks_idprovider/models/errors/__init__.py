"""
Error classes package for LKS Identity Provider API.

This package contains all exception classes organized by category:
- Base exceptions
- Token validation errors
- Client credentials errors
- Provider errors
- Configuration errors
- Authentication and authorization errors
"""

# Authentication and authorization errors
from .authentication_required import AuthenticationRequiredError
from .authorization import AuthorizationError

# Base exceptions
from .base import LKSIdProviderError

# Client credentials errors
from .client_credentials import ClientCredentialsError

# Configuration errors
from .configuration import ConfigurationError

# Provider errors
from .network import NetworkError
from .provider import ProviderError

# Token validation errors
from .token_expired import TokenExpiredError
from .token_malformed import TokenMalformedError
from .token_validation import TokenValidationError

__all__ = [
    # Base
    "LKSIdProviderError",
    # Authentication/Authorization
    "AuthenticationRequiredError",
    "AuthorizationError",
    # Client credentials
    "ClientCredentialsError",
    # Configuration
    "ConfigurationError",
    # Provider
    "NetworkError",
    "ProviderError",
    # Token
    "TokenExpiredError",
    "TokenMalformedError",
    "TokenValidationError",
]
