"""
Client identity model for LKS Identity Provider API.

This module contains the ClientIdentity class for representing authenticated clients
in service-to-service communication scenarios.
"""

from typing import Any, Optional

from pydantic import Field

from .identity import Identity


class ClientIdentity(Identity):
    """
    Represents an authenticated client (service-to-service communication).

    Extends Identity with client-specific properties like client_id, scopes, etc.
    """

    identity_type: str = Field(
        default="client", description="Always 'client' for ClientIdentity instances"
    )
    client_id: str = Field(default="", description="OAuth2 client identifier")
    client_name: Optional[str] = Field(
        default=None, description="Human-readable client name"
    )
    scopes: list[str] = Field(
        default_factory=list, description="Granted scopes for this client"
    )
    audience: Optional[str] = Field(
        default=None, description="Intended audience for the client"
    )

    def model_post_init(self, __context: Any) -> None:
        """Set name and id from client information if not provided."""
        # Set name to client_name or client_id if not provided
        if not self.name:
            display_name = self.client_name or self.client_id
            if display_name:
                object.__setattr__(self, "name", display_name)

        # Set id to client_id if not provided
        if not self.id and self.client_id:
            object.__setattr__(self, "id", self.client_id)
