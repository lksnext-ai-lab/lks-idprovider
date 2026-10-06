from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from lks_idprovider.models.auth import AuthContext
from lks_idprovider.protocols import ClientCredentialsProvider, IdentityProvider
from lks_idprovider_fastapi.security import get_bearer_token


# Default provider factory - should be overridden in production
def get_default_provider() -> ClientCredentialsProvider | IdentityProvider:
    """Default provider factory that raises an error.

    This should be overridden in production applications to return
    the actual provider instance.
    """
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "No provider configured. Please override get_default_provider dependency."
        ),
    )


async def get_auth_context(
    token: str = Depends(get_bearer_token),
    provider: ClientCredentialsProvider | IdentityProvider = Depends(
        get_default_provider
    ),
) -> AuthContext:
    """
    Dependency that resolves and returns an AuthContext for the current request.

    Args:
        token (str): The bearer token extracted from the request, provided by the
            get_bearer_token dependency.
        provider (Any): An instance of either IdentityProvider or
            ClientCredentialsProvider, injected as a dependency.

    Returns:
        AuthContext: The authentication context associated with the provided token.

    Raises:
        HTTPException: If authentication fails or the provider is not properly
            initialized.
    """

    try:
        if isinstance(provider, IdentityProvider):
            ctx = await provider.get_auth_context(token)
        elif isinstance(provider, ClientCredentialsProvider):
            ctx = await provider.get_client_auth_context(token)
        return ctx
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e


async def login_required(
    token: str = Depends(get_bearer_token),
    provider: ClientCredentialsProvider | IdentityProvider = Depends(
        get_default_provider
    ),
) -> AuthContext:
    """
    Dependency that validates the token and returns an AuthContext.

    This is a convenience alias for get_auth_context that clearly indicates
    the endpoint requires a valid login/authentication.

    Args:
        token (str): The bearer token extracted from the request.
        provider: An instance of either IdentityProvider or ClientCredentialsProvider.

    Returns:
        AuthContext: The authentication context for the validated token.

    Raises:
        HTTPException: If authentication fails.
    """
    return await get_auth_context(token, provider)


def _check_role_access(
    auth_context: AuthContext, role_names: list[str], client: str | None = None
) -> None:
    """
    Helper function to check if the user has any of the required roles.

    Args:
        auth_context: The authentication context.
        role_names: List of role names to check.
        client: Optional client ID for client-specific roles.

    Raises:
        HTTPException: If the user doesn't have any of the required roles.
    """
    # Check if user has any of the required roles
    user_has_role = any(
        role.name in role_names and role.client == client for role in auth_context.roles
    )

    if not user_has_role:
        # Create a more streamlined and descriptive error message
        if len(role_names) == 1:
            role_desc = f"'{role_names[0]}'"
            message = f"Required role {role_desc}"
        else:
            roles_str = "', '".join(role_names)
            role_desc = f"['{roles_str}']"
            message = f"At least one of roles {role_desc}"

        client_part = f" for client '{client}'" if client else ""
        detail = f"Access denied. {message}{client_part} is required."

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def _create_role_dependency(
    role_names: list[str], client: str | None = None
) -> Callable[[AuthContext], AuthContext]:
    """
    Internal helper to create a role dependency function.
    """

    def role_dependency(
        auth_context: AuthContext = Depends(get_auth_context),
    ) -> AuthContext:
        """
        Internal dependency that validates role access.
        """
        _check_role_access(auth_context, role_names, client)
        return auth_context

    return role_dependency


def requires_role(
    role_name: str, client: str | None = None
) -> Callable[[AuthContext], AuthContext]:
    """
    Dependency factory that creates a role-based access control dependency.

    This function returns a dependency that checks if the authenticated user/client
    has the specified role. It builds on top of get_auth_context.

    Args:
        role_name (str): The name of the required role.
        client (Optional[str]): The client ID for client-specific roles. If None,
                               checks for realm/global roles.

    Returns:
        Callable: A FastAPI dependency function that validates role access.

    Example:
        ```python
        @app.get("/admin")
        async def admin_endpoint(
            auth_context: AuthContext = Depends(requires_role("admin"))
        ):
            return {"message": "Admin access granted"}

        @app.get("/client-specific")
        async def client_endpoint(
            auth_context: AuthContext = Depends(
                requires_role("manager", client="my-app")
            )
        ):
            return {"message": "Client-specific role access granted"}
        ```
    """
    return _create_role_dependency([role_name], client)


def requires_any_role(
    *role_names: str, client: str | None = None
) -> Callable[[AuthContext], AuthContext]:
    """
    Dependency factory that creates a role-based access control dependency
    that accepts any of the specified roles.

    Args:
        *role_names: Variable number of role names. User must have at least one.
        client (Optional[str]): The client ID for client-specific roles.

    Returns:
        Callable: A FastAPI dependency function that validates role access.

    Example:
        ```python
        @app.get("/editor")
        async def editor_endpoint(
            auth_context: AuthContext = Depends(requires_any_role("editor", "admin"))
        ):
            return {"message": "Editor or admin access granted"}
        ```
    """
    return _create_role_dependency(list(role_names), client)
