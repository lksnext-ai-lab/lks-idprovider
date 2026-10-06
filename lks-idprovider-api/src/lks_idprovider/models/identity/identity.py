"""
Identity models for LKS Identity Provider API.

This module contains the base Identity class and its implementations
(User, ClientIdentity) that form the foundation of the unified identity model.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Identity(BaseModel):
    """
    Base identity representation for both users and clients.

    This is the foundation of the unified identity model that allows
    applications to handle both user and client authentication uniformly.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique identifier for the identity")
    name: str = Field(..., description="Display name for the identity")
    identity_type: str = Field(..., description="Type of identity: 'user' or 'client'")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Additional identity attributes"
    )

    def __str__(self) -> str:
        return f"{self.identity_type.title()}: {self.name} ({self.id})"
