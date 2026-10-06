"""
Role model for LKS Identity Provider API.

This module contains the Role class for representing user and client roles.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Role(BaseModel):
    """Represents a user or client role."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(default=None, description="Role description")
    client: Optional[str] = Field(
        default=None, description="Client ID for client-specific roles"
    )
