"""Client Credentials Provider protocol definition.

This module defines the ClientCredentialsProvider protocol for service-to-service
REST API security. It handles validation of client tokens obtained through OAuth 2.0
Client Credentials flow, rather than performing the initial token acquisition.

This is designed for securing service-to-service API calls where:
- Services have already obtained client access tokens
- The API needs to validate client tokens and extract client identity
- Authorization decisions are made based on client roles and scopes
- Focus is on token validation and client info extraction
"""

from typing import Any, Optional, Protocol, runtime_checkable

from ..models.auth import AuthContext
from ..models.identity import ClientIdentity
from ..models.role import Role
from ..models.token import TokenValidationResult
from ..types.aliases import Token


@runtime_checkable
class ClientCredentialsProvider(Protocol):
    """Protocol for client credentials provider implementations for REST API security.

    This protocol defines the interface for service-to-service API security by
    validating client tokens from already authenticated services. It does NOT handle
    initial client authentication (token acquisition), but focuses on:

    - Client token validation and verification
    - Client identity extraction from tokens
    - Client authorization data (roles,  scopes)
    - Token introspection and metadata
    """

    async def get_client_credentials_token(
        self, scopes: Optional[list[str]] = None
    ) -> dict:
        """Obtain a client credentials token from the identity provider.

        Args:
            scopes: Optional list of scopes to request

        Returns:
            Dict containing access_token, token_type, expires_in, scope, etc.

        Raises:
            ClientCredentialsError: If credentials are invalid
            ProviderError: If request fails
        """
        ...

    async def validate_client_token(self, token: Token) -> TokenValidationResult:
        """Validate a client token and return validation result.

        This is the core method for service-to-service API security. It validates
        client tokens from already authenticated services and returns detailed
        validation results.

        Args:
            token: The client token to validate

        Returns:
            TokenValidationResult containing validation status and token info

        Raises:
            TokenValidationError: If token validation fails
            ProviderError: If there's an error with the provider

        Example:
            ```python
            # In service-to-service API middleware
            result = await provider.validate_client_token(bearer_token)
            if result.is_valid:
                token_info = result.token_info
                print(f"Valid client token for: {token_info.subject}")
            else:
                raise HTTPException(401, "Invalid client token")
            ```
        """
        ...

    async def get_client_info(self, token: Token) -> ClientIdentity:
        """Extract client information from a valid token.

        This method extracts client identity information from an already validated
        client token. Used for identifying the calling service in API operations.

        Args:
            token: A valid client token (should be validated first)

        Returns:
            ClientIdentity instance containing client information extracted from token

        Raises:
            TokenValidationError: If token is invalid or expired
            ClientNotFoundError: If client referenced by token doesn't exist
            ProviderError: If there's an error with the provider
            ```
        """
        ...

    async def get_client_roles(self, token: Token) -> list[Role]:
        """Get roles assigned to the client from a valid token.

        Extracts or retrieves the roles assigned to the client identified by the token.
        Used for service-level authorization decisions.

        Args:
            token: A valid client token identifying the client

        Returns:
            List of Role instances assigned to the client

        Raises:
            TokenValidationError: If token is invalid
            ClientNotFoundError: If client doesn't exist
            ProviderError: If there's an error with the provider

        Example:
            ```python
            roles = await provider.get_client_roles(valid_token)
            role_names = [role.name for role in roles]
            if "service-admin" in role_names:
                # Allow administrative service operations
                pass
            ```
        """
        ...

    async def get_client_scopes(self, token: Token) -> list[str]:
        """Get active scopes for a client from a valid token.

        Extracts the OAuth 2.0 scopes that are active for the client token.
        Used for scope-based authorization in service-to-service communication.

        Args:
            token: A valid client token

        Returns:
            List of scope names active for the client token

        Raises:
            TokenValidationError: If token is invalid
            ProviderError: If there's an error with the provider

        Example:
            ```python
            scopes = await provider.get_client_scopes(valid_token)
            if "read:user-data" not in scopes:
                raise HTTPException(403, "Insufficient scope for operation")
            print(f"Active scopes: {', '.join(scopes)}")
            ```
        """
        ...

    async def get_client_auth_context(self, token: Token) -> AuthContext:
        """Get complete authentication context for a client token -
           PRIMARY METHOD for service API security.

        This is the main method used to secure service-to-service API endpoints.
        It validates the client token and returns complete authentication and
        authorization context including client identity, roles,  and
        scopes. This method combines token validation, client info retrieval,
        and authorization data loading into a single call.

        Args:
            token: The client token from the API request (e.g., from Authorization
            header)

        Returns:
            AuthContext containing:
            - identity: ClientIdentity instance with client information
            - roles: List of client roles for service authorization
            - token_info: Metadata about the client token including scopes

        Raises:
            TokenValidationError: If client token is invalid or expired
            AuthenticationRequiredError: If client authentication is required
            but missing ProviderError: If there's an error with the provider
        """
        ...

    # Optional configuration and health check methods

    async def get_client_provider_config(self) -> dict[str, Any]:
        """Get client credentials provider configuration information.

        Returns:
            Dictionary containing configuration details for service integration

        Example:
            ```python
            config = await provider.get_client_provider_config()
            print(f"Introspection endpoint: {config['introspection_endpoint']}")
            print(f"Supported scopes: {config['supported_scopes']}")
            ```
        """
        ...

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the client credentials provider.

        Returns:
            Dictionary containing health status information

        Example:
            ```python
            health = await provider.health_check()
            if health["status"] == "healthy":
                print("Client credentials provider is healthy")
            ```
        """
        ...
