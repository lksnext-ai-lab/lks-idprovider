"""
LKS Identity Provider API

Pure API specification for identity provider implementations focused
on REST API security.
Provides protocols, models, and contracts for building identity providers.

This library is designed for REST API securization where users and services are already
authenticated. Import from organized package structure:

- `from lks_idprovider.protocols import IdentityProvider, ClientCredentialsProvider`
- `from lks_idprovider.models.auth import AuthContext`
- `from lks_idprovider.models.identity import User, ClientIdentity`
- `from lks_idprovider.models.errors import TokenValidationError`
- `from lks_idprovider.types import TokenType`
"""

# Version information
__version__ = "0.1.0"
__author__ = "LKS Team"
__description__ = "LKS Identity Provider API Specification for REST API Security"

# Import sub-packages to maintain package structure
from . import models, protocols, types
from .models.auth import AuthContext
from .models.errors import LKSIdProviderError, TokenValidationError
from .models.identity import ClientIdentity, User

# Only expose the most essential classes at root level for convenience
from .protocols import ClientCredentialsProvider, IdentityProvider

# Minimal public API - only the most essential classes
__all__ = [
    # Sub-packages (maintain folder structure)
    "models",
    "protocols",
    "types",
    # Essential protocols for convenience
    "IdentityProvider",
    "ClientCredentialsProvider",
    # Core models for convenience
    "AuthContext",
    "User",
    "ClientIdentity",
    # Essential exceptions for convenience
    "LKSIdProviderError",
    "TokenValidationError",
]
