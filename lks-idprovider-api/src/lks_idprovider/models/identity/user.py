"""
User model for LKS Identity Provider API.

This module contains the User class for representing authenticated end-users.
"""

from typing import Any, Optional

from pydantic import Field

from .identity import Identity


class User(Identity):
    """
    Represents an authenticated user (end-user).

    Extends Identity with user-specific properties like email, names, etc.
    """

    identity_type: str = Field(
        default="user", description="Always 'user' for User instances"
    )
    username: str = Field(default="", description="Username for login")
    email: Optional[str] = Field(default=None, description="User's email address")
    first_name: Optional[str] = Field(default=None, description="User's first name")
    last_name: Optional[str] = Field(default=None, description="User's last name")
    email_verified: bool = Field(default=False, description="Whether email is verified")
    phone_number: Optional[str] = Field(default=None, description="User's phone number")
    preferred_username: Optional[str] = Field(
        default=None, description="User's preferred username"
    )

    def model_post_init(self, __context: Any) -> None:
        """Set name to username if not provided."""
        if not self.name and self.username:
            object.__setattr__(self, "name", self.username)
        elif not self.name and self.preferred_username:
            object.__setattr__(self, "name", self.preferred_username)

    @property
    def full_name(self) -> str:
        """Return user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.name
