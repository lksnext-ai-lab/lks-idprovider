"""
Utility functions for the Azure Entra ID provider.

This module provides helper functions for token validation, claims mapping,
and role extraction specific to Azure Entra ID tokens.
"""

from datetime import UTC, datetime
from typing import Any

import jwt
from lks_idprovider.models.identity import User
from lks_idprovider.models.role import Role
from lks_idprovider.models.token import TokenInfo
from lks_idprovider.types.enums import TokenType


def decode_token_without_validation(token: str) -> dict[str, Any]:
    """Decode a JWT token without validating the signature.

    ⚠️ SECURITY WARNING: This function does NOT validate the token signature.
    It should ONLY be used internally for:
    1. Extracting claims before full signature validation
    2. Determining token type/audience for proper validation setup

    NEVER use this function alone for authentication/authorization decisions.
    Always call validate_token() for security-critical operations.

    Args:
        token: JWT token string

    Returns:
        Dictionary containing the token claims (unverified)

    Raises:
        jwt.DecodeError: If the token is malformed
    """
    # This function intentionally skips signature verification for claim extraction
    # Full validation with signature check happens in validate_token()
    return jwt.decode(
        token,
        options={"verify_signature": False},  # NOSONAR
    )


def map_token_to_token_info(claims: dict[str, Any], token: str) -> TokenInfo:
    """Map Azure AD token claims to a TokenInfo model.

    Azure AD tokens have a specific structure with claims like:
    - sub: Subject (user object ID)
    - oid: Object ID (same as sub for user tokens)
    - tid: Tenant ID
    - aud: Audience (client ID)
    - iss: Issuer
    - exp: Expiration timestamp
    - iat: Issued at timestamp
    - roles: Application roles assigned to the user
    - scp: Scopes (for delegated permissions)

    Args:
        claims: Token claims dictionary
        token: Original token string

    Returns:
        TokenInfo instance with mapped claims
    """
    expires_at = (
        datetime.fromtimestamp(claims["exp"], tz=UTC) if "exp" in claims else None
    )
    issued_at = (
        datetime.fromtimestamp(claims["iat"], tz=UTC) if "iat" in claims else None
    )

    # Extract scopes from both 'scp' (delegated) and 'roles' (application)
    scopes = []

    # Delegated permissions (user tokens)
    if "scp" in claims:
        scopes.extend(
            claims["scp"].split() if isinstance(claims["scp"], str) else claims["scp"]  # pyright: ignore
        )

    # Application roles
    if "roles" in claims:
        roles_claim = claims["roles"]
        if isinstance(roles_claim, list):
            scopes.extend(roles_claim)
        elif isinstance(roles_claim, str):
            scopes.append(roles_claim)

    # Determine token type based on claims
    # Note: TokenType.CLIENT_CREDENTIALS doesn't exist in base API
    # Azure AD tokens are typically access tokens or ID tokens
    token_type = TokenType.ACCESS_TOKEN

    # Check if this is an ID token (has amr, auth_time, etc.)
    if "amr" in claims or "auth_time" in claims:
        token_type = TokenType.ID_TOKEN

    return TokenInfo(
        token=token,
        token_type=token_type,
        expires_at=expires_at,
        issued_at=issued_at,
        issuer=claims.get("iss"),
        audience=claims.get("aud"),
        subject=claims.get("sub") or claims.get("oid"),
        scopes=scopes,
    )


def extract_roles_from_token(claims: dict[str, Any]) -> list[Role]:
    """Extract roles from Azure AD token claims.

    Azure AD includes roles in the 'roles' claim as a list of role names.
    This function converts them to Role objects.

    Args:
        claims: Token claims dictionary

    Returns:
        List of Role instances
    """
    roles = []

    if "roles" in claims:
        roles_claim = claims["roles"]
        if isinstance(roles_claim, list):
            for role_name in roles_claim:
                roles.append(
                    Role(
                        name=role_name,
                        description=f"Azure AD application role: {role_name}",
                    )
                )
        elif isinstance(roles_claim, str):
            roles.append(
                Role(
                    name=roles_claim,
                    description=f"Azure AD application role: {roles_claim}",
                )
            )

    return roles


def map_graph_user_to_user(
    user_data: dict[str, Any], claims: dict[str, Any] | None = None
) -> User:
    """Map Microsoft Graph API user data to a User model.

    Graph API returns user information in a specific format. This function
    maps it to our standardized User model.

    Common Graph API fields:
    - id: User's object ID
    - userPrincipalName: User's UPN (email-like identifier)
    - displayName: User's display name
    - givenName: First name
    - surname: Last name
    - mail: Email address
    - jobTitle: Job title
    - department: Department

    Args:
        user_data: User data from Microsoft Graph API
        claims: Optional token claims for additional context

    Returns:
        User instance with mapped data
    """
    # Get email - prefer 'mail' but fallback to 'userPrincipalName'
    email = user_data.get("mail") or user_data.get("userPrincipalName")

    # Build full name from parts if displayName not available
    display_name = user_data.get("displayName")
    if not display_name:
        given_name = user_data.get("givenName", "")
        surname = user_data.get("surname", "")
        display_name = f"{given_name} {surname}".strip() or None

    # Ensure required fields are not None
    user_id = user_data.get("id") or ""
    username = user_data.get("userPrincipalName") or ""
    name = display_name or ""

    return User(
        id=user_id,
        username=username,
        email=email,
        name=name,
        first_name=user_data.get("givenName"),
        last_name=user_data.get("surname"),
        attributes={
            "job_title": user_data.get("jobTitle"),
            "department": user_data.get("department"),
            "office_location": user_data.get("officeLocation"),
            "mobile_phone": user_data.get("mobilePhone"),
            "business_phones": user_data.get("businessPhones"),
            "tenant_id": claims.get("tid") if claims else None,
        },
    )


def get_identity_type(claims: dict[str, Any]) -> str:
    """Determine the identity type from token claims.

    Azure AD tokens can represent different identity types:
    - user: Regular user identity
    - service_principal: Application/service principal
    - managed_identity: Azure managed identity

    Args:
        claims: Token claims dictionary

    Returns:
        Identity type string: 'user', 'service_principal', or 'managed_identity'
    """
    # Check for identity type claim (newer tokens)
    if "idtyp" in claims:
        if claims["idtyp"] == "app":
            return "service_principal"
        return "user"

    # Legacy detection: client credentials tokens have appid but no oid
    if "appid" in claims and "oid" not in claims:
        return "service_principal"

    # Check for managed identity indicators
    if "xms_mirid" in claims or "xms_az_rid" in claims:
        return "managed_identity"

    # Default to user
    return "user"
