"""LKS ID Provider Keycloak Implementation.

This package provides Keycloak-based implementation of the LKS ID Provider API
for REST API security and authentication.
"""

from .config import KeycloakConfig
from .provider import KeycloakProvider

__version__ = "0.1.0"
__author__ = "LKS"
__email__ = "dev@lks.com"

# Version information
VERSION = (0, 1, 0)

# Package metadata
__all__ = [
    "__version__",
    "VERSION",
    "KeycloakConfig",
    "KeycloakProvider",
]
