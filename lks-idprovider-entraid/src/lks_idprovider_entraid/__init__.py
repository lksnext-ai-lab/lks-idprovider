"""
LKS Identity Provider - Azure Entra ID Implementation.

This package provides Azure Entra ID (formerly Azure Active Directory) implementation
of the LKS Identity Provider protocols using azure.identity for authentication.
"""

from .config import EntraIDConfig, TokenType
from .provider import EntraIDProvider
from .rest.entraid_client import EntraIDCredentialClient

__version__ = "0.1.0"

__all__ = [
    "EntraIDConfig",
    "EntraIDProvider",
    "EntraIDCredentialClient",
    "TokenType",
]
