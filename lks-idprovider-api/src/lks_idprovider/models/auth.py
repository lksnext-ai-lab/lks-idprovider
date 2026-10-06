"""
Authentication context model for LKS Identity Provider API.

This module contains the AuthContext class which is the main model returned by
identity providers after successful authentication.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .identity import Identity
from .identity.client_identity import ClientIdentity
from .identity.user import User
from .role import Role
from .token import TokenInfo


class AuthContext(BaseModel):
    """
    Complete authentication context containing identity and authorization information.

    This is the main model returned by identity providers after successful
    authentication.    It contains the authenticated identity (User or
    ClientIdentity) along with roles, token information, and other metadata.
    """

    model_config = ConfigDict(frozen=True)

    identity: Identity = Field(
        ..., description="The authenticated identity (User or ClientIdentity)"
    )
    roles: list[Role] = Field(
        default_factory=list, description="Roles assigned to the identity"
    )
    token_expires_at: Optional[datetime] = Field(
        default=None, description="When the access token expires"
    )
    refresh_expires_at: Optional[datetime] = Field(
        default=None, description="When the refresh token expires"
    )
    provider: str = Field(default="", description="Name of the identity provider")
    scopes: list[str] = Field(default_factory=list, description="OAuth2 scopes granted")
    token_info: TokenInfo = Field(description="Additional token information")

    @property
    def identity_type(self) -> str:
        """Return the type of identity: 'user' or 'client'."""
        return self.identity.identity_type

    @property
    def identity_name(self) -> str:
        """Return the name/identifier of the identity."""
        return self.identity.name

    @property
    def identity_id(self) -> str:
        """Return the ID of the identity."""
        return self.identity.id

    @property
    def user(self) -> Optional[User]:
        """Return User if identity is a user, None otherwise."""
        return self.identity if isinstance(self.identity, User) else None

    @property
    def client(self) -> Optional[ClientIdentity]:
        """Return ClientIdentity if identity is a client, None otherwise."""
        return self.identity if isinstance(self.identity, ClientIdentity) else None

    @property
    def is_user(self) -> bool:
        """Return True if identity is a user."""
        return isinstance(self.identity, User)

    @property
    def is_client(self) -> bool:
        """Return True if identity is a client."""
        return isinstance(self.identity, ClientIdentity)

    def has_role(self, role_name: str, client: Optional[str] = None) -> bool:
        """Check if the identity has a specific role."""
        return any(
            role.name == role_name and (client is None or role.client == client)
            for role in self.roles
        )

    def has_scope(self, scope: str) -> bool:
        """Check if the identity has a specific OAuth2 scope."""
        return scope in self.scopes

    def get_role_names(self, client: Optional[str] = None) -> list[str]:
        """Get list of role names, optionally filtered by client."""
        return [
            role.name for role in self.roles if client is None or role.client == client
        ]

    def __str__(self) -> str:
        return f"AuthContext({self.identity}, roles={len(self.roles)})"
