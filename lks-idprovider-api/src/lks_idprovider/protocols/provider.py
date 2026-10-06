"""Identity Provider protocol definition.

This module defines the IdentityProvider protocol for REST API security.
The protocol focuses on token validation and identity extraction for already
authenticated users, rather than performing initial authentication.

This is designed for securing REST APIs where:
- Users are already authenticated and have tokens
- The service needs to validate tokens and extract user identity
- Authorization decisions are made based on user roles
- No username/password authentication is performed by the service
"""

from typing import Any, Protocol, runtime_checkable

from ..models.auth import AuthContext
from ..models.identity import User
from ..models.role import Role
from ..models.token import TokenValidationResult
from ..types.aliases import Token


@runtime_checkable
class IdentityProvider(Protocol):
    """Protocol for identity provider implementations focused on REST API security.

    This protocol defines the interface for identity providers that secure REST APIs
    by validating tokens from already authenticated users. It does NOT handle initial
    user authentication (login flows), but rather focuses on:

    - Token validation and verification
    - User identity extraction from tokens
    - User authorization data (roles)
    - Token introspection and metadata

    Example:
        ```python
        class KeycloakProvider(IdentityProvider):
            async def validate_token(self, token: Token) -> TokenValidationResult:
                # Validate token with Keycloak and return result
                pass

            async def get_auth_context(self, token: Token) -> AuthContext:
                # Extract complete user context from valid token
                pass
        ```
    """

    async def validate_token(self, token: Token) -> TokenValidationResult:
        """Validate a token and return validation result.

        This is the core method for REST API security. It validates tokens
        from already authenticated users and returns detailed validation results.

        Args:
            token: The token to validate (JWT or opaque token)

        Returns:
            TokenValidationResult containing validation status and token info

        Raises:
            TokenValidationError: If token validation fails
            ProviderError: If there's an error with the provider

        Example:
            ```python
            # In a FastAPI dependency or middleware
            result = await provider.validate_token(bearer_token)
            if result.is_valid:
                token_info = result.token_info
                print(f"Token valid for user: {token_info.subject}")
            else:
                raise HTTPException(401, "Invalid token")
            ```
        """
        ...

    async def get_user_info(self, token: Token) -> User:
        """Extract user information from a valid token.

        This method extracts user identity information from an already
        validated token. It's typically used after token validation to
        get user details for API operations.

        Args:
            token: A valid token (should be validated first)

        Returns:
            User instance containing user information extracted from the token

        Raises:
            TokenValidationError: If token is invalid or expired
            UserNotFoundError: If user referenced by token doesn't exist
            ProviderError: If there's an error with the provider

        Example:
            ```python
            # After validating token in middleware
            user = await provider.get_user_info(valid_token)
            print(f"API request from user: {user.username} ({user.email})")

            # Can be used in FastAPI dependencies
            async def get_current_user(token: str = Depends(oauth2_scheme)):
                return await provider.get_user_info(token)
            ```
        """
        ...

    async def get_user_roles(self, token: Token) -> list[Role]:
        """Get roles assigned to the user from a valid token.

        Extracts or retrieves the roles assigned to the user identified by the token.
        This is used for authorization decisions in the REST API.

        Args:
            token: A valid token identifying the user

        Returns:
            List of Role instances assigned to the user

        Raises:
            TokenValidationError: If token is invalid
            UserNotFoundError: If user doesn't exist
            ProviderError: If there's an error with the provider

        Example:
            ```python
            roles = await provider.get_user_roles(valid_token)
            role_names = [role.name for role in roles]
            if "admin" in role_names:
                # Allow admin operations
                pass
            ```
        """
        ...

    async def get_auth_context(self, token: Token) -> AuthContext:
        """Get complete authentication context from a token -
        PRIMARY METHOD for REST API security.

        This is the main method used to secure REST API endpoints. It
        validates the token and returns complete authentication and
        authorization context including user identity and roles.
        This method combines token validation, user info retrieval,
        and authorization data loading into a single call.

        Args:
            token: The token from the API request (e.g., from Authorization header)

        Returns:
            AuthContext containing:
            - identity: User instance with user information
            - roles: List of user roles for authorization
            - token_info: Metadata about the token itself

        Raises:
            TokenValidationError: If token is invalid or expired
            AuthenticationRequiredError: If authentication is required but missing
            ProviderError: If there's an error with the provider

        Example:
            ```python
            # In FastAPI middleware or dependency
            @app.middleware("http")
            async def auth_middleware(request: Request, call_next):
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    try:
                        context = await provider.get_auth_context(token)
                        request.state.user = context.identity
                        request.state.roles = context.roles
                    except TokenValidationError:
                        return JSONResponse({"error": "Invalid token"}, status_code=401)
                return await call_next(request)

            # In FastAPI dependency
            async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
                context = await provider.get_auth_context(token)
                return context.identity

            # For authorization checks
            async def require_admin(token: str = Depends(oauth2_scheme)):
                context = await provider.get_auth_context(token)
                if not any(role.name == "admin" for role in context.roles):
                    raise HTTPException(403, "Admin access required")
                return context
            ```
        """
        ...

    # Optional configuration and health check methods

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the identity provider.

        Returns:
            Dictionary containing health status information

        Example:
            ```python
            health = await provider.health_check()
            if health["status"] == "healthy":
                print("Provider is healthy")
            ```
        """
        ...

    async def get_provider_info(self) -> dict[str, Any]:
        """Get information about the provider implementation.

        Returns:
            Dictionary containing provider metadata

        Example:
            ```python
            info = await provider.get_provider_info()
            print(f"Provider: {info['name']} v{info['version']}")
            ```
        """
        ...
