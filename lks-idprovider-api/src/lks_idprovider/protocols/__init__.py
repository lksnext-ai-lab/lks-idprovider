"""Protocol definitions for LKS Identity Provider.

This module contains the protocol definitions that all provider implementations
must follow. These protocols define the contracts for:

- Identity providers (user authentication)
- Client credentials providers (service-to-service authentication)
- Cache providers (optional caching support)

All protocols work with the unified Identity model where both users and clients
are represented as Identity instances with specific subclasses.
"""

from .cache import CacheProvider
from .client_credentials import ClientCredentialsProvider
from .provider import IdentityProvider

__all__ = [
    "IdentityProvider",
    "ClientCredentialsProvider",
    "CacheProvider",
]
