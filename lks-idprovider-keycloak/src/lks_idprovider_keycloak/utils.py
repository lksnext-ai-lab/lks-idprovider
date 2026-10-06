"""
Utility functions for the Keycloak provider.
"""

from datetime import datetime, timezone
from typing import Any

from lks_idprovider.models.token import TokenInfo
from lks_idprovider.types.enums import TokenType


def map_introspection_to_token_info(
    introspection_data: dict[str, Any], token: str
) -> TokenInfo:
    """Map a Keycloak token introspection response to a TokenInfo model."""
    expires_at = (
        datetime.fromtimestamp(introspection_data["exp"], tz=timezone.utc)
        if "exp" in introspection_data
        else None
    )
    issued_at = (
        datetime.fromtimestamp(introspection_data["iat"], tz=timezone.utc)
        if "iat" in introspection_data
        else None
    )

    scopes = []
    if (
        "realm_access" in introspection_data
        and "roles" in introspection_data["realm_access"]
    ):
        scopes.extend(introspection_data["realm_access"]["roles"])
    if "resource_access" in introspection_data:
        for client_roles in introspection_data["resource_access"].values():
            if "roles" in client_roles:
                scopes.extend(client_roles["roles"])

    return TokenInfo(
        token=token,
        token_type=TokenType.ACCESS_TOKEN,
        expires_at=expires_at,
        issued_at=issued_at,
        issuer=introspection_data.get("iss"),
        audience=introspection_data.get("aud") or introspection_data.get("client_id"),
        subject=introspection_data.get("sub") or introspection_data.get("jti"),
        scopes=scopes,
    )
